#!/bin/bash
# Boot Buildroot OS with QEMU (handles it better than VirtualBox)

qemu-system-x86_64 \
  -m 1024 \
  -kernel buildroot/output/images/bzImage \
  -hda buildroot/output/images/rootfs.ext2 \
  -append "root=/dev/sda rw console=tty1" \
  -vga std \
  -display gtk \
  -name "AI-OS GUI"
