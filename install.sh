#!/bin/bash
# Cosmic OS - One-Click Installation Script
# Run with: sudo ./install.sh

set -e

echo "
╔═══════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   🌌 COSMIC OS INSTALLER                                          ║
║   AI-Integrated Desktop Experience                                 ║
║                                                                    ║
╚═══════════════════════════════════════════════════════════════════╝
"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check if running as root for system-wide install
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/opt/cosmic-os"
    SYSTEM_INSTALL=true
else
    INSTALL_DIR="$HOME/.local/share/cosmic-os"
    SYSTEM_INSTALL=false
    log_warn "Running without sudo - installing to user directory"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Ubuntu version
check_ubuntu() {
    log_step "Checking system requirements..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID" != "kubuntu" ]]; then
            log_warn "This installer is designed for Ubuntu/Kubuntu"
            log_warn "Detected: $NAME $VERSION_ID"
            read -p "Continue anyway? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    log_info "System check passed"
}

# Check hardware requirements
check_hardware() {
    log_step "Checking hardware..."
    
    # Check RAM
    RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    RAM_GB=$((RAM_KB / 1024 / 1024))
    
    if [ "$RAM_GB" -lt 4 ]; then
        log_error "Insufficient RAM: ${RAM_GB}GB detected, 4GB minimum required"
        exit 1
    fi
    
    # Determine tier
    if [ "$RAM_GB" -ge 16 ]; then
        TIER=3
    elif [ "$RAM_GB" -ge 8 ]; then
        TIER=2
    else
        TIER=1
    fi
    
    # Check for GPU
    if command -v nvidia-smi &> /dev/null; then
        TIER=3
        log_info "NVIDIA GPU detected"
    fi
    
    log_info "RAM: ${RAM_GB}GB - Recommended Tier: $TIER"
    
    # Check disk space
    AVAILABLE_GB=$(df -BG "$HOME" | awk 'NR==2 {print $4}' | tr -d 'G')
    REQUIRED_GB=$((TIER * 5 + 3))
    
    if [ "$AVAILABLE_GB" -lt "$REQUIRED_GB" ]; then
        log_error "Insufficient disk space: ${AVAILABLE_GB}GB available, ${REQUIRED_GB}GB required"
        exit 1
    fi
    
    log_info "Disk space: ${AVAILABLE_GB}GB available"
}

# Install system dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    if [ "$SYSTEM_INSTALL" = true ]; then
        apt update
        apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-pyqt6 \
            xdotool \
            wmctrl \
            scrot \
            inotify-tools \
            cmake \
            build-essential \
            git \
            curl \
            wget \
            jq
    else
        log_warn "Installing user-level dependencies only"
        log_warn "You may need to manually install: xdotool wmctrl scrot"
    fi
    
    log_info "System dependencies installed"
}

# Install KDE Plasma if needed
install_kde() {
    log_step "Checking for KDE Plasma..."
    
    if [ "$XDG_CURRENT_DESKTOP" = "KDE" ]; then
        log_info "KDE Plasma detected"
    else
        log_warn "KDE Plasma not detected"
        read -p "Install KDE Plasma? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            if [ "$SYSTEM_INSTALL" = true ]; then
                apt install -y kubuntu-desktop
                log_info "KDE Plasma installed - please reboot and select Plasma at login"
            else
                log_error "Cannot install KDE without sudo"
                exit 1
            fi
        fi
    fi
}

# Install Python packages
install_python_packages() {
    log_step "Installing Python packages..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
    
    log_info "Python packages installed"
}

# Copy files
install_files() {
    log_step "Installing Cosmic OS files..."
    
    mkdir -p "$INSTALL_DIR"
    
    # Copy core files
    cp -r "$SCRIPT_DIR/core" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/config" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/docs" "$INSTALL_DIR/"
    
    # Create model directories
    mkdir -p "$INSTALL_DIR/core/ai_engine/models"/{tier1,tier2,tier3,validators}
    touch "$INSTALL_DIR/core/ai_engine/models/.gitkeep"
    
    # Create log directory
    mkdir -p "$HOME/.local/share/cosmic-os/logs"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    chmod +x "$INSTALL_DIR/scripts/"*.py
    chmod +x "$INSTALL_DIR/core/system-config/"*.sh
    
    log_info "Files installed to $INSTALL_DIR"
}

