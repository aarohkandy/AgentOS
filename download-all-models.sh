#!/bin/bash
# Download all 4 tier models to the shared folder

set -e

cd "$(dirname "$0")"
mkdir -p models/tier1 models/tier2 models/tier3 models/tier4

echo "=== Downloading All 4 Tier Models ==="
echo ""

# Tier 1: TinyLlama 1.1B
echo "📥 Tier 1: TinyLlama 1.1B..."
if [ ! -f "models/tier1/model.gguf" ]; then
    python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

downloaded = hf_hub_download(
    repo_id="TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    filename="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    local_dir="models/tier1",
    local_dir_use_symlinks=False
)
target = Path("models/tier1/model.gguf")
if Path(downloaded).name != "model.gguf":
    shutil.move(downloaded, target)
print(f"✓ Tier 1: {target}")
PYEOF
else
    echo "✓ Tier 1: Already exists"
fi

# Tier 2: Llama 3.2 3B
echo "📥 Tier 2: Llama 3.2 3B..."
if [ ! -f "models/tier2/model.gguf" ]; then
    python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

downloaded = hf_hub_download(
    repo_id="TheBloke/Llama-3.2-3B-Instruct-GGUF",
    filename="llama-3.2-3b-instruct.Q4_K_M.gguf",
    local_dir="models/tier2",
    local_dir_use_symlinks=False
)
target = Path("models/tier2/model.gguf")
if Path(downloaded).name != "model.gguf":
    shutil.move(downloaded, target)
print(f"✓ Tier 2: {target}")
PYEOF
else
    echo "✓ Tier 2: Already exists"
fi

# Tier 3: Qwen 2.5 7B
echo "📥 Tier 3: Qwen 2.5 7B..."
if [ ! -f "models/tier3/model.gguf" ]; then
    python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

downloaded = hf_hub_download(
    repo_id="TheBloke/Qwen2.5-7B-Instruct-GGUF",
    filename="qwen2.5-7b-instruct.Q4_K_M.gguf",
    local_dir="models/tier3",
    local_dir_use_symlinks=False
)
target = Path("models/tier3/model.gguf")
if Path(downloaded).name != "model.gguf":
    shutil.move(downloaded, target)
print(f"✓ Tier 3: {target}")
PYEOF
else
    echo "✓ Tier 3: Already exists"
fi

# Tier 4: Llama 3.1 70B
echo "📥 Tier 4: Llama 3.1 70B..."
if [ ! -f "models/tier4/model.gguf" ]; then
    python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

downloaded = hf_hub_download(
    repo_id="TheBloke/Llama-3.1-70B-Instruct-GGUF",
    filename="llama-3.1-70b-instruct.Q4_K_M.gguf",
    local_dir="models/tier4",
    local_dir_use_symlinks=False
)
target = Path("models/tier4/model.gguf")
if Path(downloaded).name != "model.gguf":
    shutil.move(downloaded, target)
print(f"✓ Tier 4: {target}")
PYEOF
else
    echo "✓ Tier 4: Already exists"
fi

echo ""
echo "=== Download Complete ==="
echo ""
for tier in 1 2 3 4; do
    if [ -f "models/tier$tier/model.gguf" ]; then
        size=$(du -h "models/tier$tier/model.gguf" | cut -f1)
        echo "✓ Tier $tier: $size"
    else
        echo "✗ Tier $tier: Failed"
    fi
done


