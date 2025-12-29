#!/bin/bash
# Cosmic OS - VirtualBox VM Setup Script
# Run this inside the Ubuntu/Kubuntu VM to configure for development

set -e

echo "🖥️ Cosmic OS - VM Development Setup"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running in VM
check_vm() {
    if ! grep -qi "virtualbox\|vmware\|kvm\|qemu" /sys/class/dmi/id/product_name 2>/dev/null; then
        log_warn "This script is designed for VirtualBox VMs"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Install VirtualBox Guest Additions
install_guest_additions() {
    log_info "Installing VirtualBox Guest Additions..."
    
    sudo apt update
    sudo apt install -y \
        virtualbox-guest-utils \
        virtualbox-guest-x11 \
        dkms \
        linux-headers-$(uname -r)
    
    # Add user to vboxsf group for shared folders
    sudo usermod -aG vboxsf "$USER"
    
    log_info "Guest Additions installed"
}

# Setup shared folder mount
setup_shared_folder() {
    log_info "Setting up shared folder..."
    
    MOUNT_POINT="/mnt/cosmic-os"
    SHARE_NAME="cosmic-os"
    
    # Create mount point
    sudo mkdir -p "$MOUNT_POINT"
    
    # Add to fstab for persistent mount
    if ! grep -q "$SHARE_NAME" /etc/fstab; then
        echo "$SHARE_NAME    $MOUNT_POINT    vboxsf    defaults,uid=1000,gid=1000,dmode=775,fmode=664    0    0" | sudo tee -a /etc/fstab
    fi
    
    # Mount now
    sudo mount -a 2>/dev/null || log_warn "Mount failed - ensure shared folder '$SHARE_NAME' is configured in VirtualBox"
    
    if mountpoint -q "$MOUNT_POINT"; then
        log_info "Shared folder mounted at $MOUNT_POINT"
    else
        log_warn "Shared folder not mounted. Configure in VirtualBox: Settings > Shared Folders"
        log_warn "Create folder named '$SHARE_NAME' pointing to your cosmic-os repo"
    fi
}

# Install development dependencies
install_dependencies() {
    log_info "Installing development dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-pyqt6 \
        xdotool \
        wmctrl \
        scrot \
        inotify-tools \
        git \
        curl \
        wget \
        jq \
        build-essential \
        cmake \
        ninja-build
    
    # Install Python packages
    pip3 install --user \
        llama-cpp-python \
        dbus-python \
        python-xlib \
        Pillow \
        psutil \
        requests \
        aiohttp \
        python-dotenv \
        pydantic
    
    log_info "Dependencies installed"
}

# Configure systemd services
setup_services() {
    log_info "Setting up systemd services..."
    
    MOUNT_POINT="/mnt/cosmic-os"
    
    # Copy service files
    mkdir -p "$HOME/.config/systemd/user"
    
    if [ -f "$MOUNT_POINT/core/system-config/systemd/cosmic-ai.service" ]; then
        cp "$MOUNT_POINT/core/system-config/systemd/cosmic-ai.service" "$HOME/.config/systemd/user/"
        
        # Adjust paths for VM
        sed -i "s|/opt/cosmic-os|$MOUNT_POINT|g" "$HOME/.config/systemd/user/cosmic-ai.service"
        
        systemctl --user daemon-reload
        log_info "cosmic-ai.service installed"
    fi
    
    if [ -f "$MOUNT_POINT/core/system-config/systemd/cosmic-hotreload.service" ]; then
        cp "$MOUNT_POINT/core/system-config/systemd/cosmic-hotreload.service" "$HOME/.config/systemd/user/"
        
        sed -i "s|/opt/cosmic-os|$MOUNT_POINT|g" "$HOME/.config/systemd/user/cosmic-hotreload.service"
        
        systemctl --user daemon-reload
        log_info "cosmic-hotreload.service installed"
    fi
}

# Setup hot-reload file watcher
setup_hot_reload() {
    log_info "Setting up hot-reload system..."
    
    MOUNT_POINT="/mnt/cosmic-os"
    
    # Create the file watcher script
    mkdir -p "$HOME/.local/bin"
    
    cat > "$HOME/.local/bin/cosmic-hotreload" << 'EOF'
#!/bin/bash
# Cosmic OS Hot-Reload File Watcher

WATCH_DIR="${COSMIC_WATCH_DIR:-/mnt/cosmic-os}"

echo "👀 Watching $WATCH_DIR for changes..."

inotifywait -m -r -e modify,create,delete --format '%w%f %e' "$WATCH_DIR/core/" |
while read file event; do
    echo "[$(date +%H:%M:%S)] Change detected: $file ($event)"
    
    # Skip temp files
    if [[ "$file" == *".swp" ]] || [[ "$file" == *"~" ]] || [[ "$file" == *".pyc" ]]; then
        continue
    fi
    
    # Restart AI daemon
    if systemctl --user is-active cosmic-ai.service &>/dev/null; then
        echo "Restarting cosmic-ai service..."
        systemctl --user restart cosmic-ai.service
    fi
    
    # Send notification
    notify-send "Cosmic OS" "Code reloaded: $(basename $file)" -t 2000 2>/dev/null || true
    
    echo "✅ Reload complete"
done
EOF
    
    chmod +x "$HOME/.local/bin/cosmic-hotreload"
    
    log_info "Hot-reload script installed to ~/.local/bin/cosmic-hotreload"
}

# Configure KDE shortcuts
setup_shortcuts() {
    log_info "Setting up keyboard shortcuts..."
    
    MOUNT_POINT="/mnt/cosmic-os"
    
    # Add Super+Shift shortcut for sidebar
    kwriteconfig5 --file kglobalshortcutsrc \
        --group "cosmic-ai" \
        --key "_k_friendly_name" "Cosmic AI"
    
    kwriteconfig5 --file kglobalshortcutsrc \
        --group "cosmic-ai" \
        --key "toggle-sidebar" "Meta+Shift,Meta+Shift,Toggle Cosmic AI Sidebar"
    
    # Create desktop entry for the sidebar
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$HOME/.local/share/applications/cosmic-ai-sidebar.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Cosmic AI Sidebar
Comment=Toggle the Cosmic AI sidebar
Exec=python3 $MOUNT_POINT/core/gui/sidebar.py
Icon=applications-science
Terminal=false
Categories=Utility;
EOF
    
    log_info "Shortcuts configured"
}

# Create development conveniences
setup_dev_helpers() {
    log_info "Setting up development helpers..."
    
    MOUNT_POINT="/mnt/cosmic-os"
    
    # Add aliases to bashrc
    if ! grep -q "cosmic-os aliases" "$HOME/.bashrc"; then
        cat >> "$HOME/.bashrc" << EOF

# Cosmic OS development aliases
alias cosmic-reload='systemctl --user restart cosmic-ai.service'
alias cosmic-logs='journalctl --user -u cosmic-ai.service -f'
alias cosmic-status='systemctl --user status cosmic-ai.service'
alias cosmic-test='python3 $MOUNT_POINT/scripts/test-ai.py'
alias cosmic-watch='$HOME/.local/bin/cosmic-hotreload'
alias cosmic-dir='cd $MOUNT_POINT'
EOF
    fi
    
    log_info "Development aliases added to ~/.bashrc"
}

# Run quick test
run_test() {
    log_info "Running quick test..."
    
    MOUNT_POINT="/mnt/cosmic-os"
    
    if [ -f "$MOUNT_POINT/scripts/test-ai.py" ]; then
        python3 "$MOUNT_POINT/scripts/test-ai.py" --quick
    else
        log_warn "Test script not found"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "============================================"
    echo -e "${GREEN}✅ VM Development Setup Complete!${NC}"
    echo "============================================"
    echo ""
    echo "Next steps:"
    echo "1. Reboot the VM to apply all changes"
    echo "2. Configure VirtualBox shared folder named 'cosmic-os'"
    echo "3. Run: source ~/.bashrc"
    echo "4. Start hot-reload: cosmic-watch"
    echo "5. Test: cosmic-test"
    echo ""
    echo "Useful commands:"
    echo "  cosmic-reload  - Restart AI daemon"
    echo "  cosmic-logs    - View AI daemon logs"
    echo "  cosmic-status  - Check AI daemon status"
    echo "  cosmic-watch   - Start file watcher"
    echo "  cosmic-test    - Run quick test"
    echo ""
}

# Main
main() {
    check_vm
    install_guest_additions
    setup_shared_folder
    install_dependencies
    setup_services
    setup_hot_reload
    setup_shortcuts
    setup_dev_helpers
    print_summary
    
    read -p "Run quick test? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        run_test
    fi
    
    read -p "Reboot now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
}

main "$@"
