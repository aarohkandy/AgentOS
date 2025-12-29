"""
Cosmic OS AI Sidebar
Main AI assistant interface - slides in from right side (Perplexity Comet style).
Triggered by Super+Shift (Windows+Shift) global hotkey.
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

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel,
    QScrollArea, QFrame, QSizePolicy, QGraphicsOpacityEffect
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
    Manages screen work area when sidebar opens/closes.
    Uses _NET_WM_STRUT to reserve screen space, making the system
    think the available screen area is reduced. This causes maximized
    and fullscreen windows to automatically only use the left portion.
    """
    
    def __init__(self):
        self.xprop = shutil.which("xprop")
        self.sidebar_window_id: Optional[int] = None
        self.strut_set = False
        
    def set_sidebar_window_id(self, window_id: int):
        """Set the sidebar's window ID for setting strut property."""
        self.sidebar_window_id = window_id
    
    def set_strut(self, sidebar_width: int, screen_height: int):
        """
        Set _NET_WM_STRUT property to reserve right edge of screen.
        
        Args:
            sidebar_width: Width of sidebar (pixels to reserve on right)
            screen_height: Total screen height
        """
        if not self.xprop or not self.sidebar_window_id:
            logger.warning("xprop not available or sidebar window ID not set")
            return
        
        try:
            # _NET_WM_STRUT format: left, right, top, bottom (in pixels)
            # We want to reserve the right edge, so:
            # left=0, right=sidebar_width, top=0, bottom=0
            # But _NET_WM_STRUT_PARTIAL is better - it allows per-edge specification
            # Format: left, right, top, bottom, left_start_y, left_end_y, right_start_y, right_end_y, top_start_x, top_end_x, bottom_start_x, bottom_end_x
            
            # Use _NET_WM_STRUT_PARTIAL for more precise control
            # Reserve right edge from top (0) to bottom (screen_height)
            cmd = [
                self.xprop,
                "-id", str(self.sidebar_window_id),
                "-f", "_NET_WM_STRUT_PARTIAL", "32c",
                "-set", "_NET_WM_STRUT_PARTIAL",
                f"0, {sidebar_width}, 0, 0, 0, 0, 0, {screen_height}, 0, 0, 0, 0"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            # Also set the simpler _NET_WM_STRUT for compatibility
            cmd_simple = [
                self.xprop,
                "-id", str(self.sidebar_window_id),
                "-f", "_NET_WM_STRUT", "32c",
                "-set", "_NET_WM_STRUT",
                f"0, {sidebar_width}, 0, 0"
            ]
            
            subprocess.run(
                cmd_simple,
                capture_output=True,
                text=True,
                check=False,  # Don't fail if this doesn't work
                timeout=5
            )
            
            self.strut_set = True
            logger.info(f"Set _NET_WM_STRUT to reserve {sidebar_width}px on right edge")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set _NET_WM_STRUT: {e}")
        except Exception as e:
            logger.error(f"Error setting strut: {e}")
    
    def remove_strut(self):
        """Remove _NET_WM_STRUT property to restore full screen area."""
        if not self.xprop or not self.sidebar_window_id or not self.strut_set:
            return
        
        try:
            # Remove both strut properties
            cmd = [
                self.xprop,
                "-id", str(self.sidebar_window_id),
                "-remove", "_NET_WM_STRUT_PARTIAL"
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=5)
            
            cmd = [
                self.xprop,
                "-id", str(self.sidebar_window_id),
                "-remove", "_NET_WM_STRUT"
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=5)
            
            self.strut_set = False
            logger.info("Removed _NET_WM_STRUT, restored full screen area")
            
        except Exception as e:
            logger.error(f"Error removing strut: {e}")


class AIWorker(QThread):
    """Worker thread for AI communication."""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, socket_path: str = "/tmp/cosmic-ai.sock"):
        super().__init__()
        self.socket_path = socket_path
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
            sock.settimeout(5)  # 5 second timeout
            sock.connect(self.socket_path)
            sock.sendall(self.message.encode('utf-8'))
            
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            sock.close()
            
            result = json.loads(response.decode('utf-8'))
            self.result_ready.emit(result)
        except FileNotFoundError:
            self.error_occurred.emit("AI daemon not running. Start with: ./scripts/start-cosmic-test.sh")
        except ConnectionRefusedError:
            self.error_occurred.emit("AI daemon not responding. Check if it's running.")
        except Exception as e:
            self.error_occurred.emit(str(e))


