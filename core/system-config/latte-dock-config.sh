#!/bin/bash
# Latte Dock Configuration

echo "Setting up Latte Dock..."

# Check if latte-dock is installed
if ! command -v latte-dock &> /dev/null; then
    echo "Latte Dock not found. Skipping."
    exit 0
fi

# Import layout
# latte-dock --import-layout core/system-config/plasma-configs/ios-like.layout.latte

echo "Latte Dock configured."
