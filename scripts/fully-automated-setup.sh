#!/bin/bash
# Fully automated setup - creates VM, installs Debian automatically, sets everything up

set -e

VM_NAME="AgenticOS"
ISO_PATH="/home/aaroh/Downloads/AgentOS/debian-netinst.iso"
PRESEED="/home/aaroh/Downloads/AgentOS/iso-build/preseed.cfg"

echo "=== Fully Automated OS Setup ==="
echo ""

# Delete old VM if exists
if VBoxManage showvminfo "$VM_NAME" &>/dev/null 2>&1; then
    echo "Deleting old VM..."
    VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null || true
    sleep 2
    VBoxManage unregistervm "$VM_NAME" --delete 2>/dev/null || true
fi

# 1. Create VM
echo "1. Creating VM..."
VBoxManage createvm --name "$VM_NAME" --ostype "Debian_64" --register

# 2. Configure VM
echo "2. Configuring VM..."
VBoxManage modifyvm "$VM_NAME" --memory 4096 --cpus 2
VBoxManage modifyvm "$VM_NAME" --boot1 dvd --boot2 disk
VBoxManage modifyvm "$VM_NAME" --nic1 nat

# 3. Create disk
echo "3. Creating virtual disk..."
VBoxManage createhd --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" --size 20480 --format VDI

# 4. Attach storage
echo "4. Attaching storage..."
VBoxManage storagectl "$VM_NAME" --name "SATA" --add sata --controller IntelAHCI
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi"

VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide
VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium "$ISO_PATH"

# 5. Create shared folder for preseed
echo "5. Setting up automated installation..."
VBoxManage sharedfolder add "$VM_NAME" --name "preseed" --hostpath "$(dirname "$PRESEED")" --automount

# 6. Start VM with preseed
echo "6. Starting automated installation..."
echo ""
echo "The VM will start and install Debian automatically."
echo "It will use these settings:"
echo "  - User: ai"
echo "  - Password: ai-os-dev"
echo "  - Root password: ai-os-dev"
echo "  - All dev tools pre-installed"
echo ""
echo "Installation will take ~10-15 minutes (automated, no interaction needed)"
echo ""

VBoxManage startvm "$VM_NAME" --type gui

echo ""
echo "VM is starting. The installation will run automatically."
echo "You can watch it, but no interaction is needed."
echo ""
echo "After installation completes and VM reboots, you can:"
echo "  1. Log in (user: ai, password: ai-os-dev)"
echo "  2. Run: ./vm-post-install.sh (if you copy it into VM)"
echo "  3. Create snapshot: ./scripts/vm-snapshot-helper.sh create"


