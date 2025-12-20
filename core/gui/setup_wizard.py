import sys
from PyQt6.QtWidgets import (QApplication, QWizard, QWizardPage, QVBoxLayout, 
                             QLabel, QRadioButton, QButtonGroup, QLineEdit, QCheckBox)

class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosmic OS Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        self.addPage(WelcomePage())
        self.addPage(HardwarePage())
        self.addPage(ThemePage())
        self.addPage(ConclusionPage())
        
        self.resize(600, 400)

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Cosmic OS")
        layout = QVBoxLayout()
        label = QLabel("Welcome to the future of AI-integrated computing.\n\nThis wizard will catch you up to speed.")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setLayout(layout)

class HardwarePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Hardware Tier Selection")
        self.setSubTitle("We detected your hardware. Confirm your AI tier.")
        layout = QVBoxLayout()
        
        self.group = QButtonGroup(self)
        self.r1 = QRadioButton("Tier 1 (Low Spec / Laptop)")
        self.r2 = QRadioButton("Tier 2 (Mid Range / Desktop) [Recommended]")
        self.r3 = QRadioButton("Tier 3 (High End / GPU)")
        
        # In real app, pre-select based on /tmp/cosmic_tier
        self.r2.setChecked(True)
        
        layout.addWidget(self.r1)
        layout.addWidget(self.r2)
        layout.addWidget(self.r3)
        self.group.addButton(self.r1)
        self.group.addButton(self.r2)
        self.group.addButton(self.r3)
        
        self.setLayout(layout)

class ThemePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Design Preference")
        layout = QVBoxLayout()
        
        self.chk_theme = QCheckBox("Enable WhiteSur Dark Theme")
        self.chk_theme.setChecked(True)
        self.chk_dock = QCheckBox("Enable Latte Dock (iOS Style)")
        self.chk_dock.setChecked(True)
        
        layout.addWidget(self.chk_theme)
        layout.addWidget(self.chk_dock)
        self.setLayout(layout)

class ConclusionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("All Set!")
        layout = QVBoxLayout()
        label = QLabel("Press Finish to apply settings and launch Cosmic AI.")
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())
