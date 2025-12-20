#!/bin/bash
# Hardware Detection Script for Cosmic OS

echo "Detecting Hardware Tier..."

TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))

echo "RAM: ${TOTAL_MEM_GB}GB"

HAS_GPU=false
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    HAS_GPU=true
fi

TIER=1

if [ "$HAS_GPU" = true ] || [ "$TOTAL_MEM_GB" -gt 16 ]; then
    TIER=3
elif [ "$TOTAL_MEM_GB" -ge 8 ]; then
    TIER=2
else
    TIER=1
fi

echo "Detected Tier: $TIER"
echo $TIER > /tmp/cosmic_tier
