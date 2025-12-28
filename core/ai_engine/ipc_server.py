import logging
import threading
import json
import socket
import os
from pathlib import Path

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
            logger.info(f"Received DBus request: {user_message}")
            result = self.ai_engine.process_request(user_message)
            return json.dumps(result)

class IPCServer:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.socket_path = "/tmp/cosmic-ai.sock"
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
                    data = conn.recv(4096)
                    if not data:
                        continue
                    message = data.decode("utf-8")
                    logger.info(f"Received Socket request: {message}")
                    result = self.ai_engine.process_request(message)
                    conn.sendall(json.dumps(result).encode("utf-8"))
            except Exception as e:
                logger.error(f"Socket error: {e}")

    def stop(self):
        if DBUS_AVAILABLE and hasattr(self, 'loop'):
            self.loop.quit()
        
        self.running = False
        if hasattr(self, 'server'):
            self.server.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)

