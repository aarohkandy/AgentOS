#!/bin/bash
# Fast OS testing workflow - one command to reset and test

VM_NAME="AgenticOS"
SNAPSHOT_NAME="Clean Base"

echo "=== Fast OS Testing ==="
echo ""

# Check if snapshot exists
if ! VBoxManage snapshot "$VM_NAME" list 2>/dev/null | grep -q "$SNAPSHOT_NAME"; then
    echo "⚠ No snapshot '$SNAPSHOT_NAME' found!"
    echo ""
    echo "First-time setup:"
    echo "  1. Start VM and install Debian"
    echo "  2. Run vm-post-install.sh inside the VM"
    echo "  3. Create snapshot: ./scripts/vm-snapshot-helper.sh create"
    exit 1
fi

# Power off VM if running
echo "1. Stopping VM..."
VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null || true
sleep 2

# Restore snapshot
echo "2. Restoring clean snapshot..."
VBoxManage snapshot "$VM_NAME" restore "$SNAPSHOT_NAME"

echo ""
echo "✓ VM reset to clean state (took ~5 seconds)"
echo ""
echo "Next steps:"
echo "  1. Start the VM in VirtualBox"
echo "  2. Test your changes"
echo "  3. When done, run this script again to reset"
echo ""
echo "Or start VM headless:"
echo "  VBoxManage startvm '$VM_NAME' --type headless"


