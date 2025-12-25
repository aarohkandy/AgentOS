#!/bin/bash
# Cosmic OS - ISO Builder for VirtualBox
# Creates a bootable ISO with Cosmic OS pre-installed
# Usage: ./build-iso.sh

set -e

# Colors for live output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Progress indicators
PROGRESS_CHARS="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PROGRESS_INDEX=0

# Logging functions with live updates
log_info() { 
    echo -e "${GREEN}[INFO]${NC} $1"
    [ -d "$BUILD_DIR" ] && echo "$(date '+%H:%M:%S') [INFO] $1" >> "$BUILD_LOG" || true
}
log_warn() { 
    echo -e "${YELLOW}[WARN]${NC} $1"
    [ -d "$BUILD_DIR" ] && echo "$(date '+%H:%M:%S') [WARN] $1" >> "$BUILD_LOG" || true
}
log_error() { 
    echo -e "${RED}[ERROR]${NC} $1"
    [ -d "$BUILD_DIR" ] && echo "$(date '+%H:%M:%S') [ERROR] $1" >> "$BUILD_LOG" || true
}
log_step() { 
    echo -e "${BLUE}[STEP]${NC} $1"
    [ -d "$BUILD_DIR" ] && echo "$(date '+%H:%M:%S') [STEP] $1" >> "$BUILD_LOG" || true
}
log_progress() {
    local char="${PROGRESS_CHARS:$PROGRESS_INDEX:1}"
    echo -ne "\r${CYAN}[${char}]${NC} $1"
    PROGRESS_INDEX=$(( (PROGRESS_INDEX + 1) % ${#PROGRESS_CHARS} ))
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/iso-build"
WORK_DIR="$BUILD_DIR/work"
CHROOT_DIR="$BUILD_DIR/chroot"
ISO_OUTPUT="$SCRIPT_DIR/cosmic-os-$(date +%Y%m%d-%H%M%S).iso"
BUILD_LOG="$BUILD_DIR/build.log"

# Create build directory early
mkdir -p "$BUILD_DIR"
echo "Build started at $(date)" > "$BUILD_LOG"
# Kubuntu 24.04.3 LTS ISO URL (latest point release)
UBUNTU_ISO_URL="https://cdimage.ubuntu.com/kubuntu/releases/24.04/release/kubuntu-24.04.3-desktop-amd64.iso"
UBUNTU_ISO_NAME="kubuntu-24.04.3-desktop-amd64.iso"
MIN_DISK_SPACE_GB=20

# Banner
print_banner() {
    clear 2>/dev/null || true
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                    ║"
    echo "║   🌌 COSMIC OS ISO BUILDER                                        ║"
    echo "║   Building bootable ISO for VirtualBox                             ║"
    echo "║                                                                    ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing=()
    
    # Check for required commands (with alternatives)
    for cmd in wget curl xorriso rsync; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    # Check for 7z (p7zip provides 7z or 7za)
    if ! command -v 7z &> /dev/null && ! command -v 7za &> /dev/null; then
        missing+=("7z")
    fi
    
    # Check for genisoimage or mkisofs (cdrtools provides both)
    if ! command -v genisoimage &> /dev/null && ! command -v mkisofs &> /dev/null; then
        missing+=("genisoimage")
    fi
    
    # Note: debootstrap is not needed - we're modifying an existing ISO, not building from scratch
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Installing prerequisites..."
        
        # Check for pacman first (Arch-based systems)
        if command -v pacman &> /dev/null; then
            log_info "Detected Arch Linux - using pacman"
            sudo pacman -Sy --noconfirm
            
            # Install packages available in main repos
            # Note: 7zip (not p7zip) provides 7z command
            # isolinux is part of syslinux package
            log_info "Installing: wget curl 7zip xorriso cdrtools rsync squashfs-tools grub syslinux"
            sudo pacman -S --noconfirm \
                wget curl 7zip xorriso cdrtools rsync \
                squashfs-tools grub syslinux 2>&1 | while IFS= read -r line; do
                    if [[ $line =~ (error|Error|ERROR) ]]; then
                        log_error "$line"
                    fi
                done
            
            # Note: debootstrap not needed for this workflow
            
            # Note: genisoimage and mkisofs are provided by cdrtools
            # Create symlinks if needed (cdrtools provides genisoimage, we can symlink mkisofs)
            if command -v genisoimage &> /dev/null && ! command -v mkisofs &> /dev/null; then
                sudo ln -sf /usr/bin/genisoimage /usr/bin/mkisofs 2>/dev/null || true
            fi
            
            # 7zip provides 7z command, verify it exists
            if ! command -v 7z &> /dev/null && command -v 7za &> /dev/null; then
                # Create symlink if 7za exists but 7z doesn't
                sudo ln -sf /usr/bin/7za /usr/bin/7z 2>/dev/null || true
            fi
            
        elif command -v apt &> /dev/null; then
            log_info "Detected Debian/Ubuntu - using apt"
            sudo apt update
            sudo apt install -y \
                wget curl p7zip-full xorriso genisoimage rsync debootstrap \
                squashfs-tools grub-pc-bin grub-efi-amd64-bin \
                isolinux syslinux-utils
        else
            log_error "Unknown package manager. Please install manually: ${missing[*]}"
            log_error "On Arch: sudo pacman -S wget curl p7zip xorriso cdrtools rsync squashfs-tools grub isolinux syslinux"
            log_error "Then install debootstrap from AUR: yay -S debootstrap"
            exit 1
        fi
        
        # Verify installation and fix PATH issues
        log_info "Verifying installed tools..."
        
        # Refresh PATH to include newly installed binaries
        export PATH="/usr/bin:/usr/local/bin:$PATH"
        hash -r  # Clear command cache
        
        local still_missing=()
        for cmd in wget curl xorriso rsync; do
            if ! command -v "$cmd" &> /dev/null; then
                still_missing+=("$cmd")
            fi
        done
        
        # Check for 7z (7zip package provides 7z command)
        if ! command -v 7z &> /dev/null && ! command -v 7za &> /dev/null; then
            # Check if 7zip package is installed
            if pacman -Q 7zip &>/dev/null; then
                log_info "7zip package installed, checking binary location..."
                # 7zip provides /usr/bin/7z
                if [ -f /usr/bin/7z ]; then
                    log_info "Found 7z at /usr/bin/7z"
                elif [ -f /usr/bin/7za ]; then
                    log_info "Found 7za, creating symlink to 7z..."
                    sudo ln -sf /usr/bin/7za /usr/bin/7z 2>/dev/null || true
                else
                    log_warn "7zip installed but binaries not found in /usr/bin"
                    still_missing+=("7z")
                fi
            else
                still_missing+=("7z")
            fi
        fi
        
        # Check for genisoimage or mkisofs (from cdrtools)
        if ! command -v genisoimage &> /dev/null && ! command -v mkisofs &> /dev/null; then
            # Check if cdrtools package is installed
            if pacman -Q cdrtools &>/dev/null; then
                log_info "cdrtools package installed, checking binary location..."
                # cdrtools provides /usr/bin/genisoimage
                if [ -f /usr/bin/genisoimage ]; then
                    log_info "Found genisoimage at /usr/bin/genisoimage"
                    # Create mkisofs symlink if needed
                    if [ ! -f /usr/bin/mkisofs ]; then
                        sudo ln -sf /usr/bin/genisoimage /usr/bin/mkisofs 2>/dev/null || true
                    fi
                else
                    log_warn "cdrtools installed but genisoimage not found in /usr/bin"
                    still_missing+=("genisoimage")
                fi
            else
                still_missing+=("genisoimage")
            fi
        fi
        
        # Final check after symlinks
        hash -r  # Clear command cache again
        if [ ${#still_missing[@]} -gt 0 ]; then
            log_error "Still missing after installation: ${still_missing[*]}"
            log_error "Please install manually: sudo pacman -S 7zip cdrtools"
            exit 1
        fi
        
        log_info "All prerequisites verified successfully"
    fi
    
    # Check disk space
    local available_gb=$(df -BG "$SCRIPT_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
    if [ "$available_gb" -lt "$MIN_DISK_SPACE_GB" ]; then
        log_error "Insufficient disk space: ${available_gb}GB available, ${MIN_DISK_SPACE_GB}GB required"
        exit 1
    fi
    
    log_info "Prerequisites check passed (${available_gb}GB available)"
}

# Cleanup function
cleanup() {
    if [ -d "$CHROOT_DIR" ] && mountpoint -q "$CHROOT_DIR"; then
        log_info "Unmounting chroot..."
        sudo umount -l "$CHROOT_DIR"/dev/pts 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/dev 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/proc 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/sys 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/run 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Download Ubuntu ISO
download_iso() {
    log_step "Downloading Kubuntu 24.04 ISO..."
    
    local iso_path="$BUILD_DIR/$UBUNTU_ISO_NAME"
    
    # Check if ISO exists and has reasonable size (at least 1GB)
    if [ -f "$iso_path" ]; then
        local size=$(stat -f%z "$iso_path" 2>/dev/null || stat -c%s "$iso_path" 2>/dev/null || echo "0")
        local size_gb=$((size / 1024 / 1024 / 1024))
        if [ "$size_gb" -gt 1 ]; then
            log_info "ISO already exists (${size_gb}GB), skipping download"
            return
        else
            log_warn "ISO file exists but is too small (${size_gb}GB), re-downloading..."
            rm -f "$iso_path"
        fi
    fi
    
    log_info "Downloading from: $UBUNTU_ISO_URL"
    log_warn "This may take a while (4-5GB download)..."
    
    log_info "Starting download (this will take 10-30 minutes depending on connection)..."
    log_info "URL: $UBUNTU_ISO_URL"
    
    # Verify URL exists
    log_info "Verifying URL..."
    if ! curl -s --head "$UBUNTU_ISO_URL" | grep -q "200 OK\|302 Found"; then
        log_error "URL not found (404): $UBUNTU_ISO_URL"
        log_error "Please check: https://cdimage.ubuntu.com/kubuntu/releases/24.04/release/"
        exit 1
    fi
    
    # Use curl if available (better for large files), otherwise wget
    if command -v curl &> /dev/null; then
        log_info "Using curl to download..."
        if curl -L --progress-bar -o "$iso_path.tmp" "$UBUNTU_ISO_URL"; then
            log_info "Download completed"
        else
            log_error "curl download failed"
            rm -f "$iso_path.tmp"
            exit 1
        fi
    else
        log_info "Using wget to download..."
        if wget --progress=bar:force --show-progress -O "$iso_path.tmp" "$UBUNTU_ISO_URL"; then
            log_info "Download completed"
        else
            log_error "wget download failed"
            rm -f "$iso_path.tmp"
            exit 1
        fi
    fi
    
    # Verify download completed successfully
    if [ -f "$iso_path.tmp" ]; then
        local size=$(stat -f%z "$iso_path.tmp" 2>/dev/null || stat -c%s "$iso_path.tmp" 2>/dev/null || echo "0")
        local size_gb=$((size / 1024 / 1024 / 1024))
        local size_mb=$((size / 1024 / 1024))
        if [ "$size_gb" -gt 3 ] || [ "$size_mb" -gt 3000 ]; then
            mv "$iso_path.tmp" "$iso_path"
            log_info "Download verified: ${size_gb}GB (${size_mb}MB)"
        else
            log_error "Downloaded file too small: ${size_mb}MB (expected ~4500MB)"
            log_error "File may be corrupted or download incomplete"
            rm -f "$iso_path.tmp"
            exit 1
        fi
    else
        log_error "Download failed - no file created"
        exit 1
    fi
}

# Extract ISO
extract_iso() {
    log_step "Extracting ISO..."
    
    local iso_path="$BUILD_DIR/$UBUNTU_ISO_NAME"
    local extract_dir="$BUILD_DIR/extracted"
    
    if [ -d "$extract_dir" ]; then
        log_info "ISO already extracted, cleaning..."
        sudo rm -rf "$extract_dir"
    fi
    
    mkdir -p "$extract_dir"
    
    log_info "Mounting ISO..."
    local mount_point="$BUILD_DIR/iso-mount"
    mkdir -p "$mount_point"
    
    # Try to mount first
    if sudo mount -o loop "$iso_path" "$mount_point" 2>/dev/null; then
        log_info "ISO mounted successfully, copying files..."
        sudo cp -r "$mount_point"/* "$extract_dir/" 2>/dev/null || true
        sudo cp -r "$mount_point"/.disk "$extract_dir/" 2>/dev/null || true
        sudo umount "$mount_point" 2>/dev/null || true
        rmdir "$mount_point" 2>/dev/null || true
        log_info "Files copied from mounted ISO"
    else
        log_info "Mount failed, using 7z to extract..."
        log_warn "This may take 5-10 minutes for a 4.5GB ISO..."
        
        # Try 7z first, then 7za
        if command -v 7z &> /dev/null; then
            log_info "Extracting with 7z (this will take a while)..."
            7z x "$iso_path" -o"$extract_dir" -y 2>&1 | \
            while IFS= read -r line; do
                if [[ $line =~ ([0-9]+)% ]]; then
                    local percent="${BASH_REMATCH[1]}"
                    log_progress "Extracting: ${percent}%"
                fi
            done
            echo ""
        elif command -v 7za &> /dev/null; then
            log_info "Extracting with 7za (this will take a while)..."
            7za x "$iso_path" -o"$extract_dir" -y 2>&1 | \
            while IFS= read -r line; do
                if [[ $line =~ ([0-9]+)% ]]; then
                    local percent="${BASH_REMATCH[1]}"
                    log_progress "Extracting: ${percent}%"
                fi
            done
            echo ""
        else
            log_error "Cannot extract ISO: neither mount nor 7z/7za available"
            exit 1
        fi
        
        # Verify extraction worked
        sleep 2  # Give extraction time to complete
        if [ ! -d "$extract_dir/casper" ] && [ ! -d "$extract_dir/boot" ]; then
            log_error "Extraction failed - casper or boot directory not found"
            log_info "Checking what was extracted..."
            ls -la "$extract_dir" | head -10
            
            # Try bsdtar as fallback
            if command -v bsdtar &> /dev/null; then
                log_info "Trying bsdtar..."
                rm -rf "$extract_dir"/*
                bsdtar -xf "$iso_path" -C "$extract_dir" 2>&1
            elif command -v isoinfo &> /dev/null; then
                log_info "Trying isoinfo to list ISO contents..."
                isoinfo -i "$iso_path" -l | head -20
                log_error "Please install fuseiso or use a different extraction method"
                log_error "Or manually mount: sudo mount -o loop $iso_path /mnt && cp -r /mnt/* $extract_dir/"
                exit 1
            else
                log_error "No extraction tools available. Please install:"
                log_error "  sudo pacman -S fuseiso  # or use manual mount method"
                exit 1
            fi
        else
            log_info "Extraction verified - found casper or boot directory"
        fi
    fi
    
    
    # Extract squashfs
    if [ -f "$extract_dir/casper/filesystem.squashfs" ]; then
        log_step "Extracting filesystem..."
        mkdir -p "$CHROOT_DIR"
        
        log_progress "Unsquashing filesystem..."
        sudo unsquashfs -f -d "$CHROOT_DIR" "$extract_dir/casper/filesystem.squashfs" > /dev/null 2>&1
        
        echo ""
        log_info "Filesystem extracted"
    fi
}

# Setup chroot environment
setup_chroot() {
    log_step "Setting up chroot environment..."
    
    # Ensure chroot directory exists
    if [ ! -d "$CHROOT_DIR" ]; then
        log_error "Chroot directory does not exist: $CHROOT_DIR"
        log_error "Extraction must have failed. Please check the extraction step."
        exit 1
    fi
    
    log_info "Creating mount points..."
    sudo mkdir -p "$CHROOT_DIR"/{dev,dev/pts,proc,sys,run}
    
    log_progress "Mounting system directories..."
    sudo mount --bind /dev "$CHROOT_DIR/dev" || log_error "Failed to mount /dev"
    sudo mount --bind /dev/pts "$CHROOT_DIR/dev/pts" || log_error "Failed to mount /dev/pts"
    sudo mount --bind /proc "$CHROOT_DIR/proc" || log_error "Failed to mount /proc"
    sudo mount --bind /sys "$CHROOT_DIR/sys" || log_error "Failed to mount /sys"
    sudo mount --bind /run "$CHROOT_DIR/run" || log_error "Failed to mount /run"
    
    # Copy DNS config
    if [ -f /etc/resolv.conf ]; then
        sudo cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf" 2>/dev/null || true
    fi
    
    echo ""
    log_info "Chroot environment ready"
}

# Install Cosmic OS in chroot
install_cosmic_os() {
    log_step "Installing Cosmic OS in chroot..."
    
    # Copy Cosmic OS files into chroot
    log_info "Copying Cosmic OS files..."
    sudo mkdir -p "$CHROOT_DIR/opt/cosmic-os"
    
    log_progress "Copying core files..."
    sudo cp -r "$SCRIPT_DIR/core" "$CHROOT_DIR/opt/cosmic-os/" 2>&1 | while IFS= read -r line; do
        log_progress "Copying: $line"
    done
    echo ""
    
    log_progress "Copying config files..."
    sudo cp -r "$SCRIPT_DIR/config" "$CHROOT_DIR/opt/cosmic-os/" 2>&1 | while IFS= read -r line; do
        log_progress "Copying: $line"
    done
    echo ""
    
    log_progress "Copying scripts..."
    sudo cp -r "$SCRIPT_DIR/scripts" "$CHROOT_DIR/opt/cosmic-os/" 2>&1 | while IFS= read -r line; do
        log_progress "Copying: $line"
    done
    echo ""
    
    log_progress "Copying documentation..."
    sudo cp -r "$SCRIPT_DIR/docs" "$CHROOT_DIR/opt/cosmic-os/" 2>&1 | while IFS= read -r line; do
        log_progress "Copying: $line"
    done
    echo ""
    
    sudo cp "$SCRIPT_DIR/install.sh" "$CHROOT_DIR/opt/cosmic-os/"
    sudo cp "$SCRIPT_DIR/requirements.txt" "$CHROOT_DIR/opt/cosmic-os/"
    
    log_info "Files copied successfully"
    
    # Create installation script for chroot
    cat > "$BUILD_DIR/chroot-install.sh" << 'CHROOT_SCRIPT'
#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive

echo "🌌 Installing Cosmic OS in chroot..."

# Update system
apt-get update -qq || true

# Install core dependencies (required)
echo "Installing core dependencies..."
apt-get install -y -qq \
    python3 python3-pip python3-venv python3-pyqt6 \
    xdotool wmctrl scrot inotify-tools \
    cmake build-essential git curl wget jq || {
    echo "ERROR: Failed to install core dependencies"
    exit 1
}

# Install optional KDE packages (may not all be available)
echo "Installing optional KDE packages..."
apt-get install -y -qq \
    latte-dock \
    papirus-icon-theme \
    fonts-inter 2>&1 | grep -v "Unable to locate" || true

# Try to install kvantum (may not be available)
apt-get install -y -qq kvantum qt5-style-kvantum 2>&1 | grep -v "Unable to locate" || echo "Note: kvantum not available, skipping"

# Install Python packages
cd /opt/cosmic-os
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Create model directories
mkdir -p /opt/cosmic-os/core/ai_engine/models/{tier1,tier2,tier3,validators}

# Setup systemd service
mkdir -p /root/.config/systemd/user
cat > /root/.config/systemd/user/cosmic-ai.service << 'EOF'
[Unit]
Description=Cosmic OS AI Assistant
After=graphical-session.target

[Service]
Type=simple
ExecStart=/opt/cosmic-os/venv/bin/python3 /opt/cosmic-os/core/ai_engine/main.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=PYTHONPATH=/opt/cosmic-os

[Install]
WantedBy=graphical-session.target
EOF

# Setup autostart
mkdir -p /etc/skel/.config/autostart
cat > /etc/skel/.config/autostart/cosmic-ai.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Cosmic AI
Exec=/opt/cosmic-os/venv/bin/python3 /opt/cosmic-os/core/ai_engine/main.py
Icon=applications-science
Terminal=false
X-KDE-autostart-phase=2
EOF

# Copy to default user template
cp /etc/skel/.config/autostart/cosmic-ai.desktop /root/.config/autostart/ 2>/dev/null || true

# Make scripts executable
chmod +x /opt/cosmic-os/install.sh
chmod +x /opt/cosmic-os/scripts/*.sh
chmod +x /opt/cosmic-os/core/system-config/*.sh

echo "✅ Cosmic OS installed"
CHROOT_SCRIPT

    sudo chmod +x "$BUILD_DIR/chroot-install.sh"
    sudo cp "$BUILD_DIR/chroot-install.sh" "$CHROOT_DIR/root/"
    
    log_info "Running installation in chroot (this may take 10-15 minutes)..."
    log_warn "Installing system packages and Python dependencies..."
    
    # Run installation with live output
    sudo chroot "$CHROOT_DIR" /bin/bash /root/chroot-install.sh 2>&1 | \
    while IFS= read -r line; do
        if [[ $line =~ (Installing|Setting up|Processing|Reading|Unpacking|Selecting) ]]; then
            log_progress "$line"
        elif [[ $line =~ (✅|complete|done|finished) ]]; then
            echo ""
            log_info "$line"
        else
            echo "$line" >> "$BUILD_LOG"
        fi
    done
    
    echo ""
    log_info "Cosmic OS installation complete"
}

# Configure first-boot script
setup_firstboot() {
    log_step "Configuring first-boot setup..."
    
    # Create first-boot script
    cat > "$CHROOT_DIR/opt/cosmic-os/firstboot.sh" << 'FIRSTBOOT'
#!/bin/bash
# Cosmic OS First Boot Setup

# Wait for desktop to be ready
sleep 10

# Run KDE setup
/opt/cosmic-os/core/system-config/kde-plasma-setup.sh <<EOF
y
y
EOF

# Setup keyboard shortcut
kwriteconfig5 --file kglobalshortcutsrc \
    --group "cosmic-ai" \
    --key "_k_friendly_name" "Cosmic AI" 2>/dev/null || true

kwriteconfig5 --file kglobalshortcutsrc \
    --group "cosmic-ai" \
    --key "toggle-sidebar" "Ctrl+Space,Ctrl+Space,Toggle Cosmic AI Sidebar" 2>/dev/null || true

# Start Cosmic AI service
systemctl --user enable cosmic-ai.service 2>/dev/null || true
systemctl --user start cosmic-ai.service 2>/dev/null || true

# Show welcome notification
notify-send "Cosmic OS" "Installation complete! Press Ctrl+Space to open AI sidebar." -t 5000 2>/dev/null || true
FIRSTBOOT

    sudo chmod +x "$CHROOT_DIR/opt/cosmic-os/firstboot.sh"
    
    # Add to autostart
    sudo mkdir -p "$CHROOT_DIR/etc/skel/.config/autostart"
    cat > "$CHROOT_DIR/etc/skel/.config/autostart/cosmic-firstboot.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Cosmic OS First Boot
Exec=/opt/cosmic-os/firstboot.sh
Icon=applications-science
Terminal=false
X-KDE-autostart-phase=1
OnlyShowIn=KDE;
EOF

    log_info "First-boot script configured"
}

# Update ISO files
update_iso_files() {
    log_step "Updating ISO files..."
    
    local extract_dir="$BUILD_DIR/extracted"
    
    # Regenerate manifest
    log_progress "Regenerating manifest..."
    sudo chmod +w "$extract_dir/casper/filesystem.manifest"
    sudo chroot "$CHROOT_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$extract_dir/casper/filesystem.manifest"
    sudo cp "$extract_dir/casper/filesystem.manifest" "$extract_dir/casper/filesystem.manifest-desktop"
    
    # Update filesystem size
    local size=$(sudo du -s "$CHROOT_DIR" | cut -f1)
    echo "$size" | sudo tee "$extract_dir/casper/filesystem.size" > /dev/null
    
    # Remove old squashfs
    sudo rm -f "$extract_dir/casper/filesystem.squashfs"
    
    # Create new squashfs
    log_info "Creating new squashfs (this may take 15-30 minutes)..."
    log_warn "Compressing filesystem with xz compression..."
    
    # Use parallel compression if available
    local compress_opts="-comp xz"
    if command -v mksquashfs &> /dev/null && mksquashfs -help 2>&1 | grep -q "processors"; then
        compress_opts="$compress_opts -processors $(nproc)"
    fi
    
    sudo mksquashfs "$CHROOT_DIR" "$extract_dir/casper/filesystem.squashfs" \
        $compress_opts -e boot/boot* 2>&1 | \
    while IFS= read -r line; do
        if [[ $line =~ Parallel\ mksquashfs ]]; then
            log_info "$line"
        elif [[ $line =~ ([0-9]+)% ]]; then
            local percent="${BASH_REMATCH[1]}"
            log_progress "Compressing filesystem: ${percent}%"
        elif [[ $line =~ (Creating|Writing) ]]; then
            log_progress "$line"
        fi
    done
    
    echo ""
    log_info "ISO files updated"
}

# Calculate MD5 checksums
calculate_checksums() {
    log_step "Calculating checksums..."
    
    local extract_dir="$BUILD_DIR/extracted"
    
    log_progress "Calculating MD5 sums..."
    cd "$extract_dir"
    find . -type f -print0 | xargs -0 md5sum | grep -v "\./md5sum.txt" > md5sum.txt
    cd "$SCRIPT_DIR"
    
    echo ""
    log_info "Checksums calculated"
}

# Build ISO
build_iso() {
    log_step "Building final ISO..."
    
    local extract_dir="$BUILD_DIR/extracted"
    
    log_progress "Creating ISO image..."
    
    # Use xorriso or genisoimage
    if command -v xorriso &> /dev/null; then
        sudo xorriso -as mkisofs \
            -r -V "COSMIC-OS" \
            -cache-inodes -J -l \
            -b isolinux/isolinux.bin \
            -c isolinux/boot.cat \
            -no-emul-boot -boot-load-size 4 -boot-info-table \
            -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot \
            -isohybrid-gpt-basdat \
            -isohybrid-apm-hfsplus \
            -o "$ISO_OUTPUT" \
            "$extract_dir" 2>&1 | \
        while IFS= read -r line; do
            log_progress "Building: $line"
        done
    else
        sudo genisoimage -r -V "COSMIC-OS" \
            -cache-inodes -J -l \
            -b isolinux/isolinux.bin \
            -c isolinux/boot.cat \
            -no-emul-boot -boot-load-size 4 -boot-info-table \
            -o "$ISO_OUTPUT" \
            "$extract_dir" 2>&1 | \
        while IFS= read -r line; do
            log_progress "Building: $line"
        done
    fi
    
    echo ""
    
    # Make ISO bootable
    if command -v isohybrid &> /dev/null; then
        log_progress "Making ISO bootable..."
        sudo isohybrid "$ISO_OUTPUT" 2>/dev/null || true
    fi
    
    echo ""
    log_info "ISO created: $ISO_OUTPUT"
    
    # Show file size
    local size=$(du -h "$ISO_OUTPUT" | cut -f1)
    log_info "ISO size: $size"
}

# Show build summary
show_summary() {
    echo -e "${CYAN}Build Summary:${NC}"
    echo "  • Source: Kubuntu 24.04 LTS"
    echo "  • Output: $ISO_OUTPUT"
    echo "  • Build dir: $BUILD_DIR"
    echo "  • Estimated time: 30-60 minutes"
    echo "  • Disk space needed: ~15GB"
    echo ""
    echo -e "${YELLOW}This will:${NC}"
    echo "  1. Download Kubuntu 24.04 ISO (~4.5GB)"
    echo "  2. Extract and modify the filesystem"
    echo "  3. Install Cosmic OS and dependencies"
    echo "  4. Configure first-boot setup"
    echo "  5. Create bootable ISO"
    echo ""
    read -p "Continue? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "Build cancelled by user"
        exit 0
    fi
}

# Main execution
main() {
    print_banner
    
    show_summary
    
    log_info "Starting ISO build process..."
    log_info "Build directory: $BUILD_DIR"
    log_info "Output ISO: $ISO_OUTPUT"
    echo ""
    
    check_prerequisites
    download_iso
    extract_iso
    setup_chroot
    install_cosmic_os
    setup_firstboot
    update_iso_files
    calculate_checksums
    build_iso
    
    cleanup
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                    ║${NC}"
    echo -e "${GREEN}║   ✅ ISO BUILD COMPLETE!                                         ║${NC}"
    echo -e "${GREEN}║                                                                    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "ISO file: $ISO_OUTPUT"
    log_info "Build log: $BUILD_LOG"
    echo ""
    echo "Next steps:"
    echo "  1. Open VirtualBox"
    echo "  2. Create new VM (Ubuntu 64-bit)"
    echo "  3. Set RAM: 4GB minimum (8GB+ recommended)"
    echo "  4. Set storage: 20GB+"
    echo "  5. Mount ISO: $ISO_OUTPUT"
    echo "  6. Boot and install!"
    echo ""
    echo "After installation, Cosmic OS will be pre-configured and ready to use!"
    echo "Press Ctrl+Space to open the AI sidebar."
    echo ""
}

# Run main
main "$@"

