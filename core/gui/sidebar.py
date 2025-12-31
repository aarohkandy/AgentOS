"""
Cosmic OS AI Sidebar
Main AI assistant interface - slides in from right side (Perplexity Comet style).
Triggered by Ctrl+Space global hotkey.
"""

import sys
import json
import socket
import logging
import subprocess
import shutil
import re
from typing import Optional, List, Dict, Any
from pathlib import Path

# Import constants
try:
    from core.ai_engine.config import DEFAULT_SOCKET_PATH
except ImportError:
    # Fallback if config not available
    DEFAULT_SOCKET_PATH = "/tmp/cosmic-ai.sock"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel,
    QScrollArea, QFrame, QSizePolicy, QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QThread, 
    pyqtSignal, QTimer, QPoint, QRect
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QKeySequence, QShortcut,
    QScreen, QPainter, QBrush, QPen
)

logger = logging.getLogger(__name__)


class WindowResizeManager:
    """
    Manages window resizing when sidebar opens/closes.
    Resizes all visible windows to fit in remaining screen space.
    """
    
    def __init__(self):
        self.xdotool = shutil.which("xdotool")
        self.original_geometries: Dict[int, Dict[str, int]] = {}
        self.sidebar_window_id: Optional[int] = None
        
    def set_sidebar_window_id(self, window_id: int):
        """Set the sidebar's window ID so we can exclude it from resizing."""
        self.sidebar_window_id = window_id
    
    def _run_xdotool(self, *args: str) -> str:
        """Execute xdotool command and return output."""
        if not self.xdotool:
            return ""
        try:
            cmd = [self.xdotool] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"xdotool command failed: {e}")
            return ""
    
    def _run_shell(self, cmd: str) -> str:
        """Execute shell command and return output."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Shell command failed: {e}")
            return ""
    
    def get_all_windows(self) -> List[int]:
        """Get list of all visible window IDs, excluding sidebar and system windows."""
        if not self.xdotool:
            return []
        try:
            output = self._run_xdotool("search", "--onlyvisible", "--name", "")
            if not output:
                return []
            windows = []
            for wid_str in output.strip().split("\n"):
                if wid_str:
                    try:
                        wid = int(wid_str)
                        # Exclude sidebar window
                        if wid == self.sidebar_window_id:
                            continue
                        
                        # Get window name to check for system windows
                        name = self._run_xdotool("getwindowname", str(wid))
                        if not name:
                            continue
                        
                        # Exclude system windows (panels, docks, etc.)
                        name_lower = name.lower()
                        system_keywords = [
                            "panel", "dock", "plasma", "kde", "latte",
                            "desktop", "konsole", "system settings"
                        ]
                        # Only exclude if it's clearly a system window
                        # (be conservative - don't exclude user windows)
                        if any(keyword in name_lower for keyword in ["panel", "dock", "plasma panel"]):
                            continue
                        
                        windows.append(wid)
                    except ValueError:
                        continue
            return windows
        except Exception as e:
            logger.error(f"Failed to get window list: {e}")
            return []
    
    def get_window_geometry(self, window_id: int) -> Optional[Dict[str, int]]:
        """Get window geometry (x, y, width, height)."""
        try:
            geo_output = self._run_xdotool("getwindowgeometry", str(window_id))
            if not geo_output:
                return None
            
            x, y, width, height = 0, 0, 0, 0
            for line in geo_output.split("\n"):
                if "Position:" in line:
                    match = re.search(r"Position:\s*(\d+),(\d+)", line)
                    if match:
                        x, y = int(match.group(1)), int(match.group(2))
                elif "Geometry:" in line:
                    match = re.search(r"Geometry:\s*(\d+)x(\d+)", line)
                    if match:
                        width, height = int(match.group(1)), int(match.group(2))
            
            if width > 0 and height > 0:
                return {"x": x, "y": y, "width": width, "height": height}
            return None
        except Exception as e:
            logger.debug(f"Failed to get geometry for window {window_id}: {e}")
            return None
    
    def is_window_maximized(self, window_id: int) -> bool:
        """Check if window is maximized."""
        try:
            # Try using wmctrl first (more reliable)
            output = self._run_shell(f"wmctrl -lG | grep '^{window_id:08x}'")
            if output:
                # wmctrl format: window_id desktop x y width height
                parts = output.split()
                if len(parts) >= 6:
                    # Check if window spans most of screen (heuristic)
                    width = int(parts[4])
                    # Assume maximized if width > 90% of typical screen
                    return width > 1500
        except Exception:
            pass
        
        # Fallback: check window state via xdotool
        try:
            state = self._run_xdotool("getwindowgeometry", "--shell", str(window_id))
            # This is a heuristic - maximized windows typically have specific geometry
            return False  # Conservative: assume not maximized
        except Exception:
            return False
    
    def unmaximize_window(self, window_id: int) -> bool:
        """Unmaximize a window."""
        try:
            # Try wmctrl first
            self._run_shell(f"wmctrl -i -r {window_id} -b remove,maximized_vert,maximized_horz")
            return True
        except Exception:
            # Fallback: try xdotool key combo
            try:
                self._run_xdotool("windowactivate", str(window_id))
                self._run_xdotool("key", "super+Down")  # Unmaximize in KDE
                return True
            except Exception:
                return False
    
    def resize_window(self, window_id: int, width: int, height: int) -> bool:
        """Resize a window."""
        try:
            self._run_xdotool("windowsize", str(window_id), str(width), str(height))
            return True
        except Exception:
            return False
    
    def move_window(self, window_id: int, x: int, y: int) -> bool:
        """Move a window."""
        try:
            self._run_xdotool("windowmove", str(window_id), str(x), str(y))
            return True
        except Exception:
            return False
    
    def resize_windows_for_sidebar(self, sidebar_width: int, screen_width: int):
        """
        Resize all windows to fit in remaining space when sidebar opens.
        
        Args:
            sidebar_width: Width of the sidebar
            screen_width: Total screen width
        """
        if not self.xdotool:
            logger.warning("xdotool not available, cannot resize windows")
            return
        
        available_width = screen_width - sidebar_width
        windows = self.get_all_windows()
        
        # Store original geometries
        self.original_geometries = {}
        
        for window_id in windows:
            geo = self.get_window_geometry(window_id)
            if not geo:
                continue
            
            # Store original geometry
            self.original_geometries[window_id] = geo.copy()
            
            x = geo["x"]
            y = geo["y"]
            width = geo["width"]
            height = geo["height"]
            right_edge = x + width
            
            # Skip windows that are already within bounds
            if right_edge <= available_width:
                continue
            
            # Check if maximized - unmaximize first
            if self.is_window_maximized(window_id):
                self.unmaximize_window(window_id)
                # Re-get geometry after unmaximizing
                geo = self.get_window_geometry(window_id)
                if geo:
                    x = geo["x"]
                    y = geo["y"]
                    width = geo["width"]
                    height = geo["height"]
                    right_edge = x + width
                    # Update stored geometry
                    self.original_geometries[window_id] = geo.copy()
            
            # Calculate new width
            if x >= available_width:
                # Window is completely on the right side - move it left
                new_x = max(0, available_width - width)
                if new_x < 0:
                    # Window is wider than available space - resize it
                    new_width = available_width
                    new_x = 0
                else:
                    new_width = width
                self.move_window(window_id, new_x, y)
                if new_width != width:
                    self.resize_window(window_id, new_width, height)
            elif right_edge > available_width:
                # Window extends beyond - resize it
                new_width = available_width - x
                if new_width > 0:
                    self.resize_window(window_id, new_width, height)
        
        logger.info(f"Resized {len(self.original_geometries)} windows for sidebar")
    
    def restore_windows(self):
        """Restore all windows to their original geometries."""
        if not self.original_geometries:
            return
        
        for window_id, geo in self.original_geometries.items():
            try:
                # Restore size first
                self.resize_window(window_id, geo["width"], geo["height"])
                # Then restore position
                self.move_window(window_id, geo["x"], geo["y"])
            except Exception as e:
                logger.debug(f"Failed to restore window {window_id}: {e}")
        
        logger.info(f"Restored {len(self.original_geometries)} windows")
        self.original_geometries = {}
    
    def set_strut(self, width: int, height: int):
        """
        Set _NET_WM_STRUT and _NET_WM_STRUT_PARTIAL properties to reserve screen space for sidebar.
        This tells the window manager to reserve space on the right side.
        Format: left, right, top, bottom (in pixels from edges)
        For right-side sidebar: left=0, right=width, top=0, bottom=0
        """
        if not self.sidebar_window_id:
            # Window ID not set yet, skip
            logger.debug("Cannot set strut: sidebar window ID not set")
            return
        
        try:
            # Get screen dimensions for strut partial
            screen_width = int(self._run_shell("xdotool getdisplaygeometry | cut -d' ' -f1") or "1920")
            screen_height = int(self._run_shell("xdotool getdisplaygeometry | cut -d' ' -f2") or "1080")
            
            # _NET_WM_STRUT: left, right, top, bottom (from edges)
            # For right-side sidebar: reserve space on the right
            strut_value = f"0,{width},0,0"  # left, right, top, bottom
            
            # _NET_WM_STRUT_PARTIAL: left_start, left_end, right_start, right_end, top_start, top_end, bottom_start, bottom_end
            # For right-side sidebar: right_start=0, right_end=height
            strut_partial_value = f"0,0,0,{height},0,0,0,0"
            
            # Set _NET_WM_STRUT (32-bit cardinal array)
            cmd1 = f"xprop -id {self.sidebar_window_id} -f _NET_WM_STRUT 32c -set _NET_WM_STRUT {strut_value}"
            self._run_shell(cmd1)
            
            # Set _NET_WM_STRUT_PARTIAL (32-bit cardinal array) for better compatibility
            cmd2 = f"xprop -id {self.sidebar_window_id} -f _NET_WM_STRUT_PARTIAL 32c -set _NET_WM_STRUT_PARTIAL {strut_partial_value}"
            self._run_shell(cmd2)
            
            logger.info(f"Set _NET_WM_STRUT to {strut_value} and _NET_WM_STRUT_PARTIAL to {strut_partial_value} for sidebar")
        except Exception as e:
            # Non-critical - window resizing will still work
            logger.warning(f"Could not set _NET_WM_STRUT: {e}")
    
    def clear_strut(self):
        """Clear the _NET_WM_STRUT and _NET_WM_STRUT_PARTIAL properties."""
        if not self.sidebar_window_id:
            return
        
        try:
            cmd1 = f"xprop -id {self.sidebar_window_id} -remove _NET_WM_STRUT"
            self._run_shell(cmd1)
            cmd2 = f"xprop -id {self.sidebar_window_id} -remove _NET_WM_STRUT_PARTIAL"
            self._run_shell(cmd2)
            logger.info("Cleared _NET_WM_STRUT and _NET_WM_STRUT_PARTIAL for sidebar")
        except Exception as e:
            logger.debug(f"Could not clear _NET_WM_STRUT: {e}")


class AIWorker(QThread):
    """Worker thread for AI communication."""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, socket_path: str = None):
        super().__init__()
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH
        self.message = ""

    def set_message(self, message: str):
        self.message = message

    def run(self):
        # Try DBus first (preferred for KDE integration)
        try:
            import dbus
            bus = dbus.SessionBus()
            obj = bus.get_object("com.cosmicos.ai", "/com/cosmicos/ai")
            iface = dbus.Interface(obj, "com.cosmicos.ai")
            response_str = iface.ProcessRequest(self.message)
            result = json.loads(response_str)
            self.result_ready.emit(result)
            return
        except (ImportError, dbus.exceptions.DBusException, AttributeError) as e:
            # DBus not available or service not found, try socket
            logger.debug(f"DBus connection failed: {e}, trying socket...")
        
        # Fallback to Unix socket
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(120)  # Longer timeout for AI processing (model inference can take time)
            sock.connect(self.socket_path)
            
            # Send message with newline delimiter for proper protocol
            message_bytes = self.message.encode('utf-8')
            sock.sendall(message_bytes)
            sock.shutdown(socket.SHUT_WR)  # Signal that we're done sending
            
            # Read response - server will close connection when done
            response = b""
            while True:
                try:
                    chunk = sock.recv(8192)  # Larger buffer for JSON responses
                    if not chunk:
                        break  # Server closed connection
                    response += chunk
                except socket.timeout:
                    logger.warning("Socket read timeout - response may be incomplete")
                    break
                except Exception as e:
                    logger.error(f"Error reading socket response: {e}")
                    break
            
            sock.close()
            
            if not response:
                raise ValueError("Empty response from AI daemon")
            
            # Parse JSON response
            try:
                result = json.loads(response.decode('utf-8'))
                self.result_ready.emit(result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response was: {response.decode('utf-8', errors='ignore')[:500]}")
                self.error_occurred.emit(f"Invalid response from AI daemon: {str(e)}")
        except FileNotFoundError:
            self.error_occurred.emit("AI daemon not running. Start with: ./scripts/start-cosmic-test.sh")
        except ConnectionRefusedError:
            self.error_occurred.emit("AI daemon not responding. Check if it's running.")
        except socket.timeout:
            self.error_occurred.emit("AI daemon timeout - request took too long. The model may be processing.")
        except ValueError as e:
            self.error_occurred.emit(f"Communication error: {str(e)}")
        except json.JSONDecodeError as e:
            self.error_occurred.emit(f"Invalid response format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in AIWorker: {e}", exc_info=True)
            self.error_occurred.emit(f"Error: {str(e)}")


class MessageBubble(QFrame):
    """Chat message bubble widget."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setup_ui(text)

    def setup_ui(self, text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        label.setOpenExternalLinks(True)
        label.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML rendering
        
        # iOS-quality typography - SF Pro Text for perfect readability
        font = QFont("SF Pro Text", 15)
        if font.family() != "SF Pro Text":
            font = QFont("Arial", 15)  # Fallback font
        label.setFont(font)
        
        # Ensure label has proper minimum size
        label.setMinimumHeight(20)
        
        if self.is_user:
            # User message - Perfect iOS blue (#007AFF) with premium styling
            self.setStyleSheet("""
                QFrame {
                    background-color: #007AFF;
                    border-radius: 20px;
                    border: none;
                }
                QLabel {
                    color: #FFFFFF;
                    font-weight: 400;
                    font-size: 15px;
                    line-height: 1.5;
                    background: transparent;
                    padding: 2px;
                }
            """)
            # Set margins for user messages (left margin pushes to right)
            self.setContentsMargins(60, 4, 16, 4)
        else:
            # AI message - Perfect iOS gray with subtle border and shadow
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(44, 44, 46, 0.95);
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                }
                QLabel {
                    color: #FFFFFF;
                    font-size: 15px;
                    line-height: 1.5;
                    background: transparent;
                    padding: 2px;
                }
            """)
            # Set margins for AI messages (right margin pushes to left)
            self.setContentsMargins(16, 4, 60, 4)
        
        # Set minimum size to ensure visibility
        self.setMinimumHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        layout.addWidget(label)
        
        # Ensure widget is visible
        self.setVisible(True)
        self.show()


class CommandPlanWidget(QFrame):
    """Widget to display command plan with approve/deny buttons."""
    
    approved = pyqtSignal(dict)
    denied = pyqtSignal()

    def __init__(self, plan: dict, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            CommandPlanWidget {
                background-color: #1E1E1E;
                border: 1px solid #3D3D3D;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QLabel("📋 Command Plan")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(header)

        # Description
        desc = self.plan.get("description", "No description")
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #A0A0A0;")
        layout.addWidget(desc_label)

        # Actions list
        actions = self.plan.get("plan", [])
        if actions:
            actions_frame = QFrame()
            actions_frame.setStyleSheet("""
                QFrame {
                    background-color: #252525;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            actions_layout = QVBoxLayout(actions_frame)
            
            for i, action in enumerate(actions[:5]):  # Show max 5 actions
                action_text = self._format_action(action)
                action_label = QLabel(f"{i+1}. {action_text}")
                action_label.setStyleSheet("color: #C0C0C0; font-family: monospace;")
                actions_layout.addWidget(action_label)
            
            if len(actions) > 5:
                more_label = QLabel(f"... and {len(actions) - 5} more actions")
                more_label.setStyleSheet("color: #808080; font-style: italic;")
                actions_layout.addWidget(more_label)
            
            layout.addWidget(actions_frame)

        # Estimated time
        est_time = self.plan.get("estimated_time", 0)
        if est_time:
            time_label = QLabel(f"⏱️ Estimated time: {est_time}s")
            time_label.setStyleSheet("color: #808080;")
            layout.addWidget(time_label)

        # Buttons
        btn_layout = QHBoxLayout()
        
        deny_btn = QPushButton("✕ Deny")
        deny_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        deny_btn.clicked.connect(self._on_deny)
        
        approve_btn = QPushButton("✓ Approve")
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #388E3C;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        approve_btn.clicked.connect(self._on_approve)
        
        btn_layout.addWidget(deny_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(approve_btn)
        
        layout.addLayout(btn_layout)

    def _format_action(self, action: dict) -> str:
        act_type = action.get("action", "unknown")
        if act_type == "click":
            loc = action.get("location", [0, 0])
            target = action.get("target", "")
            return f"click {target} @ ({loc[0]}, {loc[1]})"
        elif act_type == "type":
            text = action.get("text", "")[:30]
            return f'type "{text}"'
        elif act_type == "key":
            return f"press {action.get('key', '')}"
        elif act_type == "wait":
            return f"wait {action.get('seconds', 0)}s"
        elif act_type == "drag":
            return "drag operation"
        return str(action)

    def _on_approve(self):
        self.approved.emit(self.plan)
        self.deleteLater()

    def _on_deny(self):
        self.denied.emit()
        self.deleteLater()


class CosmicSidebar(QWidget):
    """
    Main AI Sidebar widget.
    Slides in from the right side of the screen.
    """

    def __init__(self):
        super().__init__()
        self.is_visible = False
        self.messages: List[Dict[str, Any]] = []
        self.current_plan: Optional[dict] = None
        self.ai_worker = AIWorker()
        self.window_resize_manager = WindowResizeManager()
        
        self.setup_ui()
        self.setup_animations()
        self.setup_connections()
        self.setup_global_hotkey()

    def setup_ui(self):
        # Window flags for overlay sidebar
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        
        self.sidebar_width = 420
        self.setFixedWidth(self.sidebar_width)
        self.setFixedHeight(screen_geo.height())
        
        # Position off-screen initially (right side)
        self.hidden_pos = QPoint(screen_geo.width(), 0)
        self.shown_pos = QPoint(screen_geo.width() - self.sidebar_width, 0)
        self.move(self.hidden_pos)
        
        # Main container with background
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.sidebar_width, screen_geo.height())
        # iOS-quality background
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(28, 28, 30, 0.95);
                border-left: 0.5px solid rgba(60, 60, 67, 0.36);
            }
        """)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area (scrollable)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border: none;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(8)  # iOS-quality spacing
        self.chat_layout.setContentsMargins(20, 20, 20, 20)  # More padding
        
        self.chat_scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.chat_scroll, 1)

        # Input area
        input_area = self._create_input_area()
        main_layout.addWidget(input_area)

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: rgba(28, 28, 30, 0.95);
                border-bottom: 0.5px solid rgba(60, 60, 67, 0.36);
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Title - iOS-quality typography
        title = QLabel("Cosmic AI")
        title_font = QFont("SF Pro Display", 17, QFont.Weight.DemiBold)
        if title_font.family() != "SF Pro Display":
            title_font = QFont("Inter", 17, QFont.Weight.DemiBold)
        if title_font.family() != "Inter":
            title_font = QFont("Segoe UI", 17, QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF; letter-spacing: -0.3px;")
        layout.addWidget(title)
        
        layout.addStretch()

        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #A0A0A0;
            }
            QPushButton:hover {
                color: #E0E0E0;
            }
        """)
        layout.addWidget(settings_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: #A0A0A0;
            }
            QPushButton:hover {
                color: #FF5252;
            }
        """)
        close_btn.clicked.connect(self.hide_sidebar)
        layout.addWidget(close_btn)

        return header

    def _create_input_area(self) -> QFrame:
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(28, 28, 30, 0.95);
                border-top: 0.5px solid rgba(60, 60, 67, 0.36);
            }
        """)
        input_frame.setFixedHeight(80)  # iOS-standard height
        
        layout = QHBoxLayout(input_frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Cosmic AI...")
        # iOS-quality typography for input
        input_font = QFont("SF Pro Text", 15)
        if input_font.family() != "SF Pro Text":
            input_font = QFont("Inter", 15)
        if input_font.family() != "Inter":
            input_font = QFont("Segoe UI", 15)
        self.input_field.setFont(input_font)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(44, 44, 46, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 14px 20px;
                color: #F2F2F7;
                font-size: 15px;
                selection-background-color: #007AFF;
            }
            QLineEdit:focus {
                border-color: #007AFF;
                background-color: rgba(50, 50, 52, 0.95);
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        layout.addWidget(self.input_field, 1)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(36, 36)  # Perfect circle for iOS
        # iOS-quality send button
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 18px;
                font-size: 16px;
                color: #FFFFFF;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:pressed {
                background-color: #0040B3;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(send_btn)

        return input_frame

    def setup_animations(self):
        """Setup smooth iOS-quality animations - buttery smooth 60fps."""
        # Slide animation - perfect iOS timing (250ms is iOS standard)
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(250)  # Perfect iOS timing
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)  # iOS standard easing
        # Note: PyQt6 animations run at 60fps by default, no need for setUpdateInterval
        
        # Opacity animation for fade effect (iOS-style)
        try:
            self.opacity_effect = QGraphicsOpacityEffect(self.container)
            self.container.setGraphicsEffect(self.opacity_effect)
            self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.opacity_anim.setDuration(250)
            self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        except Exception as e:
            logger.debug(f"Could not setup opacity animation: {e}")
            self.opacity_effect = None
            self.opacity_anim = None

    def setup_connections(self):
        self.ai_worker.result_ready.connect(self.handle_ai_response)
        self.ai_worker.error_occurred.connect(self.handle_ai_error)

    def setup_global_hotkey(self):
        """Register global hotkey to toggle sidebar."""
        try:
            from core.gui.hotkey_handler import GlobalHotkeyHandler
            from core.ai_engine.config import Config
            
            config = Config()
            hotkey = config.get("GUI", "hotkey", fallback="Super+Shift")
            
            self.hotkey_handler = GlobalHotkeyHandler(
                callback=self.toggle_sidebar,
                hotkey=hotkey
            )
            self.hotkey_handler.register()
        except Exception as e:
            logger.debug(f"Could not register global hotkey: {e}")
    
    def _set_sidebar_window_id(self):
        """Set the sidebar window ID for exclusion from resize operations."""
        try:
            # Get X11 window ID using xdotool search
            # Search for window with our title or class
            xdotool = shutil.which("xdotool")
            if not xdotool:
                return
            
            # Try searching by window title (may contain "Cosmic" or similar)
            result = subprocess.run(
                [xdotool, "search", "--onlyvisible", "--name", "Cosmic"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                # Get the most recent window (likely ours)
                window_ids = [int(wid) for wid in result.stdout.strip().split("\n") if wid]
                if window_ids:
                    # Use the last one (most recently created)
                    self.window_resize_manager.set_sidebar_window_id(window_ids[-1])
                    logger.debug(f"Set sidebar window ID: {window_ids[-1]}")
                    return
            
            # Fallback: search by PID (our process)
            import os
            pid = os.getpid()
            result = subprocess.run(
                [xdotool, "search", "--pid", str(pid)],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                window_ids = [int(wid) for wid in result.stdout.strip().split("\n") if wid]
                if window_ids:
                    # Use the window that matches our geometry
                    screen = QApplication.primaryScreen()
                    screen_geo = screen.availableGeometry()
                    for wid in window_ids:
                        # Check if this window matches our position/size
                        geo_result = subprocess.run(
                            [xdotool, "getwindowgeometry", str(wid)],
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        if geo_result.returncode == 0:
                            # Check if width matches sidebar width
                            if f"{self.sidebar_width}x" in geo_result.stdout:
                                self.window_resize_manager.set_sidebar_window_id(wid)
                                logger.debug(f"Set sidebar window ID via geometry: {wid}")
                                return
        except Exception as e:
            logger.debug(f"Could not set sidebar window ID: {e}")

    def toggle_sidebar(self):
        if self.is_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def show_sidebar(self):
        """Show sidebar with smooth iOS-quality animation."""
        if self.is_visible:
            return
        
        self.show()
        
        # Get screen dimensions
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        screen_height = screen_geo.height()
        screen_width = screen_geo.width()
        
        # Update sidebar window ID now that window is shown
        # Then set strut and resize windows AFTER window ID is set
        def setup_screen_resize():
            # Set strut to reserve screen space (requires window ID)
            self.window_resize_manager.set_strut(
                self.sidebar_width,
                screen_height
            )
            # Resize windows to make room for sidebar
            self.window_resize_manager.resize_windows_for_sidebar(
                self.sidebar_width,
                screen_width
            )
        
        # Set window ID first, then setup screen resize
        QTimer.singleShot(50, self._set_sidebar_window_id)
        QTimer.singleShot(150, setup_screen_resize)  # After window ID is set
        
        # Start position animation
        self.slide_anim.setStartValue(self.hidden_pos)
        self.slide_anim.setEndValue(self.shown_pos)
        
        # Start opacity animation (fade in) if available
        if hasattr(self, 'opacity_effect') and self.opacity_effect and hasattr(self, 'opacity_anim') and self.opacity_anim:
            self.opacity_effect.setOpacity(0.0)
            self.opacity_anim.setStartValue(0.0)
            self.opacity_anim.setEndValue(1.0)
            self.opacity_anim.start()
        
        # Start slide animation
        self.slide_anim.start()
        
        self.is_visible = True
        
        # Focus input after animation completes
        QTimer.singleShot(300, self.input_field.setFocus)

    def hide_sidebar(self):
        """Hide sidebar with smooth iOS-quality animation."""
        if not self.is_visible:
            return
        
        self.is_visible = False
        
        # Start position animation
        self.slide_anim.setStartValue(self.shown_pos)
        self.slide_anim.setEndValue(self.hidden_pos)
        
        # Start opacity animation (fade out) if available
        if hasattr(self, 'opacity_effect') and self.opacity_effect and hasattr(self, 'opacity_anim') and self.opacity_anim:
            self.opacity_anim.setStartValue(1.0)
            self.opacity_anim.setEndValue(0.0)
            self.opacity_anim.start()
        
        # Start slide animation
        self.slide_anim.start()
        self.slide_anim.finished.connect(self._on_hide_complete)

    def _on_hide_complete(self):
        """Complete the hide process - ensure window is fully off-screen and invisible."""
        # Disconnect animation finished signal first
        self.slide_anim.finished.disconnect(self._on_hide_complete)
        
        # Move window completely off-screen (ensure it's at hidden position with extra margin)
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        # Move completely off-screen to the right with extra margin
        off_screen_pos = QPoint(screen_geo.width() + 100, 0)
        self.move(off_screen_pos)
        
        # Clear strut to release screen space (must happen before hide)
        self.window_resize_manager.clear_strut()
        
        # Restore windows to original positions
        self.window_resize_manager.restore_windows()
        
        # Hide the window completely and lower it
        self.hide()
        self.lower()  # Ensure it's behind other windows

    def send_message(self):
        """Send message to AI - iOS-quality instant responses with caching."""
        try:
            text = self.input_field.text().strip()
            if not text:
                return
            
            self.input_field.clear()
            self.add_message(text, is_user=True)
            
            # INSTANT: Check cache first for instant responses (iOS-quality)
            # This happens synchronously for instant feedback
            cached_response = self._check_cache_instant(text)
            if cached_response and not cached_response.get("cache_miss"):
                # Instant response from cache - show immediately (no loading indicator)
                QTimer.singleShot(10, lambda: self.handle_ai_response(cached_response))
                return
            
            # Show loading indicator (only if not cached)
            self.add_loading()
            
            # Send to AI with error handling
            try:
                self.ai_worker.set_message(text)
                self.ai_worker.start()
            except Exception as e:
                logger.error(f"Error starting AI worker: {e}", exc_info=True)
                self.remove_loading()
                self.add_message(f"❌ Error: Failed to send message. {str(e)}", is_user=False)
        except Exception as e:
            logger.error(f"Critical error in send_message: {e}", exc_info=True)
            self.remove_loading()
            self.add_message("❌ An unexpected error occurred. Please try again.", is_user=False)
    
    def _check_cache_instant(self, message: str) -> Optional[dict]:
        """Check cache for instant response - iOS-quality instant feedback."""
        try:
            # Try to get cached response from AI daemon
            # This is a synchronous check for instant responses
            socket_path = DEFAULT_SOCKET_PATH
            if not Path(socket_path).exists():
                return None
            
            # Quick cache check request
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.15)  # Very short timeout for instant check
            try:
                sock.connect(socket_path)
                # Send cache check request (special format)
                cache_request = f"CACHE_CHECK:{message}"
                sock.sendall(cache_request.encode('utf-8'))
                
                # Try to get response (non-blocking)
                sock.settimeout(0.1)  # Very short for instant
                response = sock.recv(8192)  # Larger buffer for better performance
                sock.close()
                
                if response:
                    result = json.loads(response.decode('utf-8'))
                    if result and not result.get("cache_miss") and not result.get("error"):
                        logger.debug(f"Cache HIT: {message[:50]}")
                        return result
            except (socket.timeout, ConnectionRefusedError, json.JSONDecodeError, OSError):
                # Cache miss or timeout - proceed normally
                pass
            finally:
                try:
                    sock.close()
                except:
                    pass
        except Exception:
            # Cache check failed - proceed normally
            pass
        
        return None

    def add_message(self, text: str, is_user: bool = True):
        # Remove empty state on first message
        if hasattr(self, 'empty_state') and self.empty_state:
            self._remove_empty_state()
        
        # Skip empty messages
        if not text or not text.strip():
            logger.debug("Skipping empty message")
            return
        
        logger.debug(f"Adding message: {text[:50]}... (user={is_user})")
        
        bubble = MessageBubble(text, is_user=is_user)
        
        # Ensure bubble is visible
        bubble.show()
        bubble.setVisible(True)
        
        # Add message bubble directly
        self.chat_layout.addWidget(bubble)
        self.messages.append({"text": text, "is_user": is_user})
        
        # Force update
        bubble.update()
        self.chat_widget.update()
        self.chat_scroll.update()
        
        # Smooth scroll to bottom
        QTimer.singleShot(5, self._scroll_to_bottom)

    def add_loading(self):
        """Add beautiful iOS-style loading indicator with buttery smooth animation."""
        loading_frame = QFrame()
        loading_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(42, 42, 46, 0.9);
                border-radius: 14px;
                border: 1px solid rgba(60, 60, 65, 0.5);
                margin-right: 40px;
                padding: 4px;
            }
        """)
        
        loading_layout = QHBoxLayout(loading_frame)
        loading_layout.setContentsMargins(20, 16, 20, 16)
        loading_layout.setSpacing(8)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Beautiful animated dots with perfect timing
        self.loading_dots = []
        self.loading_anims = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("""
                QLabel {
                    color: #007AFF;
                    font-size: 12px;
                    font-weight: 600;
                }
            """)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setFixedSize(12, 12)
            loading_layout.addWidget(dot)
            self.loading_dots.append(dot)
            
            # Perfect iOS-style dot animation - smooth pulse
            dot_opacity = QGraphicsOpacityEffect(dot)
            dot.setGraphicsEffect(dot_opacity)
            dot_anim = QPropertyAnimation(dot_opacity, b"opacity")
            dot_anim.setDuration(600)  # Faster for instant feel
            dot_anim.setStartValue(0.2)
            dot_anim.setKeyValueAt(0.5, 1.0)
            dot_anim.setEndValue(0.2)
            dot_anim.setLoopCount(-1)  # Infinite smooth loop
            # Perfect stagger for wave effect
            QTimer.singleShot(i * 160, lambda anim=dot_anim: anim.start())
            self.loading_anims.append(dot_anim)
        
        # Add "Thinking..." text
        thinking_label = QLabel("Thinking...")
        thinking_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
                font-weight: 500;
            }
        """)
        loading_layout.addWidget(thinking_label)
        
        self.loading_label = loading_frame
        self.chat_layout.addWidget(loading_frame)
        
        # Instant fade-in with perfect easing
        loading_opacity = QGraphicsOpacityEffect(loading_frame)
        loading_frame.setGraphicsEffect(loading_opacity)
        loading_opacity.setOpacity(0.0)
        loading_anim = QPropertyAnimation(loading_opacity, b"opacity")
        loading_anim.setDuration(120)  # Instant iOS feel
        loading_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        loading_anim.setStartValue(0.0)
        loading_anim.setEndValue(1.0)
        loading_anim.start()
        
        # Smooth scroll - instant
        QTimer.singleShot(5, self._scroll_to_bottom)  # Instant scroll

    def remove_loading(self):
        """Remove loading indicator with smooth fade-out."""
        if hasattr(self, 'loading_label') and self.loading_label:
            # Stop animations first
            if hasattr(self, 'loading_anims'):
                for anim in self.loading_anims:
                    anim.stop()
                del self.loading_anims
            # Smooth fade-out before removal
            loading_opacity = self.loading_label.graphicsEffect()
            if loading_opacity:
                fade_out = QPropertyAnimation(loading_opacity, b"opacity")
                fade_out.setDuration(100)  # Instant fade-out
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.finished.connect(lambda: self._actually_remove_loading())
                fade_out.start()
            else:
                self._actually_remove_loading()
        else:
            self._actually_remove_loading()
    
    def _actually_remove_loading(self):
        """Actually remove loading indicator after fade-out."""
        if hasattr(self, 'loading_dots'):
            del self.loading_dots
        if hasattr(self, 'loading_label') and self.loading_label:
            self.loading_label.deleteLater()
            self.loading_label = None

    def _scroll_to_bottom(self):
        """Smooth scroll to bottom - iOS-quality buttery smooth (60fps)."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # Perfect iOS-style smooth animated scroll - instant but smooth
        scroll_anim = QPropertyAnimation(scrollbar, b"value")
        scroll_anim.setDuration(120)  # Faster for instant iOS feel
        scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)  # Perfect iOS easing
        scroll_anim.setStartValue(scrollbar.value())
        scroll_anim.setEndValue(max_value)
        scroll_anim.start()

    def handle_ai_response(self, result: dict):
        """Handle AI response with comprehensive error handling - never crashes."""
        try:
            self.remove_loading()
            
            if not result or not isinstance(result, dict):
                logger.warning(f"Invalid AI response: {result}")
                self.add_message("❌ Invalid response from AI. Please try again.", is_user=False)
                return
            
            if "error" in result:
                self.add_message(f"❌ Error: {result['error']}", is_user=False)
                return
            
            # Check if it's a command plan
            if "plan" in result and isinstance(result["plan"], list):
                # Show plan for approval
                desc = result.get("description", "Generated command plan")
                
                # Show fallback mode indicator only for command plans (not for every message)
                if result.get("fallback_mode") and result["plan"]:
                    # Only show once per session, or make it less intrusive
                    if not hasattr(self, '_fallback_warning_shown'):
                        self.add_message("ℹ️ Using rule-based fallback mode. Install models for full AI: ./scripts/install-models.sh", is_user=False)
                        self._fallback_warning_shown = True
                
                self.add_message(f"📋 {desc}", is_user=False)
                
                # Only show plan widget if there are actual actions
                if result["plan"]:
                    plan_widget = CommandPlanWidget(result)
                    plan_widget.approved.connect(self.execute_approved_plan)
                    plan_widget.denied.connect(self.handle_plan_denied)
                    self.chat_layout.addWidget(plan_widget)
                    self.current_plan = result
                else:
                    # Empty plan - just show description
                    pass
            else:
                # Regular text response (conversational messages, help text, etc.)
                text = result.get("description", str(result))
                # Clean up text - remove JSON artifacts and format
                text = self._format_response_text(text)
                self.add_message(text, is_user=False)
            
            QTimer.singleShot(5, self._scroll_to_bottom)  # Instant scroll
        except Exception as e:
            logger.error(f"Error handling AI response: {e}", exc_info=True)
            self.remove_loading()
            self.add_message("❌ Error processing AI response. Please try again.", is_user=False)

    def handle_ai_error(self, error: str):
        """Handle AI error with comprehensive error handling - never crashes."""
        try:
            self.remove_loading()
            error_msg = str(error) if error else "Unknown error"
            self.add_message(f"❌ Connection error: {error_msg}", is_user=False)
        except Exception as e:
            logger.error(f"Error in handle_ai_error: {e}", exc_info=True)
            # Last resort - just log it

    def execute_approved_plan(self, plan: dict):
        self.add_message("✅ Plan approved. Executing...", is_user=False)
        
        # Send execution request
        exec_request = json.dumps({"action": "execute", "plan": plan})
        self.ai_worker.set_message(exec_request)
        self.ai_worker.start()
        
        self.current_plan = None

    def handle_plan_denied(self):
        self.add_message("❌ Plan denied.", is_user=False)
        self.current_plan = None

    def _format_response_text(self, text: str) -> str:
        """
        Format response text with HTML and clean up JSON artifacts.
        Converts markdown-style formatting to HTML.
        """
        if not text:
            return ""
        
        # Remove JSON artifacts (like "{}\nDescription: ...")
        if text.startswith("{"):
            # Try to extract just the description part
            if "Description:" in text:
                text = text.split("Description:")[-1].strip()
            elif "description:" in text:
                text = text.split("description:")[-1].strip()
        
        # Remove leading/trailing braces and quotes
        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            text = text[1:-1].strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
        
        # Convert markdown-style to HTML
        import re
        
        # Bold: **text** -> <b>text</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        
        # Italic: *text* -> <i>text</i> (but not if it's part of **)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        
        # Links: [text](url) -> <a href="url">text</a>
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #0078D4;">\1</a>', text)
        
        # Code: `code` -> <code style="background-color: #3D3D3D; padding: 2px 4px; border-radius: 3px;">code</code>
        text = re.sub(r'`([^`]+)`', r'<code style="background-color: #3D3D3D; padding: 2px 4px; border-radius: 3px; font-family: monospace;">\1</code>', text)
        
        # Convert newlines to <br>
        text = text.replace('\n', '<br>')
        
        return text

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_sidebar()
        super().keyPressEvent(event)


def main():
    """Run the sidebar as standalone for testing."""
    # Check if another instance is already running (atomic lock)
    import os
    import fcntl
    lock_file = "/tmp/cosmic-sidebar.lock"
    lock_fd = None
    
    try:
        # Try to open/create lock file
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        
        # Try to acquire exclusive lock (non-blocking)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # Lock is held by another process
            os.close(lock_fd)
            # Read the PID from the lock file
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                    print(f"Another sidebar instance is already running (PID: {old_pid})")
                    print("Use 'anos --stop' to stop it first")
                    sys.exit(1)
                except ProcessLookupError:
                    # Process doesn't exist, stale lock - will be removed below
                    pass
            except (ValueError, IOError):
                pass
            
            # Try one more time to acquire lock (in case stale lock was removed)
            lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                os.close(lock_fd)
                print("Another sidebar instance is already running")
                print("Use 'anos --stop' to stop it first")
                sys.exit(1)
        
        # Write PID to lock file
        os.write(lock_fd, str(os.getpid()).encode())
        os.fsync(lock_fd)  # Ensure it's written to disk
    
    except Exception as e:
        # If lock acquisition fails for any reason, exit
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except:
                pass
        print(f"Failed to acquire sidebar lock: {e}")
        sys.exit(1)
    
    try:
        app = QApplication(sys.argv)
        
        # Set application-wide dark theme
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
        app.setPalette(palette)
        
        sidebar = CosmicSidebar()
        sidebar.show_sidebar()
        
        # Cleanup on exit
        def cleanup():
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                except:
                    pass
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass
        
        import atexit
        atexit.register(cleanup)
        
        sys.exit(app.exec())
    finally:
        # Ensure lock file is removed
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except:
                pass
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except:
                pass


if __name__ == "__main__":
    main()
