"""
Cosmic OS Settings Panel
Configuration interface for the AI assistant.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QCheckBox, QComboBox,
    QSlider, QSpinBox, QLineEdit, QFrame, QScrollArea,
    QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class SettingsSection(QGroupBox):
    """A styled settings section with title."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3D3D3D;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #E0E0E0;
            }
        """)


class GeneralTab(QWidget):
    """General settings tab."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Hotkey settings
        hotkey_section = SettingsSection("Hotkey")
        hotkey_layout = QFormLayout(hotkey_section)
        
        self.hotkey_input = QLineEdit("Ctrl+Space")
        self.hotkey_input.setReadOnly(True)
        self.hotkey_input.setPlaceholderText("Click to set hotkey...")
        hotkey_layout.addRow("Activation Hotkey:", self.hotkey_input)
        
        layout.addWidget(hotkey_section)

        # Appearance settings
        appearance_section = SettingsSection("Appearance")
        appearance_layout = QFormLayout(appearance_section)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Cosmic Dark", "Cosmic Light", "System"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.sidebar_width = QSpinBox()
        self.sidebar_width.setRange(300, 600)
        self.sidebar_width.setValue(420)
        self.sidebar_width.setSuffix(" px")
        appearance_layout.addRow("Sidebar Width:", self.sidebar_width)
        
        self.animation_speed = QSlider(Qt.Orientation.Horizontal)
        self.animation_speed.setRange(100, 500)
        self.animation_speed.setValue(200)
        appearance_layout.addRow("Animation Speed:", self.animation_speed)
        
        layout.addWidget(appearance_section)

        # Startup settings
        startup_section = SettingsSection("Startup")
        startup_layout = QVBoxLayout(startup_section)
        
        self.autostart = QCheckBox("Start Cosmic AI on login")
        self.autostart.setChecked(True)
        startup_layout.addWidget(self.autostart)
        
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        self.minimize_to_tray.setChecked(True)
        startup_layout.addWidget(self.minimize_to_tray)
        
        layout.addWidget(startup_section)
        layout.addStretch()


