import logging
import threading
import json
import socket
import os
import time
from pathlib import Path

from core.ai_engine.config import DEFAULT_SOCKET_PATH

# Try importing dbus, fall back to socket if not available or fails
try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False

logger = logging.getLogger(__name__)

if DBUS_AVAILABLE:
    class CosmicDBusService(dbus.service.Object):
        def __init__(self, ai_engine):
            self.ai_engine = ai_engine
            bus_name = dbus.service.BusName("com.cosmicos.ai", bus=dbus.SessionBus())
            dbus.service.Object.__init__(self, bus_name, "/com/cosmicos/ai")

        @dbus.service.method("com.cosmicos.ai", in_signature='s', out_signature='s')
        def ProcessRequest(self, user_message):
            logger.info(f"Received DBus request: {user_message[:50]}...")
            try:
                # Instant response for system queries
                result = self.ai_engine.process_request(user_message)
                return json.dumps(result)
            except Exception as e:
                logger.error(f"Error processing DBus request: {e}", exc_info=True)
                return json.dumps({"error": f"Processing failed: {str(e)}"})
        
        @dbus.service.method("com.cosmicos.ai", in_signature='s', out_signature='s')
        def ExecutePlan(self, plan_json):
            """Execute an approved plan."""
            logger.info("Received DBus execute plan request")
            try:
                plan = json.loads(plan_json)
                result = self.ai_engine.execute_plan_request(plan)
                return json.dumps(result)
            except Exception as e:
                logger.error(f"Error executing plan: {e}", exc_info=True)
                return json.dumps({"success": False, "error": f"Execution failed: {str(e)}"})

class IPCServer:
    def __init__(self, ai_engine, socket_path=None):
        self.ai_engine = ai_engine
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH
        self.running = False
        self.thread = None

    def start(self):
        # Start DBus if available (preferred for KDE integration)
        if DBUS_AVAILABLE:
            try:
                self._start_dbus()
            except Exception as e:
                logger.error(f"Failed to start DBus server: {e}")
                logger.info("Falling back to Unix socket...")
        
        # Always start socket as fallback (for compatibility)
        # This ensures both DBus and socket work simultaneously
        self._start_socket()

    def _start_dbus(self):
        DBusGMainLoop(set_as_default=True)
        self.dbus_service = CosmicDBusService(self.ai_engine)
        self.loop = GLib.MainLoop()
        self.thread = threading.Thread(target=self.loop.run)
        self.thread.daemon = True
        self.thread.start()
        logger.info("DBus server started on com.cosmicos.ai")

    def _start_socket(self):
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
            
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.socket_path)
        self.server.listen(1)
        self.running = True
        
        self.thread = threading.Thread(target=self._socket_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Socket server started on {self.socket_path}")

    def _socket_loop(self):
        while self.running:
            try:
                conn, _ = self.server.accept()
                with conn:
                    try:
                        # Optimize socket for instant response
                        conn.settimeout(60)  # Longer timeout for complex tasks
                        conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 128KB buffer
                        conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
                        try:
                            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # No delay
                        except:
                            pass  # TCP_NODELAY not available on Unix sockets
                        
                        data = conn.recv(8192)  # Larger initial read for better performance
                        if not data:
                            continue
                        message = data.decode("utf-8")
                        logger.info(f"Received Socket request: {message[:100]}...")  # Log first 100 chars only
                        try:
                            # INSTANT: Check cache first for iOS-quality instant responses
                            if message.startswith("CACHE_CHECK:"):
                                query = message[12:]  # Remove "CACHE_CHECK:" prefix
                                # Check cache in command generator
                                if hasattr(self.ai_engine, 'command_gen') and self.ai_engine.command_gen and self.ai_engine.command_gen.cache:
                                    cache_key = query.strip().lower()
                                    cached = self.ai_engine.command_gen.cache.get(cache_key)
                                    if cached:
                                        logger.debug(f"Cache HIT for: {query[:50]}")
                                        response = json.dumps(cached).encode("utf-8")
                                        conn.sendall(response)
                                        continue
                                    else:
                                        # Cache miss - return empty to proceed normally
                                        response = json.dumps({"cache_miss": True}).encode("utf-8")
                                        conn.sendall(response)
                                        continue
                            
                            # Check if this is an execute plan request (starts with "EXECUTE:")
                            if message.startswith("EXECUTE:"):
                                plan_json = message[8:]  # Remove "EXECUTE:" prefix
                                try:
                                    plan = json.loads(plan_json)
                                except json.JSONDecodeError as e:
                                    logger.error(f"Invalid JSON in execute plan: {e}")
                                    error_response = json.dumps({"success": False, "error": "Invalid plan JSON"}).encode("utf-8")
                                    conn.sendall(error_response)
                                    continue
                                result = self.ai_engine.execute_plan_request(plan)
                            else:
                                # Regular process request
                                result = self.ai_engine.process_request(message)
                            
                            if result is None:
                                result = {"error": "Request processing returned None"}
                            
                            response = json.dumps(result).encode("utf-8")
                            conn.sendall(response)
                        except (KeyboardInterrupt, SystemExit):
                            logger.warning("Request processing interrupted")
                            error_response = json.dumps({"error": "Request interrupted"}).encode("utf-8")
                            try:
                                conn.sendall(error_response)
                            except:
                                pass
                            raise  # Re-raise to exit loop
                        except Exception as e:
                            logger.error(f"Error processing request: {e}", exc_info=True)
                            error_response = json.dumps({"error": f"Processing failed: {str(e)}"}).encode("utf-8")
                            try:
                                conn.sendall(error_response)
                            except Exception as send_error:
                                logger.debug(f"Failed to send error response: {send_error}")
                    except socket.timeout:
                        logger.warning("Socket request timed out")
                        try:
                            conn.sendall(json.dumps({"error": "Request timeout"}).encode("utf-8"))
                        except:
                            pass
                    except (KeyboardInterrupt, SystemExit):
                        # Allow interrupts to propagate
                        raise
                    except Exception as e:
                        logger.error(f"Error handling socket connection: {e}", exc_info=True)
            except (KeyboardInterrupt, SystemExit):
                # Allow interrupts to propagate to main loop
                logger.info("IPC server interrupted, shutting down...")
                break
            except Exception as e:
                logger.error(f"Socket error: {e}", exc_info=True)
                # Continue running - don't crash
                time.sleep(1)  # Brief pause before retrying

    def stop(self):
        if DBUS_AVAILABLE and hasattr(self, 'loop'):
            self.loop.quit()
        
        self.running = False
        if hasattr(self, 'server'):
            self.server.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)

