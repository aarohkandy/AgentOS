import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTabWidget, 
                             QFormLayout, QCheckBox, QComboBox, QSlider, QLabel)
from PyQt6.QtCore import Qt

class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosmic OS Settings")
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.tabs.addTab(self.create_ai_tab(), "AI Engine")
        self.tabs.addTab(self.create_gui_tab(), "Appearance")
        self.tabs.addTab(self.create_system_tab(), "System")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def create_ai_tab(self):
        tab = QWidget()
        form = QFormLayout()
        
        self.tier_combo = QComboBox()
        self.tier_combo.addItems(["Tier 1 (Qwen 3B)", "Tier 2 (Qwen 7B)", "Tier 3 (Qwen 14B)"])
        form.addRow("Active Model:", self.tier_combo)
        
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(70)
        form.addRow("Temperature:", self.temp_slider)
        
        tab.setLayout(form)
        return tab

    def create_gui_tab(self):
        tab = QWidget()
        form = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Cosmic Dark", "Cosmic Light", "System Default"])
        form.addRow("Theme:", self.theme_combo)
        
        self.blur_check = QCheckBox("Enable Blur Effects")
        self.blur_check.setChecked(True)
        form.addRow("", self.blur_check)
        
        tab.setLayout(form)
        return tab

    def create_system_tab(self):
        tab = QWidget()
        form = QFormLayout()
        
        form.addRow("Auto-Update:", QCheckBox("Enabled"))
        form.addRow("Telemetry:", QCheckBox("Disabled"))
        
        tab.setLayout(form)
        return tab

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SettingsPanel()
    window.show()
    sys.exit(app.exec())

