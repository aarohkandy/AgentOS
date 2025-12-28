#!/bin/bash
# DOWNLOAD MODELS - Run this manually!
# These are VERIFIED WORKING URLs from TheBloke's HuggingFace

set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "AgentOS Model Downloader"
echo "=============================================="
echo ""

mkdir -p models/tier1 models/tier2 models/tier3 models/tier4

# Tier 1: TinyLlama (already downloaded, skip if exists)
TIER1="models/tier1/model.gguf"
if [ -f "$TIER1" ] && [ $(stat -c%s "$TIER1" 2>/dev/null || stat -f%z "$TIER1" 2>/dev/null) -gt 100000000 ]; then
    echo "✓ Tier 1 already downloaded"
else
    echo "📥 Downloading Tier 1: TinyLlama 1.1B (~638MB)..."
    wget -c "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" -O "$TIER1"
fi
echo ""

# Tier 2: Llama-2-7B-Chat (VERIFIED - this repo exists)
TIER2="models/tier2/model.gguf"
rm -f "$TIER2" 2>/dev/null
echo "📥 Downloading Tier 2: Llama 2 7B Chat (~4GB)..."
echo "   URL: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
wget -c "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf" -O "$TIER2"
echo ""

# Tier 3: Mistral-7B-Instruct (VERIFIED - this repo exists)
TIER3="models/tier3/model.gguf"
rm -f "$TIER3" 2>/dev/null
echo "📥 Downloading Tier 3: Mistral 7B Instruct (~4.4GB)..."
echo "   URL: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
wget -c "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf" -O "$TIER3"
echo ""

# Tier 4: Llama-2-13B-Chat (VERIFIED - this repo exists, smaller than 70B for practicality)
TIER4="models/tier4/model.gguf"
rm -f "$TIER4" 2>/dev/null
echo "📥 Downloading Tier 4: Llama 2 13B Chat (~7.4GB)..."
echo "   URL: https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf"
wget -c "https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf" -O "$TIER4"
echo ""

echo "=============================================="
echo "Download Complete! Checking sizes..."
echo "=============================================="
ls -lh models/tier*/model.gguf


