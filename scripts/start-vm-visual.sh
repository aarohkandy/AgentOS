#!/bin/bash
# Start VM for visual/interactive testing

VM_NAME="AgenticOS"

echo "=== Starting VM for Visual Testing ==="
echo ""

# Check if VM exists
if ! VBoxManage showvminfo "$VM_NAME" &>/dev/null; then
    echo "✗ VM '$VM_NAME' not found!"
    echo "Run: ./scripts/setup-vm-fast.sh"
    exit 1
fi

# Check if VM is running
if VBoxManage showvminfo "$VM_NAME" --machinereadable | grep -q 'VMState="running"'; then
    echo "VM is already running"
    echo "Open VirtualBox to see it"
else
    echo "Starting VM..."
    VBoxManage startvm "$VM_NAME" --type gui
    
    echo ""
    echo "✓ VM starting..."
    echo ""
    echo "The VM window will open - you can now:"
    echo "  - See the OS desktop"
    echo "  - Interact with the UI"
    echo "  - Test your AI agent visually"
    echo "  - See screen capture in action"
    echo ""
    echo "To stop: Close VM window or run:"
    echo "  VBoxManage controlvm $VM_NAME poweroff"
fi


