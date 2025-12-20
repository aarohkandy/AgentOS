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

echo ""
echo "Would you like to run the Visual Setup (KDE/Dock/Theme)? (y/n)"
read -r -p "Select y to transform desktop layout: " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    # We must run these as the SUDO_USER if available, or current user
    # because visual settings are user-specific, not root
    REAL_USER=${SUDO_USER:-$USER}
    echo "Running visual setup as user: $REAL_USER"
    
    chmod +x $INSTALL_DIR/core/system-config/*.sh
    
    su - $REAL_USER -c "$INSTALL_DIR/core/system-config/kde-plasma-setup.sh"
    su - $REAL_USER -c "$INSTALL_DIR/core/system-config/latte-dock-config.sh"
    su - $REAL_USER -c "$INSTALL_DIR/core/system-config/theme-setup.sh"
else
    echo "Skipping visual setup. You can run scripts in core/system-config/ later."
fi

echo "Installation complete."
