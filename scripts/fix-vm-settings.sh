#!/bin/bash
# Fix VM settings to reasonable values

VM_NAME="AgenticOS"
ISO_PATH="/home/aaroh/Downloads/AgentOS/debian-netinst.iso"

echo "Fixing VM settings for $VM_NAME..."
echo ""

# 1. Reduce RAM to 8GB (reasonable for dev VM)
echo "1. Setting RAM to 8GB (was 23GB)..."
VBoxManage modifyvm "$VM_NAME" --memory 8192
echo "   ✓ RAM set to 8GB"

# 2. Attach the ISO
if [ -f "$ISO_PATH" ]; then
    echo ""
    echo "2. Attaching Debian ISO..."
    VBoxManage storageattach "$VM_NAME" \
        --storagectl "IDE" \
        --port 1 \
        --device 0 \
        --type dvddrive \
        --medium "$ISO_PATH"
    echo "   ✓ ISO attached: $ISO_PATH"
else
    echo ""
    echo "2. ⚠ ISO not found at: $ISO_PATH"
    echo "   You'll need to attach it manually in VirtualBox settings"
fi

# 3. Enable hardware acceleration (if KVM is disabled)
echo ""
echo "3. Configuring acceleration..."
VBoxManage modifyvm "$VM_NAME" --paravirtprovider kvm
echo "   ✓ Acceleration configured"

echo ""
echo "=== VM Fixed ==="
echo ""
echo "You can now:"
echo "  1. Start the VM in VirtualBox"
echo "  2. Install Debian"
echo "  3. After installation, create a snapshot:"
echo "     ./scripts/vm-snapshot-helper.sh create"


