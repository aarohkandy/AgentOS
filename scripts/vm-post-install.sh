#!/bin/bash
# Run this INSIDE the VM after Debian is installed
# Sets up everything needed for development

set -e

echo "=== Setting up AI-OS development environment ==="
echo ""

# Update system
echo "1. Updating system..."
sudo apt update
sudo apt upgrade -y

# Install essentials + desktop environment for visual testing
echo ""
echo "2. Installing development tools and desktop environment..."
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    vim \
    build-essential \
    xfce4 \
    xfce4-goodies \
    x11-utils \
    xdotool \
    scrot

# Create dev directory
echo ""
echo "3. Setting up workspace..."
mkdir -p ~/dev
cd ~/dev

# Clone repo (adjust URL as needed)
echo ""
echo "4. Cloning repository..."
if [ ! -d "AgentOS" ]; then
    echo "   Note: You'll need to clone the repo manually or copy it via shared folder"
    echo "   git clone <your-repo-url> AgentOS"
else
    echo "   Repository already exists"
fi

# Set up Python environment
if [ -d "AgentOS" ]; then
    cd AgentOS
    echo ""
    echo "5. Setting up Python environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pip install -e .
    
    echo ""
    echo "6. Running tests..."
    .venv/bin/python -m pytest tests/ -v
    
    echo ""
    echo "✓ Setup complete!"
    echo ""
    echo "Now create a snapshot from the host:"
    echo "  ./scripts/vm-snapshot-helper.sh create"
else
    echo ""
    echo "⚠ Repository not found. Please clone it first."
fi

