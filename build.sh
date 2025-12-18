#!/bin/bash
set -e

echo "════════════════════════════════════════"
echo "  agentOS ISO Builder"
echo "════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in Docker
if [ ! -f /.dockerenv ]; then
    echo -e "${YELLOW}Not running in Docker. Starting Docker build environment...${NC}"
    
    # Build Docker image if it doesn't exist
    if ! docker image inspect agentos-builder >/dev/null 2>&1; then
        echo -e "${YELLOW}Building Docker image...${NC}"
        docker build -t agentos-builder -f- . <<DOCKERFILE
FROM debian:bookworm
RUN apt-get update && \
    apt-get install -y \
        live-build \
        debootstrap \
        squashfs-tools \
        xorriso \
        isolinux \
        syslinux-efi \
        grub-pc-bin \
        grub-efi-amd64-bin \
        mtools \
        dosfstools && \
    apt-get clean
WORKDIR /build
DOCKERFILE
    fi
    
    echo -e "${GREEN}Starting Docker container...${NC}"
    docker run --rm --privileged \
        -v "$(pwd):/build" \
        -it agentos-builder \
        /build/build.sh
    
    exit 0
fi

# We're inside Docker now
echo -e "${GREEN}Running inside Docker container${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
lb clean --purge || true
rm -f *.iso *.img

# Configure live-build
echo -e "${YELLOW}Configuring live-build...${NC}"
bash config/lb-config

# Build the ISO
echo -e "${YELLOW}Building ISO (this will take 30-60 minutes)...${NC}"
echo ""
lb build 2>&1 | tee build.log

# Check if build succeeded
if [ -f live-image-amd64.hybrid.iso ]; then
    # Rename to something cleaner
    mv live-image-amd64.hybrid.iso agentOS-amd64.hybrid.iso
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}  BUILD SUCCESSFUL!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo -e "ISO Location: ${GREEN}$(pwd)/agentOS-amd64.hybrid.iso${NC}"
    echo -e "ISO Size: $(du -h agentOS-amd64.hybrid.iso | cut -f1)"
    echo ""
    echo "Next steps:"
    echo "1. Load agentOS-amd64.hybrid.iso into Oracle VM"
    echo "2. Boot from ISO"
    echo "3. Test the system"
    echo ""
else
    echo ""
    echo -e "${RED}════════════════════════════════════════${NC}"
    echo -e "${RED}  BUILD FAILED${NC}"
    echo -e "${RED}════════════════════════════════════════${NC}"
    echo ""
    echo "Check build.log for errors"
    exit 1
fi
