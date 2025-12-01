#!/bin/bash
# Build Windows-like desktop with XFCE

cd buildroot

# Add XFCE desktop environment (Windows-like)
cat >> .config << 'EOF'

# XFCE Desktop (full Windows-like environment)
BR2_PACKAGE_XFCE4=y
BR2_PACKAGE_XFCE4_PANEL=y
BR2_PACKAGE_XFCE4_SESSION=y
BR2_PACKAGE_XFCE4_SETTINGS=y
BR2_PACKAGE_XFCE4_TERMINAL=y

# File manager
BR2_PACKAGE_THUNAR=y

# Window manager  
BR2_PACKAGE_XFWM4=y

# Desktop manager
BR2_PACKAGE_XFDESKTOP=y

# Display manager (login screen)
BR2_PACKAGE_LIGHTDM=y

# Essential apps
BR2_PACKAGE_MOUSEPAD=y

# Make sure X11 is there
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y

EOF

# Fix legacy and rebuild
sed -i 's/BR2_LEGACY=y/# BR2_LEGACY is not set/' .config
make olddefconfig
make -j$(nproc)

echo "XFCE desktop build complete!"
