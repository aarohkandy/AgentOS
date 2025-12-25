#!/bin/bash
# ANOS Custom Operating System Builder
# Creates a custom ANOS ISO with Ubuntu base, Calamares installer, and Cosmic OS
# Usage: ./build-anos-iso.sh

set -e

# Colors for live output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Progress indicators
PROGRESS_CHARS="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PROGRESS_INDEX=0

# Logging functions
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
BUILD_DIR="$SCRIPT_DIR/anos-build"
CHROOT_DIR="$BUILD_DIR/chroot"
# ISO goes directly in agentOS root, single file that gets overwritten
ISO_OUTPUT="$SCRIPT_DIR/../anos.iso"
BUILD_LOG="$BUILD_DIR/build.log"

# Create build directory early
mkdir -p "$BUILD_DIR"
echo "ANOS build started at $(date)" > "$BUILD_LOG"

# Use Kubuntu 24.04.3 ISO (we know this URL works, we'll strip it down)
# This gives us Ubuntu base + KDE, which we can minimize
UBUNTU_ISO_URL="https://cdimage.ubuntu.com/kubuntu/releases/24.04/release/kubuntu-24.04.3-desktop-amd64.iso"
UBUNTU_ISO_NAME="kubuntu-24.04.3-desktop-amd64.iso"
MIN_DISK_SPACE_GB=20

