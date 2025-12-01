#!/bin/bash
# Quick rebuild with auto-startx and simpler boot

cd buildroot

# Add auto-login and startx
mkdir -p output/target/etc
cat > output/target/etc/issue << 'EOF'
AI-OS - Custom Operating System

EOF

# Create auto-login for tty1
cat > output/target/etc/inittab << 'EOF'
::sysinit:/bin/mount -t proc proc /proc
::sysinit:/bin/mount -o remount,rw /
::sysinit:/bin/mkdir -p /dev/pts /dev/shm
::sysinit:/bin/mount -a
::sysinit:/bin/hostname -F /etc/hostname
::sysinit:/etc/init.d/rcS

# Auto-login and start X on tty1
tty1::respawn:/bin/login -f root

::ctrlaltdel:/sbin/reboot
::shutdown:/etc/init.d/rcK
::shutdown:/sbin/swapoff -a
::shutdown:/bin/umount -a -r
EOF

# Create .profile that starts X automatically
cat > output/target/root/.profile << 'EOF'
export PATH=/usr/local/bin:/usr/bin:/bin
export HOME=/root

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
fi
EOF

# Rebuild just the filesystem
make

echo "Rebuild complete!"
