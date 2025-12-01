#!/bin/bash
# Fully automated OS setup - creates VM, configures everything, starts it

set -e

VM_NAME="AgenticOS"
ISO_AUTO="/home/aaroh/Downloads/AgentOS/debian-auto.iso"
ISO_FALLBACK="/home/aaroh/Downloads/AgentOS/debian-netinst.iso"

# Use automated ISO if it exists, otherwise use regular ISO
if [ -f "$ISO_AUTO" ]; then
    ISO_PATH="$ISO_AUTO"
    echo "Using automated installation ISO"
else
    ISO_PATH="$ISO_FALLBACK"
    echo "Using regular ISO (will need manual installation)"
    echo "To create automated ISO, run: ./scripts/create-automated-iso.sh"
fi

echo "=== Fully Automated OS Setup ==="
echo ""

# 1. Create VM
echo "1. Creating VM..."
VBoxManage createvm --name "$VM_NAME" --ostype "Debian_64" --register

# 2. Configure VM with optimal settings
echo "2. Configuring VM..."
VBoxManage modifyvm "$VM_NAME" --memory 4096 --cpus 2
VBoxManage modifyvm "$VM_NAME" --boot1 dvd --boot2 disk --boot3 none --boot4 none
VBoxManage modifyvm "$VM_NAME" --nic1 nat

# 3. Create and attach disk
echo "3. Creating virtual disk..."
VBoxManage createhd --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" --size 20480 --format VDI

# 4. Attach storage controllers
echo "4. Attaching storage..."
VBoxManage storagectl "$VM_NAME" --name "SATA" --add sata --controller IntelAHCI
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi"

VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide
VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium "$ISO_PATH"

# 5. Enable hardware acceleration
echo "5. Configuring acceleration..."
VBoxManage modifyvm "$VM_NAME" --paravirtprovider kvm 2>/dev/null || true

echo ""
echo "✓ VM created and configured"
echo ""

# 6. Start VM
echo "6. Starting OS..."
VBoxManage startvm "$VM_NAME" --type gui

echo ""
echo "=== OS Starting ==="
echo ""
echo "The VM window will open - you can now:"
echo "  - Install Debian (follow the installer)"
echo "  - Or if already installed, it will boot into the OS"
echo ""
echo "After installation, inside the VM run:"
echo "  ./vm-post-install.sh"
echo ""
echo "Then from host, create snapshot:"
echo "  ./scripts/vm-snapshot-helper.sh create"

