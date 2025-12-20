#!/bin/bash
# Cosmic OS Theme Setup
# Installs WhiteSur Dark theme for iOS-like aesthetic

set -e

echo "╔══════════════════════════════════════════╗"
echo "║      Cosmic OS Theme Setup               ║"
echo "╚══════════════════════════════════════════╝"

# Check for git
if ! command -v git &> /dev/null; then
    echo "GiT not found. Installing..."
    sudo apt install -y git
fi

THEME_DIR="$HOME/.local/share/themes"
ICON_DIR="$HOME/.local/share/icons"
mkdir -p "$THEME_DIR" "$ICON_DIR"

echo "▶ Downloading WhiteSur KDE Theme..."
# We clone to /tmp to avoid clutter
git clone https://github.com/vinceliuice/WhiteSur-kde.git /tmp/whitesur-kde

echo "▶ Installing WhiteSur Theme..."
cd /tmp/whitesur-kde
./install.sh --dark --round --opacity normal

echo ""
echo "▶ Downloading WhiteSur Icon Theme..."
git clone https://github.com/vinceliuice/WhiteSur-icon-theme.git /tmp/whitesur-icon-theme
cd /tmp/whitesur-icon-theme
./install.sh -b

echo ""
echo "▶ Setting Wallpaper..."
# Download a nice default wallpaper
WALLPAPER_DIR="$HOME/.local/share/wallpapers/CosmicOS/"
mkdir -p "$WALLPAPER_DIR"
wget -O "$WALLPAPER_DIR/default.jpg" "https://images.unsplash.com/photo-1635776062127-d379bfcba9f8?q=80&w=3832&auto=format&fit=crop"

# Apply Wallpaper
if command -v plasma-apply-wallpaperimage &> /dev/null; then
    plasma-apply-wallpaperimage "$WALLPAPER_DIR/default.jpg"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      Theme Setup Complete!               ║"
echo "╚══════════════════════════════════════════╝"
echo "Please restart your session."