# Banner
print_banner() {
    clear 2>/dev/null || true
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                    ║"
    echo "║   🚀 ANOS OPERATING SYSTEM BUILDER                                ║"
    echo "║   Custom Linux Distribution with Cosmic OS                          ║"
    echo "║                                                                    ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing=()
    for cmd in wget curl xorriso rsync; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if ! command -v 7z &> /dev/null && ! command -v 7za &> /dev/null; then
        missing+=("7z")
    fi
    
    if ! command -v genisoimage &> /dev/null && ! command -v mkisofs &> /dev/null; then
        missing+=("genisoimage")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Installing prerequisites..."
        
        if command -v pacman &> /dev/null; then
            sudo pacman -Sy --noconfirm
            sudo pacman -S --noconfirm \
                wget curl 7zip xorriso cdrtools rsync \
                squashfs-tools grub syslinux 2>&1 | while IFS= read -r line; do
                    if [[ $line =~ (error|Error|ERROR) ]]; then
                        log_error "$line"
                    fi
                done
        elif command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y \
                wget curl p7zip-full xorriso genisoimage rsync \
                squashfs-tools grub-pc-bin grub-efi-amd64-bin \
                isolinux syslinux-utils
        else
            log_error "Unknown package manager. Please install: ${missing[*]}"
            exit 1
        fi
        
        export PATH="/usr/bin:/usr/local/bin:$PATH"
        hash -r
    fi
    
    local available_gb=$(df -BG "$SCRIPT_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
    if [ "$available_gb" -lt "$MIN_DISK_SPACE_GB" ]; then
        log_error "Insufficient disk space: ${available_gb}GB available, ${MIN_DISK_SPACE_GB}GB required"
        exit 1
    fi
    
    log_info "Prerequisites check passed (${available_gb}GB available)"
}

# Cleanup function
cleanup() {
    if [ -d "$CHROOT_DIR" ] && mountpoint -q "$CHROOT_DIR" 2>/dev/null; then
        log_info "Unmounting chroot..."
        sudo umount -l "$CHROOT_DIR"/dev/pts 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/dev 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/proc 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/sys 2>/dev/null || true
        sudo umount -l "$CHROOT_DIR"/run 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Download Ubuntu server ISO
download_iso() {
    log_step "Downloading Kubuntu 24.04.3 ISO (Ubuntu base)..."
    
    local iso_path="$BUILD_DIR/$UBUNTU_ISO_NAME"
    
    if [ -f "$iso_path" ]; then
        local size=$(stat -f%z "$iso_path" 2>/dev/null || stat -c%s "$iso_path" 2>/dev/null || echo "0")
        local size_gb=$((size / 1024 / 1024 / 1024))
        if [ "$size_gb" -gt 1 ]; then
            log_info "ISO already exists (${size_gb}GB), skipping download"
            return
        else
            log_warn "ISO file exists but is too small, re-downloading..."
            rm -f "$iso_path"
        fi
    fi
    
    log_info "Downloading from: $UBUNTU_ISO_URL"
    
    # Verify URL exists
    log_info "Verifying URL..."
    if ! curl -s --head "$UBUNTU_ISO_URL" | grep -q "200 OK\|302 Found"; then
        log_error "URL not found (404): $UBUNTU_ISO_URL"
        log_error "Please check: https://cdimage.ubuntu.com/ubuntu/releases/24.04/release/"
        exit 1
    fi
    
    log_info "URL is valid, starting download..."
    log_warn "This may take a while (4-5GB download)..."
    
    local download_success=false
    if command -v curl &> /dev/null; then
        if curl -L --progress-bar -o "$iso_path.tmp" "$UBUNTU_ISO_URL"; then
            local size=$(stat -f%z "$iso_path.tmp" 2>/dev/null || stat -c%s "$iso_path.tmp" 2>/dev/null || echo "0")
            local size_mb=$((size / 1024 / 1024))
            if [ "$size" -gt 0 ] && [ "$size_mb" -gt 100 ]; then
                mv "$iso_path.tmp" "$iso_path"
                log_info "Download verified: ${size_mb}MB"
                download_success=true
            else
                log_error "Downloaded file too small (${size_mb}MB, expected >100MB)"
                log_error "File may be corrupted. Checking if partial download exists..."
                if [ -f "$iso_path.tmp" ] && [ "$size_mb" -gt 10 ]; then
                    log_warn "Partial download found. You can resume by running the script again."
                fi
                rm -f "$iso_path.tmp"
            fi
        else
            log_error "Download failed"
        fi
    else
        if wget --progress=bar:force --show-progress -O "$iso_path.tmp" "$UBUNTU_ISO_URL"; then
            local size=$(stat -f%z "$iso_path.tmp" 2>/dev/null || stat -c%s "$iso_path.tmp" 2>/dev/null || echo "0")
            local size_mb=$((size / 1024 / 1024))
            if [ "$size" -gt 0 ] && [ "$size_mb" -gt 100 ]; then
                mv "$iso_path.tmp" "$iso_path"
                log_info "Download verified: ${size_mb}MB"
                download_success=true
            else
                log_error "Downloaded file too small (${size_mb}MB, expected >100MB)"
                rm -f "$iso_path.tmp"
            fi
        else
            log_error "Download failed"
        fi
    fi
    
    if [ "$download_success" = false ]; then
        log_error "Download failed. Please try again or download manually."
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
    
    if sudo mount -o loop "$iso_path" "$mount_point" 2>/dev/null; then
        log_info "ISO mounted, copying files..."
        sudo cp -r "$mount_point"/* "$extract_dir/" 2>/dev/null || true
        sudo cp -r "$mount_point"/.disk "$extract_dir/" 2>/dev/null || true
        sudo umount "$mount_point" 2>/dev/null || true
        rmdir "$mount_point" 2>/dev/null || true
    else
        log_info "Mount failed, using 7z to extract..."
        if command -v 7z &> /dev/null; then
            7z x "$iso_path" -o"$extract_dir" -y > /dev/null 2>&1
        elif command -v 7za &> /dev/null; then
            7za x "$iso_path" -o"$extract_dir" -y > /dev/null 2>&1
        else
            log_error "Cannot extract ISO"
            exit 1
        fi
    fi
    
    # Extract squashfs if it exists
    if [ -f "$extract_dir/casper/filesystem.squashfs" ]; then
        log_step "Extracting filesystem..."
        mkdir -p "$CHROOT_DIR"
        sudo unsquashfs -f -d "$CHROOT_DIR" "$extract_dir/casper/filesystem.squashfs" > /dev/null 2>&1
        log_info "Filesystem extracted"
    elif [ -f "$extract_dir/install/filesystem.squashfs" ]; then
        log_step "Extracting filesystem..."
        mkdir -p "$CHROOT_DIR"
        sudo unsquashfs -f -d "$CHROOT_DIR" "$extract_dir/install/filesystem.squashfs" > /dev/null 2>&1
        log_info "Filesystem extracted"
    else
        log_error "No filesystem.squashfs found in ISO"
        exit 1
    fi
}

# Setup chroot
setup_chroot() {
    log_step "Setting up chroot environment..."
    
    if [ ! -d "$CHROOT_DIR" ]; then
        log_error "Chroot directory does not exist"
        exit 1
    fi
    
    sudo mkdir -p "$CHROOT_DIR"/{dev,dev/pts,proc,sys,run}
    sudo mount --bind /dev "$CHROOT_DIR/dev" || log_error "Failed to mount /dev"
    sudo mount --bind /dev/pts "$CHROOT_DIR/dev/pts" || log_error "Failed to mount /dev/pts"
    sudo mount --bind /proc "$CHROOT_DIR/proc" || log_error "Failed to mount /proc"
    sudo mount --bind /sys "$CHROOT_DIR/sys" || log_error "Failed to mount /sys"
    sudo mount --bind /run "$CHROOT_DIR/run" || log_error "Failed to mount /run"
    
    if [ -f /etc/resolv.conf ]; then
        sudo cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf" 2>/dev/null || true
    fi
    
    log_info "Chroot environment ready"
}

# Install minimal packages and Cosmic OS
install_system() {
    log_step "Installing ANOS system packages..."
    
    # Copy Cosmic OS files
    log_info "Copying Cosmic OS files..."
    sudo mkdir -p "$CHROOT_DIR/opt/cosmic-os"
    if [ -d "$SCRIPT_DIR/../core" ]; then
        sudo cp -r "$SCRIPT_DIR/../core" "$CHROOT_DIR/opt/cosmic-os/" 2>/dev/null || true
        sudo cp -r "$SCRIPT_DIR/../config" "$CHROOT_DIR/opt/cosmic-os/" 2>/dev/null || true
        sudo cp -r "$SCRIPT_DIR/../scripts" "$CHROOT_DIR/opt/cosmic-os/" 2>/dev/null || true
        sudo cp -r "$SCRIPT_DIR/../docs" "$CHROOT_DIR/opt/cosmic-os/" 2>/dev/null || true
        sudo cp "$SCRIPT_DIR/../install.sh" "$CHROOT_DIR/opt/cosmic-os/" 2>/dev/null || true
        sudo cp "$SCRIPT_DIR/../requirements.txt" "$CHROOT_DIR/opt/cosmic-os/" 2>/dev/null || true
    fi
    
    # Copy installation scripts to chroot
    sudo mkdir -p "$CHROOT_DIR/root"
    sudo cp "$SCRIPT_DIR/cosmic-integration/install-anos.sh" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/cosmic-integration/install-cosmic.sh" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/cosmic-integration/configure-kde.sh" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/packages/base.list" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/packages/remove.list" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/branding/apply-branding.sh" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/branding/system/os-release" "$CHROOT_DIR/root/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/branding/system/issue" "$CHROOT_DIR/root/" 2>/dev/null || true
    
    # Make scripts executable
    sudo chmod +x "$CHROOT_DIR/root/"*.sh 2>/dev/null || true
    
    # Run system installation in chroot
    log_info "Running system installation (this may take 15-20 minutes)..."
    sudo chroot "$CHROOT_DIR" /bin/bash /root/install-anos.sh 2>&1 | \
    while IFS= read -r line; do
        if [[ $line =~ ([0-9]+)% ]]; then
            log_progress "$line"
        elif [[ $line =~ (ERROR|WARN|Installing|Complete) ]]; then
            echo ""
            log_info "$line"
        fi
    done
    
    echo ""
    log_info "System installation complete"
}

# Apply branding
apply_branding() {
    log_step "Applying ANOS branding..."
    
    # Create assets directory
    sudo mkdir -p "$CHROOT_DIR/usr/share/anos"
    if [ -d "$SCRIPT_DIR/assets" ]; then
        sudo cp -r "$SCRIPT_DIR/assets/"* "$CHROOT_DIR/usr/share/anos/" 2>/dev/null || true
    fi
    
    # Branding is already applied in install-anos.sh, but ensure it's done
    log_info "Branding applied"
}

# Configure Calamares
configure_calamares() {
    log_step "Configuring Calamares installer..."
    
    # Copy Calamares configuration
    sudo mkdir -p "$CHROOT_DIR/etc/calamares"
    sudo mkdir -p "$CHROOT_DIR/usr/share/calamares"
    if [ -d "$SCRIPT_DIR/installer/calamares" ]; then
        sudo cp -r "$SCRIPT_DIR/installer/calamares/"* "$CHROOT_DIR/etc/calamares/" 2>/dev/null || true
        sudo cp -r "$SCRIPT_DIR/installer/calamares/branding" "$CHROOT_DIR/usr/share/calamares/" 2>/dev/null || true
    fi
    
    log_info "Calamares configured"
}

# Update ISO files
update_iso_files() {
    log_step "Updating ISO files..."
    
    local extract_dir="$BUILD_DIR/extracted"
    
    # Regenerate manifest
    sudo chmod +w "$extract_dir/casper/filesystem.manifest" 2>/dev/null || true
    sudo chroot "$CHROOT_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$extract_dir/casper/filesystem.manifest" 2>/dev/null || \
    sudo chroot "$CHROOT_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$extract_dir/install/filesystem.manifest" 2>/dev/null || true
    
    # Update filesystem size
    local size=$(sudo du -s "$CHROOT_DIR" | cut -f1)
    echo "$size" | sudo tee "$extract_dir/casper/filesystem.size" > /dev/null 2>/dev/null || \
    echo "$size" | sudo tee "$extract_dir/install/filesystem.size" > /dev/null 2>/dev/null || true
    
    # Remove old squashfs
    sudo rm -f "$extract_dir/casper/filesystem.squashfs" "$extract_dir/install/filesystem.squashfs" 2>/dev/null || true
    
    # Create new squashfs
    log_info "Creating new squashfs (no compression for maximum speed)..."
    log_warn "Using no compression - fastest possible (30 seconds - 2 minutes)..."
    local squashfs_path="$extract_dir/casper/filesystem.squashfs"
    [ ! -f "$squashfs_path" ] && squashfs_path="$extract_dir/install/filesystem.squashfs"
    
    # No compression = fastest possible (file will be larger but builds in seconds)
    # Also use parallel processing if available
    local compress_opts="-no-compression"
    if mksquashfs -help 2>&1 | grep -q "processors"; then
        compress_opts="$compress_opts -processors $(nproc)"
    fi
    
    sudo mksquashfs "$CHROOT_DIR" "$squashfs_path" \
        $compress_opts -e boot/boot* -progress 2>&1 | \
    while IFS= read -r line; do
        if [[ $line =~ ([0-9]+)% ]]; then
            local percent="${BASH_REMATCH[1]}"
            log_progress "Compressing: ${percent}%"
        elif [[ $line =~ (Creating|Writing|Parallel) ]]; then
            log_progress "$line"
        fi
    done
    
    echo ""
    log_info "ISO files updated"
}

# Calculate checksums
calculate_checksums() {
    log_step "Calculating checksums..."
    local extract_dir="$BUILD_DIR/extracted"
    cd "$extract_dir"
    find . -type f -print0 | xargs -0 md5sum | grep -v "\./md5sum.txt" > md5sum.txt 2>/dev/null || true
    cd "$SCRIPT_DIR"
    log_info "Checksums calculated"
}

# Build ISO
build_iso() {
    log_step "Building final ANOS ISO..."
    
    local extract_dir="$BUILD_DIR/extracted"
    
    log_info "Creating ISO image..."
    
    if command -v xorriso &> /dev/null; then
        sudo xorriso -as mkisofs \
            -r -V "ANOS" \
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
        sudo genisoimage -r -V "ANOS" \
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
    
    if command -v isohybrid &> /dev/null; then
        sudo isohybrid "$ISO_OUTPUT" 2>/dev/null || true
    fi
    
    local size=$(du -h "$ISO_OUTPUT" | cut -f1)
    log_info "ANOS ISO created: $ISO_OUTPUT (${size})"
}

# Main execution
main() {
    print_banner
    
    log_info "Starting ANOS build process..."
    log_info "Build directory: $BUILD_DIR"
    log_info "Output ISO: $ISO_OUTPUT"
    echo ""
    
    check_prerequisites
    download_iso
    extract_iso
    setup_chroot
    install_system
    apply_branding
    configure_calamares
    update_iso_files
    calculate_checksums
    build_iso
    
    cleanup
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                    ║${NC}"
    echo -e "${GREEN}║   ✅ ANOS ISO BUILD COMPLETE!                                    ║${NC}"
    echo -e "${GREEN}║                                                                    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "ISO file: $ISO_OUTPUT"
    echo ""
}

main "$@"



