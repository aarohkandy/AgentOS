#!/bin/bash

# Cosmic OS Installation Script
# This script installs all dependencies and sets up the environment for Cosmic OS

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Cosmic OS Installation...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Please run as root${NC}"
  exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
else
    echo -e "${RED}Cannot detect OS. This script requires Ubuntu/Kubuntu 24.04 LTS.${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS $VERSION${NC}"

# Check system requirements
TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
if [ $TOTAL_MEM -lt 8000000 ]; then
    echo -e "${RED}Warning: Less than 8GB RAM detected. Cosmic OS may run slowly.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install system dependencies
echo -e "${BLUE}Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3-pip python3-venv python3-dev build-essential \
    xdotool inotify-tools libdbus-1-dev libglib2.0-dev

# specific KDE packages if on Kubuntu likely already there, but ensuring
# apt-get install -y plasma-desktop latte-dock # Uncomment if needed and not present

# Create installation directory
INSTALL_DIR="/opt/cosmic-os"
echo -e "${BLUE}Creating installation directory at $INSTALL_DIR...${NC}"
mkdir -p $INSTALL_DIR
cp -r . $INSTALL_DIR/

# Setup Python environment
echo -e "${BLUE}Setting up Python environment...${NC}"
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run hardware detection and model download
echo -e "${BLUE}Detecting hardware and downloading models...${NC}"
# We'll make sure scripts are executable
chmod +x scripts/*.sh
./scripts/detect-hardware.sh
./scripts/install-models.sh

# Install systemd services
echo -e "${BLUE}Installing systemd services...${NC}"
# Assumes services are in core/system-config/systemd/
cp core/system-config/systemd/*.service /etc/systemd/user/
systemctl --user daemon-reload

# Configure KDE Plasma (User level)
# We need to run this as the actual user, not root, or careful with sudo
echo -e "${BLUE}Configuring KDE Plasma...${NC}"
# This part is tricky as root. We should probably instruct user to run a user-setup script 
# or use `runuser` if we know the user.
# For now, we'll just copy the script and let the user run the config step.

echo -e "${GREEN}Installation complete!${NC}"
echo -e "Please run 'core/system-config/kde-plasma-setup.sh' as your normal user to finish desktop configuration."
echo -e "Then reboot your system."
