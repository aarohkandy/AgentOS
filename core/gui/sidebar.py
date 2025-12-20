import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QObject
from PyQt6.QtGui import QColor, QPalette

class Sidebar(QWidget):
    def __init__(self, ipc_client=None):
        super().__init__()
        self.ipc_client = ipc_client
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle('Cosmic AI')
        # Sidebar dimensions usually handled by window manager (kwin) or fixed position
        self.setGeometry(100, 100, 400, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Styling (basic dark mode)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 240);
                color: white;
                border-radius: 10px;
                font-family: Inter, sans-serif;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTextEdit {
                background-color: transparent;
                border: none;
            }
        """)

        # Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        # Input Area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask AI to do something...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Command Preview Area (Hidden by default)
        self.preview_area = QWidget()
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("Proposed Plan:")
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        
        btn_layout = QHBoxLayout()
        self.approve_btn = QPushButton("Approve")
        self.deny_btn = QPushButton("Deny")
        self.approve_btn.clicked.connect(self.approve_plan)
        self.deny_btn.clicked.connect(self.deny_plan)
        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.deny_btn)

        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_text)
        preview_layout.addLayout(btn_layout)
        self.preview_area.setLayout(preview_layout)
        self.preview_area.hide()
        
        layout.addWidget(self.preview_area)
        
        self.current_plan = None

    def send_message(self):
        text = self.input_field.text()
        if not text:
            return
            
        self.chat_history.append(f"<b>You:</b> {text}")
        self.input_field.clear()
        
        if self.ipc_client:
            # Async call ideally
            response = self.ipc_client.send_request(text)
            self.handle_ai_response(response)
        else:
            # Mock response for UI testing
            self.chat_history.append("<i>AI: (No backend connected)</i>")

    def handle_ai_response(self, response):
        if "plan" in response:
            self.current_plan = response
            steps = response.get("plan", [])
            description = response.get("description", "No description")
            
            preview_str = f"<b>Goal:</b> {description}<br><br><b>Steps:</b><br>"
            for i, step in enumerate(steps):
                preview_str += f"{i+1}. {step.get('action')} {step.get('target', '')} {step.get('text', '')}<br>"
            
            self.preview_text.setHtml(preview_str)
            self.preview_area.show()
            self.chat_history.append("<i>AI: I have a plan. Please approve.</i>")
        else:
            self.chat_history.append(f"<b>AI:</b> {response}")

    def approve_plan(self):
        self.chat_history.append("<i>System: Executing plan...</i>")
        self.preview_area.hide()
        # TODO: Send approval back to backend
        
    def deny_plan(self):
        self.chat_history.append("<i>System: Plan cancelled.</i>")
        self.preview_area.hide()
        self.current_plan = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Sidebar()
    sys.exit(app.exec())
