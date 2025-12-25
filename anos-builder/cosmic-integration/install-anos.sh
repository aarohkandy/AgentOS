#!/bin/bash
# Main ANOS installation script (runs in chroot)

set -e

export DEBIAN_FRONTEND=noninteractive

echo "=== ANOS System Installation ==="

# Update package lists
apt-get update -qq

# Install base packages
echo "Installing base packages..."
if [ -f /root/base.list ]; then
    xargs -a /root/base.list apt-get install -y -qq || true
else
    # Fallback minimal install
    apt-get install -y -qq \
        systemd udev dbus network-manager sudo bash \
        apt dpkg wget curl \
        grub-pc linux-image-generic \
        plasma-desktop kwin sddm \
        calamares calamares-settings-ubuntu \
        python3 python3-pip python3-venv
fi

# Remove unwanted packages
if [ -f /root/remove.list ]; then
    echo "Removing unnecessary packages..."
    xargs -a /root/remove.list apt-get remove -y --purge 2>/dev/null || true
    apt-get autoremove -y -qq
    apt-get autoclean -y -qq
fi

# Install Cosmic OS
if [ -d /opt/cosmic-os ] && [ -f /root/install-cosmic.sh ]; then
    echo "Installing Cosmic OS..."
    bash /root/install-cosmic.sh
fi

# Configure KDE
if [ -f /root/configure-kde.sh ]; then
    echo "Configuring KDE..."
    bash /root/configure-kde.sh
fi

# Apply ANOS branding
if [ -f /root/apply-branding.sh ]; then
    echo "Applying ANOS branding..."
    bash /root/apply-branding.sh
fi

# Clean up
apt-get clean
rm -rf /tmp/* /var/tmp/*
rm -f /root/*.sh /root/*.list

echo "=== ANOS Installation Complete ==="




