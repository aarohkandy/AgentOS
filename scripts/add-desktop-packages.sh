#!/bin/bash
# Add X11 and desktop packages to Buildroot config

cd buildroot

# Enable X11
echo "BR2_PACKAGE_XORG7=y" >> .config
echo "BR2_PACKAGE_XSERVER_XORG_SERVER=y" >> .config
echo "BR2_PACKAGE_XSERVER_XORG_SERVER_MODULAR=y" >> .config

# Graphics drivers for VirtualBox
echo "BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y" >> .config
echo "BR2_PACKAGE_XDRIVER_XF86_VIDEO_FBDEV=y" >> .config
echo "BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y" >> .config  
echo "BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y" >> .config

# Window manager and desktop
echo "BR2_PACKAGE_OPENBOX=y" >> .config
echo "BR2_PACKAGE_TINT2=y" >> .config
echo "BR2_PACKAGE_PCMANFM=y" >> .config

# Terminal
echo "BR2_PACKAGE_XTERM=y" >> .config

# Fonts
echo "BR2_PACKAGE_LIBERATION=y" >> .config
echo "BR2_PACKAGE_DEJAVU=y" >> .config
echo "BR2_PACKAGE_FONT_UTIL=y" >> .config

# Desktop utilities
echo "BR2_PACKAGE_FLTK=y" >> .config

# Reprocess config to resolve dependencies
make olddefconfig

echo "X11 and desktop packages added!"