class MessageBubble(QFrame):
    """Chat message bubble widget."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setup_ui(text)

    def setup_ui(self, text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        label.setOpenExternalLinks(True)
        label.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML rendering
        
        font = QFont("Segoe UI", 11)
        label.setFont(font)
        
        if self.is_user:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #0078D4;
                    border-radius: 12px;
                    margin-left: 40px;
                }
                QLabel {
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #2D2D2D;
                    border-radius: 12px;
                    margin-right: 40px;
                }
                QLabel {
                    color: #E0E0E0;
                }
            """)
        
        layout.addWidget(label)


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
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 0.95);
                border-left: 1px solid #3D3D3D;
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
                background: #2D2D2D;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #5D5D5D;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        
        self.chat_scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.chat_scroll, 1)

        # Input area
        input_area = self._create_input_area()
        main_layout.addWidget(input_area)

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-bottom: 1px solid #3D3D3D;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)

        # Title
        title = QLabel("✨ Cosmic AI")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #E0E0E0;")
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
                background-color: #252525;
                border-top: 1px solid #3D3D3D;
            }
        """)
        
        layout = QHBoxLayout(input_frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Cosmic AI...")
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #3D3D3D;
                border: 1px solid #4D4D4D;
                border-radius: 20px;
                padding: 10px 16px;
                color: #E0E0E0;
            }
            QLineEdit:focus {
                border-color: #0078D4;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        layout.addWidget(self.input_field, 1)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(40, 40)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1084D8;
            }
            QPushButton:pressed {
                background-color: #006CBD;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(send_btn)

        return input_frame

    def setup_animations(self):
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(200)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def setup_connections(self):
        self.ai_worker.result_ready.connect(self.handle_ai_response)
        self.ai_worker.error_occurred.connect(self.handle_ai_error)

    def setup_global_hotkey(self):
        # Note: This only works when the app has focus
        # For true global hotkey, need to use system-level binding
        # (handled by KDE keybinding config)
        pass
    
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
        if self.is_visible:
            return
        
        self.show()
        
        # Update sidebar window ID now that window is shown
        QTimer.singleShot(50, self._set_sidebar_window_id)
        
        # Get screen dimensions
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        screen_height = screen_geo.height()
        
        # Set strut to reserve screen space (with small delay to ensure window is ready)
        QTimer.singleShot(100, lambda: self.window_resize_manager.set_strut(
            self.sidebar_width,
            screen_height
        ))
        
        self.slide_anim.setStartValue(self.hidden_pos)
        self.slide_anim.setEndValue(self.shown_pos)
        self.slide_anim.start()
        self.is_visible = True
        self.input_field.setFocus()

    def hide_sidebar(self):
        if not self.is_visible:
            return
        
        self.slide_anim.setStartValue(self.shown_pos)
        self.slide_anim.setEndValue(self.hidden_pos)
        self.slide_anim.start()
        self.slide_anim.finished.connect(self._on_hide_complete)
        self.is_visible = False

    def _on_hide_complete(self):
        self.hide()
        self.slide_anim.finished.disconnect(self._on_hide_complete)
        
        # Remove strut to restore full screen area
        self.window_resize_manager.remove_strut()

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self.add_message(text, is_user=True)
        
        # Show loading indicator
        self.add_loading()
        
        # Send to AI
        self.ai_worker.set_message(text)
        self.ai_worker.start()

    def add_message(self, text: str, is_user: bool = True):
        bubble = MessageBubble(text, is_user=is_user)
        self.chat_layout.addWidget(bubble)
        self.messages.append({"text": text, "is_user": is_user})
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def add_loading(self):
        self.loading_label = QLabel("🔄 Thinking...")
        self.loading_label.setStyleSheet("color: #808080; padding: 8px;")
        self.chat_layout.addWidget(self.loading_label)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def remove_loading(self):
        if hasattr(self, 'loading_label'):
            self.loading_label.deleteLater()
            del self.loading_label

    def _scroll_to_bottom(self):
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_ai_response(self, result: dict):
        self.remove_loading()
        
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
        
        QTimer.singleShot(50, self._scroll_to_bottom)

    def handle_ai_error(self, error: str):
        self.remove_loading()
        self.add_message(f"❌ Connection error: {error}", is_user=False)

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
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
