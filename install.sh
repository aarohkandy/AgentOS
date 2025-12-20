#!/bin/bash
# Cosmic OS Installation Script

set -e

# Check for root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

echo "Installing Cosmic OS..."

# Install dependencies
apt-get update
apt-get install -y python3-pip python3-venv python3-dev build-essential \
    xdotool inotify-tools libdbus-1-dev libglib2.0-dev

# Create install dir
INSTALL_DIR="/opt/cosmic-os"
mkdir -p $INSTALL_DIR
cp -r . $INSTALL_DIR/

# Setup Python venv
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Models
chmod +x scripts/*.sh
./scripts/detect-hardware.sh
./scripts/install-models.sh

# Systemd
# Assume user 1000 for now or current real user if invoked differently
# Ideally we install as user service for the actual user
# Copying to global skeletal directory or instructing user
echo "To enable services, run:"
echo "cp $INSTALL_DIR/core/system-config/autostart/cosmic-ai.desktop ~/.config/autostart/"

echo "Installation complete."
