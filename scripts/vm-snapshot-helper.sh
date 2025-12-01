#!/bin/bash
# Helper script for managing VirtualBox snapshots for testing

VM_NAME="AgenticOS"
SNAPSHOT_NAME="Clean Base"

case "$1" in
    create)
        echo "Creating snapshot '$SNAPSHOT_NAME' for VM '$VM_NAME'..."
        VBoxManage snapshot "$VM_NAME" take "$SNAPSHOT_NAME" --description "Clean base for testing"
        if [ $? -eq 0 ]; then
            echo "✓ Snapshot created successfully"
        else
            echo "✗ Failed to create snapshot"
            exit 1
        fi
        ;;
    restore)
        echo "Restoring snapshot '$SNAPSHOT_NAME' for VM '$VM_NAME'..."
        VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null
        sleep 2
        VBoxManage snapshot "$VM_NAME" restore "$SNAPSHOT_NAME"
        if [ $? -eq 0 ]; then
            echo "✓ Snapshot restored successfully"
            echo "You can now start the VM"
        else
            echo "✗ Failed to restore snapshot"
            exit 1
        fi
        ;;
    list)
        echo "Snapshots for VM '$VM_NAME':"
        VBoxManage snapshot "$VM_NAME" list
        ;;
    *)
        echo "Usage: $0 {create|restore|list}"
        echo ""
        echo "Commands:"
        echo "  create  - Create a snapshot of current VM state"
        echo "  restore - Restore VM to snapshot (fast reset for testing)"
        echo "  list    - List all snapshots"
        exit 1
        ;;
esac



