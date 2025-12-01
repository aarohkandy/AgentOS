#!/bin/bash
# Test Custom AI-OS in VirtualBox

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ISO_PATH="$PROJECT_DIR/buildroot/output/images/rootfs.iso9660"

VM_NAME="AI-OS-Custom"

echo "========================================"
echo "Testing Custom AI-OS"
echo "========================================"
echo ""

# Check if ISO exists
if [ ! -f "$ISO_PATH" ]; then
    echo "ERROR: ISO file not found at:"
    echo "  $ISO_PATH"
    echo ""
    echo "Please build the OS first:"
    echo "  ./scripts/build-custom-os.sh"
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
    VBoxManage createvm --name "$VM_NAME" --ostype "Linux_64" --register
    
    # Configure VM
    VBoxManage modifyvm "$VM_NAME" \
        --memory 512 \
        --cpus 2 \
        --vram 16 \
        --boot1 dvd \
        --boot2 disk \
        --boot3 none \
        --boot4 none
    
    # Create storage controller
    VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide
    
    # Attach ISO
    VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium "$ISO_PATH"
    
    echo "✓ VM created successfully"
fi

echo ""
echo "Starting VM..."
VBoxManage startvm "$VM_NAME" --type gui

echo ""
echo "VM started! You should see:"
echo "  - Fast boot (1-3 seconds)"
echo "  - No installation prompts"
echo "  - Auto-login to shell"
echo "  - AI Agent welcome message"
echo "  - AI Agent demo running"
echo ""
