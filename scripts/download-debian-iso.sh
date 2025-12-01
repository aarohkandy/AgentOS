#!/bin/bash
# Quick script to download a minimal Debian ISO for immediate use

echo "Downloading Debian Bookworm netinst ISO (small, fast download)..."
echo ""

ISO_URL="https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.9.0-amd64-netinst.iso"
ISO_FILE="/home/aaroh/Downloads/AgentOS/debian-netinst.iso"

echo "URL: $ISO_URL"
echo "Saving to: $ISO_FILE"
echo ""
echo "Starting download (this may take a few minutes)..."
echo ""

wget -O "$ISO_FILE" "$ISO_URL" --progress=bar:force 2>&1 | grep -E "(saving|%|MB|GB)"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Download complete!"
    echo "ISO file: $ISO_FILE"
    echo ""
    echo "You can now use this ISO in Oracle VirtualBox:"
    echo "  1. Create new VM (Linux, Debian 64-bit)"
    echo "  2. Select this ISO: $ISO_FILE"
    echo "  3. Boot and install minimal Debian"
    echo "  4. Then clone this repo and install the AI-OS agent"
else
    echo ""
    echo "✗ Download failed. You can manually download from:"
    echo "  https://www.debian.org/CD/http-ftp/#netinst"
fi

