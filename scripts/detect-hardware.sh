#!/bin/bash
# Cosmic OS - Hardware Detection Script
# Detects system capabilities and recommends appropriate AI tier

set -e

echo "🔍 Cosmic OS - Hardware Detection"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Output format (json or text)
OUTPUT_FORMAT="${1:-text}"

# Gather system info
get_cpu_info() {
    CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
    CPU_CORES=$(nproc)
    CPU_THREADS=$(grep -c processor /proc/cpuinfo)
}

get_memory_info() {
    MEM_TOTAL_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    MEM_TOTAL_GB=$((MEM_TOTAL_KB / 1024 / 1024))
    MEM_AVAILABLE_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    MEM_AVAILABLE_GB=$((MEM_AVAILABLE_KB / 1024 / 1024))
}

get_gpu_info() {
    HAS_NVIDIA=false
    HAS_AMD=false
    NVIDIA_GPU=""
    NVIDIA_VRAM=""
    AMD_GPU=""
    
    # Check NVIDIA
    if command -v nvidia-smi &> /dev/null; then
        HAS_NVIDIA=true
        NVIDIA_GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        NVIDIA_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1)
    fi
    
    # Check AMD
    if lspci 2>/dev/null | grep -i "vga.*amd\|radeon" > /dev/null; then
        HAS_AMD=true
        AMD_GPU=$(lspci 2>/dev/null | grep -i "vga.*amd\|radeon" | head -1 | cut -d: -f3 | xargs)
    fi
    
    # Check Intel integrated
    HAS_INTEL_GPU=false
    if lspci 2>/dev/null | grep -i "vga.*intel" > /dev/null; then
        HAS_INTEL_GPU=true
    fi
}

get_disk_info() {
    DISK_TOTAL=$(df -BG / | awk 'NR==2 {print $2}' | tr -d 'G')
    DISK_AVAILABLE=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
}

get_os_info() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="$NAME"
        OS_VERSION="$VERSION_ID"
    else
        OS_NAME=$(uname -s)
        OS_VERSION=$(uname -r)
    fi
    
    KERNEL=$(uname -r)
    DESKTOP="${XDG_CURRENT_DESKTOP:-Unknown}"
    DISPLAY_SERVER="${XDG_SESSION_TYPE:-Unknown}"
}

# Determine recommended tier
calculate_tier() {
    TIER=1
    TIER_REASON=""
    
    # Check RAM first
    if [ "$MEM_TOTAL_GB" -ge 16 ]; then
        TIER=3
        TIER_REASON="16GB+ RAM"
    elif [ "$MEM_TOTAL_GB" -ge 8 ]; then
        TIER=2
        TIER_REASON="8-16GB RAM"
    else
        TIER=1
        TIER_REASON="<8GB RAM"
    fi
    
    # GPU can upgrade tier
    if [ "$HAS_NVIDIA" = true ]; then
        if [ "$TIER" -lt 3 ]; then
            TIER=3
            TIER_REASON="NVIDIA GPU detected"
        fi
    fi
    
    # Check disk space requirements
    case $TIER in
        1) REQUIRED_DISK=5 ;;
        2) REQUIRED_DISK=8 ;;
        3) REQUIRED_DISK=15 ;;
    esac
    
    if [ "$DISK_AVAILABLE" -lt "$REQUIRED_DISK" ]; then
        if [ "$TIER" -gt 1 ]; then
            TIER=$((TIER - 1))
            TIER_REASON="Disk space limited to ${DISK_AVAILABLE}GB"
        fi
    fi
}

# Output results
output_text() {
    echo ""
    echo -e "${CYAN}=== CPU ===${NC}"
    echo "  Model: $CPU_MODEL"
    echo "  Cores: $CPU_CORES (Threads: $CPU_THREADS)"
    
    echo ""
    echo -e "${CYAN}=== Memory ===${NC}"
    echo "  Total: ${MEM_TOTAL_GB}GB"
    echo "  Available: ${MEM_AVAILABLE_GB}GB"
    
    echo ""
    echo -e "${CYAN}=== GPU ===${NC}"
    if [ "$HAS_NVIDIA" = true ]; then
        echo "  NVIDIA: $NVIDIA_GPU"
        echo "  VRAM: $NVIDIA_VRAM"
    elif [ "$HAS_AMD" = true ]; then
        echo "  AMD: $AMD_GPU"
    elif [ "$HAS_INTEL_GPU" = true ]; then
        echo "  Intel Integrated Graphics"
    else
        echo "  No dedicated GPU detected"
    fi
    
    echo ""
    echo -e "${CYAN}=== Storage ===${NC}"
    echo "  Total: ${DISK_TOTAL}GB"
    echo "  Available: ${DISK_AVAILABLE}GB"
    
    echo ""
    echo -e "${CYAN}=== System ===${NC}"
    echo "  OS: $OS_NAME $OS_VERSION"
    echo "  Kernel: $KERNEL"
    echo "  Desktop: $DESKTOP"
    echo "  Display: $DISPLAY_SERVER"
    
    echo ""
    echo -e "${GREEN}=== Recommendation ===${NC}"
    echo -e "  Recommended Tier: ${YELLOW}$TIER${NC}"
    echo "  Reason: $TIER_REASON"
    echo ""
    
    case $TIER in
        1)
            echo "  Tier 1 (Lightweight): SmolLM 1.7B or Phi-3 Mini"
            echo "  - Fast response times"
            echo "  - Basic assistance capabilities"
            echo "  - ~2GB download"
            ;;
        2)
            echo "  Tier 2 (Balanced): Qwen2.5 3B or Llama 3.2 3B"
            echo "  - Good balance of speed and capability"
            echo "  - Handles complex tasks well"
            echo "  - ~4GB download"
            ;;
        3)
            echo "  Tier 3 (Powerful): Qwen2.5 7B or Llama 3.1 8B"
            echo "  - Best reasoning and accuracy"
            echo "  - Handles multi-step tasks"
            echo "  - ~8GB download"
            ;;
    esac
    echo ""
}

output_json() {
    cat << EOF
{
    "cpu": {
        "model": "$CPU_MODEL",
        "cores": $CPU_CORES,
        "threads": $CPU_THREADS
    },
    "memory": {
        "total_gb": $MEM_TOTAL_GB,
        "available_gb": $MEM_AVAILABLE_GB
    },
    "gpu": {
        "has_nvidia": $HAS_NVIDIA,
        "has_amd": $HAS_AMD,
        "nvidia_model": "$NVIDIA_GPU",
        "nvidia_vram": "$NVIDIA_VRAM",
        "amd_model": "$AMD_GPU"
    },
    "disk": {
        "total_gb": $DISK_TOTAL,
        "available_gb": $DISK_AVAILABLE
    },
    "os": {
        "name": "$OS_NAME",
        "version": "$OS_VERSION",
        "kernel": "$KERNEL",
        "desktop": "$DESKTOP",
        "display_server": "$DISPLAY_SERVER"
    },
    "recommendation": {
        "tier": $TIER,
        "reason": "$TIER_REASON"
    }
}
EOF
}

# Main
main() {
    get_cpu_info
    get_memory_info
    get_gpu_info
    get_disk_info
    get_os_info
    calculate_tier
    
    case $OUTPUT_FORMAT in
        json)
            output_json
            ;;
        *)
            output_text
            ;;
    esac
}

main
