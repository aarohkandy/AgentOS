#!/bin/bash
# Install Cosmic OS in ANOS chroot environment

set -e

export DEBIAN_FRONTEND=noninteractive

echo "Installing Cosmic OS in ANOS..."

# Install Cosmic OS dependencies
apt-get update -qq

# Install core dependencies
apt-get install -y -qq \
    python3 python3-pip python3-venv python3-pyqt6 \
    xdotool wmctrl scrot inotify-tools \
    cmake build-essential git curl wget jq \
    libdbus-1-dev libdbus-glib-1-dev || {
    echo "ERROR: Failed to install core dependencies"
    exit 1
}

# Install Python packages
cd /opt/cosmic-os
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt || {
    echo "WARN: Some packages failed, installing core packages..."
    pip install --quiet llama-cpp-python PyQt6 Pillow psutil requests aiohttp python-dotenv pydantic || true
}

# Create model directories
mkdir -p /opt/cosmic-os/core/ai_engine/models/{tier1,tier2,tier3,validators}

# Setup systemd service
mkdir -p /etc/skel/.config/systemd/user
cat > /etc/skel/.config/systemd/user/cosmic-ai.service << 'EOF'
[Unit]
Description=Cosmic OS AI Assistant
After=graphical-session.target

[Service]
Type=simple
ExecStart=/opt/cosmic-os/venv/bin/python3 /opt/cosmic-os/core/ai_engine/main.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=PYTHONPATH=/opt/cosmic-os

[Install]
WantedBy=graphical-session.target
EOF

# Setup autostart
mkdir -p /etc/skel/.config/autostart
cat > /etc/skel/.config/autostart/cosmic-ai.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Cosmic AI
Exec=/opt/cosmic-os/venv/bin/python3 /opt/cosmic-os/core/ai_engine/main.py
Icon=applications-science
Terminal=false
X-KDE-autostart-phase=2
EOF

# Make scripts executable
chmod +x /opt/cosmic-os/install.sh 2>/dev/null || true
chmod +x /opt/cosmic-os/scripts/*.sh 2>/dev/null || true
chmod +x /opt/cosmic-os/core/system-config/*.sh 2>/dev/null || true

echo "Cosmic OS installed successfully"




