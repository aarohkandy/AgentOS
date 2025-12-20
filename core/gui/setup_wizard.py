"""
Cosmic OS Setup Wizard
First-boot setup experience for configuring the AI assistant.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup, QProgressBar,
    QCheckBox, QFrame, QLineEdit, QComboBox, QTextEdit, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor

logger = logging.getLogger(__name__)


class HardwareDetectionWorker(QThread):
    """Worker thread for detecting hardware capabilities."""
    finished = pyqtSignal(dict)

    def run(self):
        import psutil
        import subprocess
        
        result = {
            "ram_gb": psutil.virtual_memory().total / (1024 ** 3),
            "cpu_cores": psutil.cpu_count(),
            "has_nvidia_gpu": False,
            "has_amd_gpu": False,
            "recommended_tier": 1
        }
        
        # Check for NVIDIA GPU
        try:
            subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            result["has_nvidia_gpu"] = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        # Check for AMD GPU
        try:
            lspci = subprocess.run(
                ["lspci"],
                capture_output=True,
                text=True
            )
            if "AMD" in lspci.stdout and "VGA" in lspci.stdout:
                result["has_amd_gpu"] = True
        except Exception:
            pass
        
        # Determine recommended tier
        if result["ram_gb"] > 16 or result["has_nvidia_gpu"]:
            result["recommended_tier"] = 3
        elif result["ram_gb"] >= 8:
            result["recommended_tier"] = 2
        else:
            result["recommended_tier"] = 1
        
        self.finished.emit(result)


class ModelDownloadWorker(QThread):
    """Worker thread for downloading AI models."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, tier: int):
        super().__init__()
        self.tier = tier

    def run(self):
        # Simulated download - in production, use huggingface_hub
        import time
        
        model_info = {
            1: ("SmolLM 1.7B", 1.7),
            2: ("Qwen2.5 3B", 3.0),
            3: ("Qwen2.5 7B", 7.0)
        }
        
        name, size = model_info.get(self.tier, ("Unknown", 1.0))
        
        self.progress.emit(0, f"Preparing to download {name}...")
        time.sleep(0.5)
        
        # Simulate download progress
        for i in range(100):
            self.progress.emit(i + 1, f"Downloading {name}... {i+1}%")
            time.sleep(0.05)
        
        self.progress.emit(100, "Verifying download...")
        time.sleep(0.5)
        
        self.finished.emit(True, f"Successfully downloaded {name}")


class WelcomePage(QWizardPage):
    """Welcome page with introduction."""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Cosmic OS")
        self.setSubTitle("Your AI-powered desktop experience")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Logo/Icon placeholder
        icon_label = QLabel("✨")
        icon_label.setFont(QFont("Segoe UI", 72))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Welcome text
        welcome = QLabel(
            "Cosmic OS brings AI directly into your desktop experience.\n\n"
            "With a simple keystroke (Ctrl+Space), summon an intelligent assistant "
            "that can help you navigate, automate tasks, and control your computer "
            "through natural conversation.\n\n"
            "This wizard will help you set up Cosmic OS for your system."
        )
        welcome.setWordWrap(True)
        welcome.setFont(QFont("Segoe UI", 11))
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome)
        
        layout.addStretch()


