#!/bin/sh
# Quick Alpine Linux Desktop Setup Script
# Run this inside Alpine VM after boot

echo "=========================================="
echo "Installing Desktop Environment"
echo "=========================================="

# Setup networking
setup-interfaces -a
rc-service networking start

# Update repos
apk update

# Install X11 and desktop
apk add xorg-server xf86-video-vesa xf86-input-mouse xf86-input-keyboard

# Install Openbox and components
apk add openbox tint2 pcmanfm xterm

# Install fonts
apk add ttf-liberation ttf-dejavu

# Set beige background
echo 'xsetroot -solid "#F5F5DC"' > /root/.xinitrc
echo 'openbox &' >> /root/.xinitrc
echo 'tint2 &' >> /root/.xinitrc  
echo 'pcmanfm -d &' >> /root/.xinitrc
chmod +x /root/.xinitrc

# Auto-start X11
echo 'if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then' >> /root/.profile
echo '    startx' >> /root/.profile
echo 'fi' >> /root/.profile

echo ""
echo "=========================================="
echo "Desktop setup complete!"
echo "=========================================="
echo "Type 'reboot' to restart and see your desktop"
echo ""