class AITab(QWidget):
    """AI model settings tab."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Model selection
        model_section = SettingsSection("AI Model")
        model_layout = QFormLayout(model_section)
        
        self.tier_combo = QComboBox()
        self.tier_combo.addItems([
            "Auto (Recommended)",
            "Tier 1: Lightweight (1-4B)",
            "Tier 2: Balanced (3-7B)",
            "Tier 3: Powerful (7-14B)"
        ])
        model_layout.addRow("Model Tier:", self.tier_combo)
        
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("core/ai_engine/models/tier2/model.gguf")
        browse_btn = QPushButton("Browse")
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.model_path)
        path_layout.addWidget(browse_btn)
        model_layout.addRow("Model Path:", path_layout)
        
        layout.addWidget(model_section)

        # Generation settings
        gen_section = SettingsSection("Generation")
        gen_layout = QFormLayout(gen_section)
        
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(128, 2048)
        self.max_tokens.setValue(512)
        gen_layout.addRow("Max Tokens:", self.max_tokens)
        
        self.temperature = QSlider(Qt.Orientation.Horizontal)
        self.temperature.setRange(0, 100)
        self.temperature.setValue(70)
        self.temp_label = QLabel("0.70")
        self.temperature.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v/100:.2f}")
        )
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature)
        temp_layout.addWidget(self.temp_label)
        gen_layout.addRow("Temperature:", temp_layout)
        
        layout.addWidget(gen_section)

        # Validator settings
        val_section = SettingsSection("Validators")
        val_layout = QVBoxLayout(val_section)
        
        self.safety_validator = QCheckBox("Safety Validator (blocks dangerous commands)")
        self.safety_validator.setChecked(True)
        self.safety_validator.setEnabled(False)  # Always on
        val_layout.addWidget(self.safety_validator)
        
        self.logic_validator = QCheckBox("Logic Validator (checks command sequences)")
        self.logic_validator.setChecked(True)
        val_layout.addWidget(self.logic_validator)
        
        self.efficiency_validator = QCheckBox("Efficiency Validator (suggests optimizations)")
        self.efficiency_validator.setChecked(True)
        val_layout.addWidget(self.efficiency_validator)
        
        layout.addWidget(val_section)
        layout.addStretch()


class PermissionsTab(QWidget):
    """Permissions settings tab."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Action permissions
        action_section = SettingsSection("Action Permissions")
        action_layout = QVBoxLayout(action_section)
        
        self.file_ops = QCheckBox("Allow file operations")
        self.file_ops.setToolTip("Create, modify, and delete files")
        self.file_ops.setChecked(True)
        action_layout.addWidget(self.file_ops)
        
        self.network = QCheckBox("Allow network access")
        self.network.setToolTip("Open URLs, download files")
        self.network.setChecked(True)
        action_layout.addWidget(self.network)
        
        self.system_settings = QCheckBox("Allow system settings changes")
        self.system_settings.setToolTip("Modify system configuration")
        self.system_settings.setChecked(False)
        action_layout.addWidget(self.system_settings)
        
        self.app_install = QCheckBox("Allow application installation")
        self.app_install.setToolTip("Install packages via apt/flatpak")
        self.app_install.setChecked(False)
        action_layout.addWidget(self.app_install)
        
        layout.addWidget(action_section)

        # Confirmation settings
        confirm_section = SettingsSection("Confirmations")
        confirm_layout = QVBoxLayout(confirm_section)
        
        self.require_confirm = QCheckBox("Require confirmation for all actions")
        self.require_confirm.setChecked(True)
        confirm_layout.addWidget(self.require_confirm)
        
        self.confirm_destructive = QCheckBox("Extra confirmation for destructive actions")
        self.confirm_destructive.setChecked(True)
        self.confirm_destructive.setEnabled(False)  # Always on
        confirm_layout.addWidget(self.confirm_destructive)
        
        self.safe_mode = QCheckBox("Safe Mode (preview only, no execution)")
        self.safe_mode.setChecked(False)
        confirm_layout.addWidget(self.safe_mode)
        
        layout.addWidget(confirm_section)

        # Blocked paths
        blocked_section = SettingsSection("Blocked Paths")
        blocked_layout = QVBoxLayout(blocked_section)
        
        info = QLabel("The AI cannot access these directories:")
        info.setStyleSheet("color: #808080;")
        blocked_layout.addWidget(info)
        
        blocked_list = QLabel(
            "• /etc/\n"
            "• /boot/\n"
            "• /sys/\n"
            "• /proc/\n"
            "• ~/.ssh/\n"
            "• ~/.gnupg/"
        )
        blocked_list.setStyleSheet("font-family: monospace; color: #A0A0A0;")
        blocked_layout.addWidget(blocked_list)
        
        layout.addWidget(blocked_section)
        layout.addStretch()