# Setup systemd service
setup_service() {
    log_step "Setting up systemd service..."
    
    mkdir -p "$HOME/.config/systemd/user"
    
    cat > "$HOME/.config/systemd/user/cosmic-ai.service" << EOF
[Unit]
Description=Cosmic OS AI Assistant
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/core/ai_engine/main.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=PYTHONPATH=$INSTALL_DIR

[Install]
WantedBy=graphical-session.target
EOF
    
    systemctl --user daemon-reload
    systemctl --user enable cosmic-ai.service
    
    log_info "Systemd service configured"
}

# Setup autostart
setup_autostart() {
    log_step "Setting up autostart..."
    
    mkdir -p "$HOME/.config/autostart"
    
    cat > "$HOME/.config/autostart/cosmic-ai.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Cosmic AI
Exec=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/core/ai_engine/main.py
Icon=applications-science
Terminal=false
X-KDE-autostart-phase=2
EOF
    
    log_info "Autostart configured"
}

# Setup keyboard shortcut
setup_hotkey() {
    log_step "Setting up Super+Shift hotkey..."
    
    if command -v kwriteconfig5 &> /dev/null; then
        kwriteconfig5 --file kglobalshortcutsrc \
            --group "cosmic-ai" \
            --key "_k_friendly_name" "Cosmic AI"
        
        kwriteconfig5 --file kglobalshortcutsrc \
            --group "cosmic-ai" \
            --key "toggle-sidebar" "Super+Shift,Super+Shift,Toggle Cosmic AI Sidebar"
        
        log_info "Hotkey configured"
    else
        log_warn "kwriteconfig5 not found - please configure hotkey manually"
    fi
}

# Download AI models
download_models() {
    log_step "AI Model Setup"
    
    echo ""
    echo "Cosmic OS needs AI models to function."
    echo "Recommended tier based on your hardware: $TIER"
    echo ""
    echo "1) Download Tier $TIER models now (~$((TIER * 3))GB)"
    echo "2) Skip - I'll download later"
    echo ""
    read -p "Choice [1-2]: " -n 1 -r
    echo
    
    if [[ $REPLY == "1" ]]; then
        source "$INSTALL_DIR/venv/bin/activate"
        "$INSTALL_DIR/scripts/install-models.sh" --tier "$TIER"
    else
        log_warn "Skipped model download"
        log_warn "Run ./scripts/install-models.sh later to download models"
    fi
}

# Apply KDE customizations
apply_kde_config() {
    log_step "KDE Customization"
    
    read -p "Apply iOS-like KDE theme? [Y/n] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        "$INSTALL_DIR/core/system-config/kde-plasma-setup.sh"
        "$INSTALL_DIR/core/system-config/latte-dock-config.sh"
        "$INSTALL_DIR/core/system-config/theme-setup.sh"
    else
        log_info "Skipped KDE customization"
    fi
}

# Print completion message
print_complete() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                    ║"
    echo "║   ✅ COSMIC OS INSTALLATION COMPLETE!                             ║"
    echo "║                                                                    ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Detected tier: $TIER"
    echo ""
    echo "Next steps:"
    echo "  1. Log out and log back in (or reboot)"
    echo "  2. Press Super+Shift (Windows+Shift) to open the AI sidebar"
    echo "  3. Try: 'Open Firefox'"
    echo ""
    echo "Useful commands:"
    echo "  systemctl --user start cosmic-ai   # Start AI daemon"
    echo "  systemctl --user status cosmic-ai  # Check status"
    echo "  journalctl --user -u cosmic-ai -f  # View logs"
    echo ""
    echo "Documentation: $INSTALL_DIR/docs/"
    echo ""
}

# Offer reboot
offer_reboot() {
    read -p "Reboot now to complete setup? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
}

# Main installation flow
main() {
    check_ubuntu
    check_hardware
    install_dependencies
    install_kde
    install_files
    install_python_packages
    setup_service
    setup_autostart
    setup_hotkey
    download_models
    apply_kde_config
    print_complete
    offer_reboot
}

# Run with error handling
if main; then
    exit 0
else
    log_error "Installation failed. Check the output above for errors."
    exit 1
fi
