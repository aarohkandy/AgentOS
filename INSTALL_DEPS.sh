#!/bin/bash
# Install all dependencies for iOS-quality experience

set -e

echo "Installing Cosmic OS dependencies..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install dependencies
echo "Installing Python packages..."
pip3 install --user PyQt6 psutil requests dbus-python python-xlib Pillow aiohttp python-dotenv pydantic

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Verify with: python3 verify_ios_quality.py"
echo "Start with: ./start_cosmic.sh"




