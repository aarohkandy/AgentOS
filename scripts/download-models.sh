#!/bin/bash
# Script to download quantized LLM models for the AI agent
# Supports multiple model choices optimized for local inference

set -e

# Default model storage directory
DEFAULT_MODELS_DIR="$HOME/.cache/ai-os-models"
TARGET_DIR="${1:-$DEFAULT_MODELS_DIR}" # Use first argument as target if provided

mkdir -p "$TARGET_DIR"

echo "=== AI-OS Model Download Script ==="
echo ""
echo "Models will be saved to: $TARGET_DIR"
echo ""

# Check for required tools
if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
    echo "❌ Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi

DOWNLOAD_CMD=""
if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -L -C - -o"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -c -O"
fi

echo "=== Available Models ==="
echo ""
echo "1. Llama 3.2 3B Instruct (Q4_K_M) - ~2.0 GB"
echo "   - Fast, efficient, good for general tasks"
echo "   - Recommended for most users"
echo ""
echo "2. Phi-3.5 Mini Instruct (Q4_K_M) - ~2.2 GB"
echo "   - High quality, compact model from Microsoft"
echo "   - Excellent reasoning capabilities"
echo ""
echo "3. Qwen2.5 3B Instruct (Q4_K_M) - ~2.0 GB"
echo "   - Strong coding abilities"
echo "   - Good multilingual support"
echo ""
echo "4. All models (download all three)"
echo ""

# If running non-interactively (e.g. from build script), default to 1
if [ ! -t 0 ]; then
    echo "Non-interactive mode detected. Defaulting to Llama 3.2 3B."
    choice=1
else
    read -p "Select model to download (1-4): " choice
fi

download_model() {
    local name=$1
    local url=$2
    local filename=$3
    
    local filepath="$TARGET_DIR/$filename"
    
    echo ""
    echo "=== Downloading: $name ==="
    echo "File: $filename"
    echo "Destination: $filepath"
    echo ""
    
    if [ -f "$filepath" ]; then
        echo "⚠️  File already exists: $filepath"
        if [ -t 0 ]; then
            read -p "Re-download? (yes/no): " redownload
            if [ "$redownload" != "yes" ]; then
                echo "✓ Skipping download"
                return 0
            fi
        else
            echo "✓ Skipping download (non-interactive)"
            return 0
        fi
    fi
    
    echo "Starting download..."
    $DOWNLOAD_CMD "$filepath" "$url"
    
    if [ $? -eq 0 ]; then
        echo "✓ Download complete: $filename"
        ls -lh "$filepath"
    else
        echo "❌ Download failed"
        return 1
    fi
}

# Model URLs (using HuggingFace)
LLAMA_32_3B_URL="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
PHI_35_MINI_URL="https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf"
QWEN_25_3B_URL="https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf"

case $choice in
    1)
        download_model "Llama 3.2 3B Instruct" "$LLAMA_32_3B_URL" "llama-3.2-3b-instruct-q4_k_m.gguf"
        ;;
    2)
        download_model "Phi-3.5 Mini Instruct" "$PHI_35_MINI_URL" "phi-3.5-mini-instruct-q4_k_m.gguf"
        ;;
    3)
        download_model "Qwen2.5 3B Instruct" "$QWEN_25_3B_URL" "qwen2.5-3b-instruct-q4_k_m.gguf"
        ;;
    4)
        download_model "Llama 3.2 3B Instruct" "$LLAMA_32_3B_URL" "llama-3.2-3b-instruct-q4_k_m.gguf"
        download_model "Phi-3.5 Mini Instruct" "$PHI_35_MINI_URL" "phi-3.5-mini-instruct-q4_k_m.gguf"
        download_model "Qwen2.5 3B Instruct" "$QWEN_25_3B_URL" "qwen2.5-3b-instruct-q4_k_m.gguf"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=== Download Summary ==="
echo ""
echo "Models directory: $TARGET_DIR"
echo ""
echo "Downloaded models:"
ls -lh "$TARGET_DIR"/*.gguf 2>/dev/null || echo "  (none)"
echo ""
echo "✅ Complete!"
