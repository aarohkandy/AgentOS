#!/bin/bash
# Test Debian Auto-Install ISO in VirtualBox

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ISO_PATH="$PROJECT_DIR/debian-auto.iso"

VM_NAME="AI-OS-Debian"

echo "========================================"
echo "Testing Debian AI-OS Installer"
echo "========================================"
echo ""

# Check if ISO exists
if [ ! -f "$ISO_PATH" ]; then
    echo "ERROR: ISO file not found at:"
    echo "  $ISO_PATH"
    exit 1
fi

echo "✓ Found ISO: $ISO_PATH"
echo "  Size: $(du -h "$ISO_PATH" | cut -f1)"
echo ""

# Check if VM exists
if VBoxManage showvminfo "$VM_NAME" &>/dev/null; then
    echo "VM '$VM_NAME' exists. Updating ISO..."
    VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium "$ISO_PATH"
else
    echo "Creating new VM '$VM_NAME'..."
    
    # Create VM
    VBoxManage createvm --name "$VM_NAME" --ostype "Debian_64" --register
    
    # Configure VM
    VBoxManage modifyvm "$VM_NAME" \
        --memory 8192 \
        --cpus 6 \
        --vram 128 \
        --graphicscontroller vmsvga \
        --accelerate3d on \
        --boot1 dvd \
        --boot2 disk \
        --boot3 none \
        --boot4 none \
        --nic1 nat
    
    # Create storage controller
    VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide
    VBoxManage storagectl "$VM_NAME" --name "SATA" --add sata --controller IntelAHCI
    
    # Create Disk
    DISK_PATH="$PROJECT_DIR/${VM_NAME}.vdi"
    if [ ! -f "$DISK_PATH" ]; then
        VBoxManage createmedium disk --filename "$DISK_PATH" --size 20000
    fi
    VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$DISK_PATH"
    
    # Attach ISO
    VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium "$ISO_PATH"
    
    echo "✓ VM created successfully"
fi

echo ""
echo "Starting VM..."
# Start in headless mode if in CI, or gui if local
VBoxManage startvm "$VM_NAME" --type gui 2>/dev/null || VBoxManage startvm "$VM_NAME" --type headless

echo ""
echo "VM started! The automated installation will begin."
echo "It will take 10-20 minutes to download and install everything."
echo "When finished, it will reboot into the XFCE desktop."
echo ""
