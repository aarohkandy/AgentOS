"""
AI Agent Overlay Interface.
Built with PyQt6 for a modern, animated, always-on-top experience.
"""

import sys
import os
import logging

# Add src to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QGraphicsDropShadowEffect, QLineEdit,
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import (Qt, QPropertyAnimation, QRect, QTimer, QEasingCurve, 
                          QPoint, QThread, pyqtSignal, QSize)
from PyQt6.QtGui import QColor, QPalette, QBrush, QCursor, QFont

from src.agent.agent_core import Agent, AgentConfig
from src.agent.llm_interface import EchoBackend
from src.agent.types import Message

class AgentWorker(QThread):
    """Background thread to run the Agent so UI doesn't freeze."""
    response_ready = pyqtSignal(str)
    
    def __init__(self, agent, user_text):
        super().__init__()
        self.agent = agent
        self.user_text = user_text
        
    def run(self):
        # Create message object
        msg = Message(role="user", content=self.user_text)
        # Run agent
        result = self.agent.run([msg])
        # Emit result
        self.response_ready.emit(result.final_answer)

class MessageBubble(QFrame):
    """A styled chat bubble."""
    def __init__(self, text, is_user=False):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWidth(0)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Bubble Container
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setFont(QFont("Segoe UI", 11))
        
        # Style based on sender
        if is_user:
            layout.addStretch()
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #0078D4;
                    color: white;
                    border-radius: 15px;
                    padding: 10px 15px;
                }
            """)
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #2D2D30;
                    color: #E0E0E0;
                    border-radius: 15px;
                    padding: 10px 15px;
                    border: 1px solid #3E3E42;
                }
            """)
            layout.addWidget(bubble)
            layout.addStretch()

class AgentSidebar(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize Agent
        self.backend = EchoBackend() # Placeholder until real LLM
        self.agent = Agent(backend=self.backend)
        
        # Screen Setup
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.screen_width = geometry.width() + geometry.x()
        self.screen_height = geometry.height()
        self.screen_top = geometry.y()
        
        self.sidebar_width = 450
        self.is_visible = False
        
        # Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Initial Geometry
        self.setGeometry(self.screen_width, self.screen_top, self.sidebar_width, self.screen_height)
        
        self.init_ui()
        
        # Animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def init_ui(self):
        # Main Container
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.sidebar_width, self.screen_height)
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(18, 18, 24, 0.98);
                border-left: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 40, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("AgentOS")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #00ff9d; font-size: 12px;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        layout.addLayout(header_layout)
        
        # Chat Area (Scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 8px; background: transparent; }
            QScrollBar::handle:vertical { background: #444; border-radius: 4px; }
        """)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch() # Push messages to bottom
        
        self.scroll_area.setWidget(self.chat_widget)
        layout.addWidget(self.scroll_area)
        
        # Input Area
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask AgentOS...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                color: white;
                border: 1px solid #3E3E42;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
            }
        """)
        self.input_field.returnPressed.connect(self.handle_submit)
        layout.addWidget(self.input_field)
        
        # Add initial welcome message
        self.add_message("System Online. How can I help you?", is_user=False)
        
    def add_message(self, text, is_user=False):
        bubble = MessageBubble(text, is_user)
        self.chat_layout.addWidget(bubble)
        # Scroll to bottom
        QTimer.singleShot(10, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
    def handle_submit(self):
        text = self.input_field.text().strip()
        if not text:
            return
            
        # Clear input
        self.input_field.clear()
        
        # Show user message
        self.add_message(text, is_user=True)
        
        # Set status to thinking
        self.status_indicator.setStyleSheet("color: #ffaa00;") # Orange
        
        # Run Agent in background
        self.worker = AgentWorker(self.agent, text)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.start()
        
    def handle_response(self, response):
        self.add_message(response, is_user=False)
        self.status_indicator.setStyleSheet("color: #00ff9d;") # Green
        
    def slide_in(self):
        if self.is_visible: return
        self.is_visible = True
        self.show()
        self.anim.setStartValue(QPoint(self.screen_width, self.screen_top))
        self.anim.setEndValue(QPoint(self.screen_width - self.sidebar_width, self.screen_top))
        self.anim.start()
        self.input_field.setFocus()
        
    def slide_out(self):
        if not self.is_visible: return
        # Don't close if input has focus or text? No, let's stick to mouse logic for now
        self.is_visible = False
        self.anim.setStartValue(QPoint(self.screen_width - self.sidebar_width, self.screen_top))
        self.anim.setEndValue(QPoint(self.screen_width, self.screen_top))
        self.anim.start()

class EdgeTrigger(QWidget):
    """Invisible 1px window on the right edge to detect mouse entry."""
    def __init__(self, sidebar):
        super().__init__()
        self.sidebar = sidebar
        
        # Screen Setup
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        
        # 2px wide trigger zone on the far right
        self.setGeometry(
            geometry.width() + geometry.x() - 2, 
            geometry.y(), 
            2, 
            geometry.height()
        )
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.show()

    def enterEvent(self, event):
        """Mouse entered the edge!"""
        self.sidebar.slide_in()

def main():
    # Setup logging
    logging.basicConfig(
        filename='/tmp/agent-overlay.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Starting AgentOS Overlay...")
    
    try:
        app = QApplication(sys.argv)
        
        # Create Sidebar
        sidebar = AgentSidebar()
        
        # Create Edge Trigger
        trigger = EdgeTrigger(sidebar)
        
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Overlay crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
