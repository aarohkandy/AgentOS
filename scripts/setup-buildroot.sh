#!/bin/bash
set -e

# Setup Buildroot environment
# This script ensures Buildroot is extracted and ready

if [ -d "buildroot" ]; then
    echo "Buildroot directory already exists."
    exit 0
fi

if [ -f "buildroot-2024.11.tar.gz" ]; then
    echo "Extracting Buildroot from local archive..."
    tar -xzf buildroot-2024.11.tar.gz
    mv buildroot-2024.11 buildroot
    echo "Buildroot extracted."
else
    echo "Downloading Buildroot 2024.11..."
    wget https://buildroot.org/downloads/buildroot-2024.11.tar.gz
    tar -xzf buildroot-2024.11.tar.gz
    mv buildroot-2024.11 buildroot
    echo "Buildroot downloaded and extracted."
fi
