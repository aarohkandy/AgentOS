#!/bin/bash

# Development Setup Script
# Sets up the environment for developing Cosmic OS

set -e

echo "Setting up development environment..."

# install dev dependencies
sudo apt-get install -y git virtualbox virtualbox-guest-additions-iso

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.sh
chmod +x core/system-config/*.sh

echo "Development environment ready."
echo "Active venv with: source venv/bin/activate"