class HardwareDetectionPage(QWizardPage):
    """Hardware detection and tier selection page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Hardware Detection")
        self.setSubTitle("Detecting your system capabilities...")
        
        self.hardware_info = None
        self.detection_complete = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Detection status
        self.status_label = QLabel("🔍 Scanning hardware...")
        self.status_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.status_label)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress)
        
        # Results frame (hidden initially)
        self.results_frame = QFrame()
        self.results_frame.setVisible(False)
        results_layout = QVBoxLayout(self.results_frame)
        
        self.specs_label = QLabel()
        self.specs_label.setFont(QFont("Segoe UI", 10))
        results_layout.addWidget(self.specs_label)
        
        # Tier selection
        tier_label = QLabel("Select AI Model Tier:")
        tier_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        results_layout.addWidget(tier_label)
        
        self.tier_group = QButtonGroup(self)
        
        self.tier1_radio = QRadioButton("Tier 1: Lightweight (1-4B params)")
        self.tier1_radio.setToolTip("Best for systems with <8GB RAM. Fast but less capable.")
        self.tier_group.addButton(self.tier1_radio, 1)
        results_layout.addWidget(self.tier1_radio)
        
        self.tier2_radio = QRadioButton("Tier 2: Balanced (3-7B params)")
        self.tier2_radio.setToolTip("Best for systems with 8-16GB RAM. Good balance.")
        self.tier_group.addButton(self.tier2_radio, 2)
        results_layout.addWidget(self.tier2_radio)
        
        self.tier3_radio = QRadioButton("Tier 3: Powerful (7-14B params)")
        self.tier3_radio.setToolTip("Best for systems with >16GB RAM or GPU. Most capable.")
        self.tier_group.addButton(self.tier3_radio, 3)
        results_layout.addWidget(self.tier3_radio)
        
        self.recommendation_label = QLabel()
        self.recommendation_label.setStyleSheet("color: #4CAF50;")
        results_layout.addWidget(self.recommendation_label)
        
        layout.addWidget(self.results_frame)
        layout.addStretch()
        
        # Register field
        self.registerField("tier*", self.tier1_radio)

    def initializePage(self):
        self.worker = HardwareDetectionWorker()
        self.worker.finished.connect(self.on_detection_complete)
        self.worker.start()

    def on_detection_complete(self, info: dict):
        self.hardware_info = info
        self.detection_complete = True
        
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status_label.setText("✅ Hardware detection complete")
        
        # Show specs
        gpu = "NVIDIA GPU" if info["has_nvidia_gpu"] else (
            "AMD GPU" if info["has_amd_gpu"] else "No dedicated GPU"
        )
        self.specs_label.setText(
            f"RAM: {info['ram_gb']:.1f} GB\n"
            f"CPU Cores: {info['cpu_cores']}\n"
            f"GPU: {gpu}"
        )
        
        # Set recommendation
        rec_tier = info["recommended_tier"]
        self.recommendation_label.setText(f"✨ Recommended: Tier {rec_tier}")
        
        # Select recommended tier
        if rec_tier == 1:
            self.tier1_radio.setChecked(True)
        elif rec_tier == 2:
            self.tier2_radio.setChecked(True)
        else:
            self.tier3_radio.setChecked(True)
        
        self.results_frame.setVisible(True)
        self.completeChanged.emit()

    def isComplete(self):
        return self.detection_complete and self.tier_group.checkedId() > 0

    def get_selected_tier(self) -> int:
        return self.tier_group.checkedId()


class PermissionsPage(QWizardPage):
    """Permissions configuration page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Permissions")
        self.setSubTitle("Configure what Cosmic AI can do")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        info = QLabel(
            "Cosmic AI needs certain permissions to help you effectively. "
            "You can always change these later in settings."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Permissions checkboxes
        self.file_ops = QCheckBox("Allow file operations (create, modify files)")
        self.file_ops.setChecked(True)
        layout.addWidget(self.file_ops)
        
        self.network = QCheckBox("Allow network access (open URLs, download)")
        self.network.setChecked(True)
        layout.addWidget(self.network)
        
        self.system = QCheckBox("Allow system settings changes")
        self.system.setChecked(False)
        layout.addWidget(self.system)
        
        self.confirm = QCheckBox("Require confirmation before executing actions")
        self.confirm.setChecked(True)
        self.confirm.setEnabled(False)  # Always required for safety
        layout.addWidget(self.confirm)
        
        # Warning
        warning = QLabel(
            "⚠️ All commands are validated by 3 safety AI models before execution. "
            "Dangerous operations are automatically blocked."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #FFA000;")
        layout.addWidget(warning)
        
        layout.addStretch()
        
        # Register fields
        self.registerField("allow_file_ops", self.file_ops)
        self.registerField("allow_network", self.network)
        self.registerField("allow_system", self.system)


class ModelDownloadPage(QWizardPage):
    """Model download page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Download AI Models")
        self.setSubTitle("Downloading required AI models...")
        
        self.download_complete = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        self.status_label = QLabel("Preparing download...")
        self.status_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.details_label)
        
        # Skip button for testing
        skip_btn = QPushButton("Skip (for testing without models)")
        skip_btn.clicked.connect(self.skip_download)
        layout.addWidget(skip_btn)
        
        layout.addStretch()

    def initializePage(self):
        # Get selected tier from previous page
        tier = self.wizard().page(1).get_selected_tier()
        
        self.worker = ModelDownloadWorker(tier)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, value: int, message: str):
        self.progress.setValue(value)
        self.status_label.setText(message)

    def on_finished(self, success: bool, message: str):
        self.download_complete = True
        if success:
            self.status_label.setText("✅ " + message)
        else:
            self.status_label.setText("❌ " + message)
        self.completeChanged.emit()

    def skip_download(self):
        self.download_complete = True
        self.status_label.setText("⚠️ Skipped - AI will run in demo mode")
        self.progress.setValue(100)
        self.completeChanged.emit()

    def isComplete(self):
        return self.download_complete


class CompletePage(QWizardPage):
    """Setup complete page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete!")
        self.setSubTitle("Cosmic OS is ready to use")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Success icon
        icon = QLabel("🎉")
        icon.setFont(QFont("Segoe UI", 64))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # Instructions
        instructions = QLabel(
            "Cosmic OS has been configured successfully!\n\n"
            "To use the AI assistant:\n"
            "• Press Ctrl+Space to open the sidebar\n"
            "• Type your request in natural language\n"
            "• Review and approve the command plan\n"
            "• Watch as Cosmic AI executes your request\n\n"
            "Tip: Try saying 'Open Firefox and go to google.com'"
        )
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Segoe UI", 11))
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        layout.addStretch()


class SetupWizard(QWizard):
    """Main setup wizard."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosmic OS Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 500)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Add pages
        self.addPage(WelcomePage())
        self.addPage(HardwareDetectionPage())
        self.addPage(PermissionsPage())
        self.addPage(ModelDownloadPage())
        self.addPage(CompletePage())
        
        self.finished.connect(self.on_finished)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWizard {
                background-color: #1E1E1E;
            }
            QWizardPage {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QRadioButton, QCheckBox {
                color: #E0E0E0;
            }
            QLineEdit {
                background-color: #3D3D3D;
                border: 1px solid #4D4D4D;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #0078D4;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1084D8;
            }
            QProgressBar {
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                text-align: center;
                background-color: #2D2D2D;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
        """)

    def on_finished(self, result: int):
        if result == QWizard.DialogCode.Accepted:
            self.save_configuration()

    def save_configuration(self):
        """Save wizard configuration to cosmic-os.conf."""
        config_path = Path("config/cosmic-os.conf")
        
        # Get values from pages
        tier = self.page(1).get_selected_tier()
        allow_file_ops = self.field("allow_file_ops")
        allow_network = self.field("allow_network")
        allow_system = self.field("allow_system")
        
        # Update config (in production, use proper config writer)
        logger.info(f"Saving config: tier={tier}, file_ops={allow_file_ops}")
        
        # Mark first_run as false
        # This would update the config file


def main():
    """Run the setup wizard."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    wizard = SetupWizard()
    wizard.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
