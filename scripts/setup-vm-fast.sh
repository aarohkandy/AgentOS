#!/bin/bash
# Fast VM setup - automates everything possible

set -e

VM_NAME="AgenticOS"
ISO_PATH="/home/aaroh/Downloads/AgentOS/debian-netinst.iso"
SNAPSHOT_NAME="Clean Base"

echo "=== Fast VM Setup ==="
echo ""

# Check if VM exists
if ! VBoxManage showvminfo "$VM_NAME" &>/dev/null; then
    echo "Creating VM '$VM_NAME'..."
    
    # Create VM with optimal settings
    VBoxManage createvm --name "$VM_NAME" --ostype "Debian_64" --register
    
    # Set reasonable resources
    VBoxManage modifyvm "$VM_NAME" --memory 4096 --cpus 2
    VBoxManage modifyvm "$VM_NAME" --boot1 dvd --boot2 disk --boot3 none --boot4 none
    
    # Create disk (20GB)
    VBoxManage createhd --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" --size 20480
    
    # Attach storage
    VBoxManage storagectl "$VM_NAME" --name "SATA" --add sata --controller IntelAHCI
    VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi"
    
    # Attach ISO
    VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide
    VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium "$ISO_PATH"
    
    # Network
    VBoxManage modifyvm "$VM_NAME" --nic1 nat
    
    echo "✓ VM created"
else
    echo "VM '$VM_NAME' already exists"
fi

# Check if snapshot exists
if VBoxManage snapshot "$VM_NAME" list | grep -q "$SNAPSHOT_NAME"; then
    echo ""
    echo "Snapshot '$SNAPSHOT_NAME' exists - restoring for fresh start..."
    VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null || true
    sleep 2
    VBoxManage snapshot "$VM_NAME" restore "$SNAPSHOT_NAME"
    echo "✓ Restored to clean snapshot"
    echo ""
    echo "VM is ready! Start it in VirtualBox to use."
else
    echo ""
    echo "No snapshot found. After you install Debian and set up the environment,"
    echo "run this to create a snapshot:"
    echo "  ./scripts/vm-snapshot-helper.sh create"
fi

echo ""
echo "=== Quick Start Guide ==="
echo "1. Start VM in VirtualBox"
echo "2. Install Debian (minimal install is fine)"
echo "3. After install, run inside VM:"
echo "   curl -s https://raw.githubusercontent.com/your-repo/setup-vm.sh | bash"
echo "   (or copy scripts/vm-post-install.sh into VM)"
echo "4. Create snapshot: ./scripts/vm-snapshot-helper.sh create"
echo ""
echo "After that, testing is fast - just restore snapshot!"


