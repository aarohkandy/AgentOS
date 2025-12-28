#!/bin/bash
# Check download status and resume incomplete downloads

cd "$(dirname "$0")"

echo "=== Checking Download Status ==="
echo ""

for tier in 1 2 3 4; do
    file="models/tier$tier/model.gguf"
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        size_mb=$((size / 1024 / 1024))
        if [ "$size" -gt 100000000 ]; then  # >100MB = likely complete
            echo "✓ Tier $tier: ${size_mb}MB (likely complete)"
        else
            echo "✗ Tier $tier: ${size_mb}MB (incomplete - will resume)"
        fi
    else
        echo "✗ Tier $tier: Not found (will download)"
    fi
done

echo ""
echo "=== Resuming Downloads ==="
echo ""

# Tier 1
if [ ! -f "models/tier1/model.gguf" ] || [ $(stat -c%s "models/tier1/model.gguf" 2>/dev/null || stat -f%z "models/tier1/model.gguf" 2>/dev/null) -lt 100000000 ]; then
    echo "📥 Resuming Tier 1: TinyLlama 1.1B..."
    wget -c "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" -O "models/tier1/model.gguf"
    echo ""
fi

# Tier 2
if [ ! -f "models/tier2/model.gguf" ] || [ $(stat -c%s "models/tier2/model.gguf" 2>/dev/null || stat -f%z "models/tier2/model.gguf" 2>/dev/null) -lt 3000000000 ]; then
    echo "📥 Resuming Tier 2: Llama 2 7B Chat (~4GB)..."
    wget -c "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf" -O "models/tier2/model.gguf"
    echo ""
fi

# Tier 3
if [ ! -f "models/tier3/model.gguf" ] || [ $(stat -c%s "models/tier3/model.gguf" 2>/dev/null || stat -f%z "models/tier3/model.gguf" 2>/dev/null) -lt 4000000000 ]; then
    echo "📥 Resuming Tier 3: Mistral 7B Instruct (~4.4GB)..."
    wget -c "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf" -O "models/tier3/model.gguf"
    echo ""
fi

# Tier 4
if [ ! -f "models/tier4/model.gguf" ] || [ $(stat -c%s "models/tier4/model.gguf" 2>/dev/null || stat -f%z "models/tier4/model.gguf" 2>/dev/null) -lt 7000000000 ]; then
    echo "📥 Resuming Tier 4: Llama 2 13B Chat (~7.4GB)..."
    wget -c "https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf" -O "models/tier4/model.gguf"
    echo ""
fi

echo "=== Final Status ==="
ls -lh models/tier*/model.gguf