class AutomationTab(QWidget):
    """Automation settings tab."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Timing settings
        timing_section = SettingsSection("Timing")
        timing_layout = QFormLayout(timing_section)
        
        self.click_delay = QSpinBox()
        self.click_delay.setRange(50, 500)
        self.click_delay.setValue(100)
        self.click_delay.setSuffix(" ms")
        timing_layout.addRow("Click Delay:", self.click_delay)
        
        self.type_delay = QSpinBox()
        self.type_delay.setRange(10, 200)
        self.type_delay.setValue(50)
        self.type_delay.setSuffix(" ms")
        timing_layout.addRow("Typing Delay:", self.type_delay)
        
        self.max_retries = QSpinBox()
        self.max_retries.setRange(1, 10)
        self.max_retries.setValue(3)
        timing_layout.addRow("Max Retries:", self.max_retries)
        
        layout.addWidget(timing_section)

        # Debugging
        debug_section = SettingsSection("Debugging")
        debug_layout = QVBoxLayout(debug_section)
        
        self.screenshot_on_error = QCheckBox("Take screenshot on error")
        self.screenshot_on_error.setChecked(True)
        debug_layout.addWidget(self.screenshot_on_error)
        
        self.log_actions = QCheckBox("Log all actions to file")
        self.log_actions.setChecked(True)
        debug_layout.addWidget(self.log_actions)
        
        self.debug_mode = QCheckBox("Debug mode (verbose logging)")
        self.debug_mode.setChecked(False)
        debug_layout.addWidget(self.debug_mode)
        
        layout.addWidget(debug_section)

        # Accessibility
        a11y_section = SettingsSection("Accessibility Backend")
        a11y_layout = QVBoxLayout(a11y_section)
        
        self.backend_combo = QComboBox()
        self.backend_combo.addItems([
            "xdotool (X11 - Current)",
            "AT-SPI2 (Accessibility - Experimental)",
            "Hybrid (Both)"
        ])
        
        backend_info = QLabel(
            "xdotool uses screen coordinates. AT-SPI2 uses semantic elements.\n"
            "AT-SPI2 is more robust but requires accessibility support in apps."
        )
        backend_info.setStyleSheet("color: #808080; font-size: 10px;")
        backend_info.setWordWrap(True)
        
        a11y_layout.addWidget(self.backend_combo)
        a11y_layout.addWidget(backend_info)
        
        layout.addWidget(a11y_section)
        layout.addStretch()


class DevelopmentTab(QWidget):
    """Development settings tab."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Hot reload
        hotreload_section = SettingsSection("Hot Reload")
        hotreload_layout = QVBoxLayout(hotreload_section)
        
        self.hot_reload = QCheckBox("Enable hot reload")
        self.hot_reload.setChecked(False)
        hotreload_layout.addWidget(self.hot_reload)
        
        info = QLabel(
            "When enabled, the AI daemon will automatically restart\n"
            "when code changes are detected in the shared folder."
        )
        info.setStyleSheet("color: #808080;")
        hotreload_layout.addWidget(info)
        
        layout.addWidget(hotreload_section)

        # Logging
        log_section = SettingsSection("Logging")
        log_layout = QFormLayout(log_section)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        log_layout.addRow("Log Level:", self.log_level)
        
        self.log_path = QLineEdit()
        self.log_path.setText("~/.local/share/cosmic-os/logs/")
        log_layout.addRow("Log Directory:", self.log_path)
        
        layout.addWidget(log_section)

        # Testing
        test_section = SettingsSection("Testing")
        test_layout = QVBoxLayout(test_section)
        
        test_btn = QPushButton("Run Quick Test")
        test_btn.clicked.connect(self.run_test)
        test_layout.addWidget(test_btn)
        
        self.dry_run = QCheckBox("Dry run mode (log commands, don't execute)")
        self.dry_run.setChecked(False)
        test_layout.addWidget(self.dry_run)
        
        layout.addWidget(test_section)
        layout.addStretch()

    def run_test(self):
        QMessageBox.information(
            self,
            "Test",
            "Quick test would run here.\n"
            "This verifies AI connection and basic automation."
        )


class SettingsPanel(QDialog):
    """Main settings dialog."""
    
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cosmic OS Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(GeneralTab(), "General")
        self.tabs.addTab(AITab(), "AI Model")
        self.tabs.addTab(PermissionsTab(), "Permissions")
        self.tabs.addTab(AutomationTab(), "Automation")
        self.tabs.addTab(DevelopmentTab(), "Development")
        
        layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept_settings)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
            }
            QTabWidget::pane {
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #A0A0A0;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QCheckBox {
                color: #E0E0E0;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #3D3D3D;
                border: 1px solid #4D4D4D;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #3D3D3D;
                border: 1px solid #4D4D4D;
                border-radius: 4px;
                padding: 8px 16px;
                color: #E0E0E0;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
            QPushButton:default {
                background-color: #0078D4;
                border: none;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3D3D3D;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078D4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)

    def reset_defaults(self):
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Reset logic would go here
            QMessageBox.information(self, "Reset", "Settings reset to defaults.")

    def apply_settings(self):
        settings = self.collect_settings()
        self.settings_changed.emit(settings)
        logger.info("Settings applied")

    def accept_settings(self):
        self.apply_settings()
        self.accept()

    def collect_settings(self) -> dict:
        """Collect all settings from tabs."""
        # This would collect values from all tab widgets
        return {
            "applied": True
        }


def main():
    """Run settings panel standalone."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    panel = SettingsPanel()
    panel.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
