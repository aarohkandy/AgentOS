"""
AI Agent Overlay Interface.
Built with PyQt6 for a modern, animated, always-on-top experience.
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPalette, QBrush

# Global mouse listener (needs to be in a separate thread usually, 
# but for this prototype we might poll or use a library like pynput in a thread)
from pynput import mouse

class AgentSidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.screen_width = QApplication.primaryScreen().size().width()
        self.screen_height = QApplication.primaryScreen().size().height()
        self.sidebar_width = 400
        self.is_visible = False
        
        # Window Setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Initial Geometry (Hidden off-screen to the right)
        self.setGeometry(self.screen_width, 0, self.sidebar_width, self.screen_height)
        
        # Styling
        self.init_ui()
        
        # Animation Setup
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300) # ms
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Mouse Listener
        self.listener = mouse.Listener(on_move=self.on_mouse_move)
        self.listener.start()
        
        # Debounce timer for mouse events to avoid spam
        self.mouse_check_timer = QTimer()
        self.mouse_check_timer.setSingleShot(True)
        
    def init_ui(self):
        # Main Container with Glass-morphism look
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.sidebar_width, self.screen_height)
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 30, 0.95);
                border-left: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0px;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 40, 20, 20)
        
        # Header
        title = QLabel("AgentOS")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)
        layout.addWidget(title)
        
        # Status
        self.status = QLabel("● Online")
        self.status.setStyleSheet("color: #00ff00; font-size: 14px;")
        layout.addWidget(self.status)
        
        layout.addStretch()
        
    def slide_in(self):
        if self.is_visible: return
        self.is_visible = True
        self.show()
        self.raise_() # Bring to front
        
        # Animate from Off-Screen (Right) to On-Screen (Right Edge)
        start_pos = QPoint(self.screen_width, 0)
        end_pos = QPoint(self.screen_width - self.sidebar_width, 0)
        
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.start()
        print("Sidebar sliding IN")
        
    def slide_out(self):
        if not self.is_visible: return
        self.is_visible = False
        
        # Animate from On-Screen to Off-Screen
        start_pos = QPoint(self.screen_width - self.sidebar_width, 0)
        end_pos = QPoint(self.screen_width, 0)
        
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.start()
        print("Sidebar sliding OUT")

    def on_mouse_move(self, x, y):
        # Debug print to see if we are getting events
        # print(f"Mouse: {x}, {y}") 
        
        # Trigger zone: Rightmost 5 pixels
        if x >= self.screen_width - 5:
            QTimer.singleShot(0, self.slide_in)
        
        # Close zone: If mouse moves left of the sidebar
        elif x < self.screen_width - self.sidebar_width - 50:
             QTimer.singleShot(0, self.slide_out)

def main():
    app = QApplication(sys.argv)
    
    # Force update screen size
    screen = app.primaryScreen()
    rect = screen.geometry()
    print(f"Screen Resolution: {rect.width()}x{rect.height()}")
    
    sidebar = AgentSidebar()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
