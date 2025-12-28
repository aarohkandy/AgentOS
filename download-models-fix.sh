#!/bin/bash
# Download models with proper error handling and progress

set -e

cd "$(dirname "$0")"
mkdir -p models/tier2 models/tier3 models/tier4

echo "=== Downloading Missing Models ==="
echo ""

# Tier 2
echo "📥 Tier 2: Llama 3.2 3B (~2.5GB)..."
python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
from pathlib import Path
import shutil
import sys

try:
    print("Starting download...")
    sys.stdout.flush()
    downloaded = hf_hub_download(
        repo_id="TheBloke/Llama-3.2-3B-Instruct-GGUF",
        filename="llama-3.2-3b-instruct.Q4_K_M.gguf",
        local_dir="models/tier2",
        local_dir_use_symlinks=False,
        resume_download=True
    )
    target = Path("models/tier2/model.gguf")
    if Path(downloaded).name != "model.gguf":
        shutil.move(downloaded, target)
    size = target.stat().st_size / (1024**2)
    print(f"✓ Tier 2: {size:.2f} MB")
except Exception as e:
    print(f"✗ Tier 2 error: {e}")
    sys.exit(1)
PYEOF

echo ""

# Tier 3
echo "📥 Tier 3: Qwen 2.5 7B (~4.5GB)..."
python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
from pathlib import Path
import shutil
import sys

try:
    print("Starting download...")
    sys.stdout.flush()
    downloaded = hf_hub_download(
        repo_id="TheBloke/Qwen2.5-7B-Instruct-GGUF",
        filename="qwen2.5-7b-instruct.Q4_K_M.gguf",
        local_dir="models/tier3",
        local_dir_use_symlinks=False,
        resume_download=True
    )
    target = Path("models/tier3/model.gguf")
    if Path(downloaded).name != "model.gguf":
        shutil.move(downloaded, target)
    size = target.stat().st_size / (1024**2)
    print(f"✓ Tier 3: {size:.2f} MB")
except Exception as e:
    print(f"✗ Tier 3 error: {e}")
    sys.exit(1)
PYEOF

echo ""

# Tier 4
echo "📥 Tier 4: Llama 3.1 70B (~40GB - this will take a while)..."
python3 << 'PYEOF'
from huggingface_hub import hf_hub_download
from pathlib import Path
import shutil
import sys

try:
    print("Starting download (this is a large file)...")
    sys.stdout.flush()
    downloaded = hf_hub_download(
        repo_id="TheBloke/Llama-3.1-70B-Instruct-GGUF",
        filename="llama-3.1-70b-instruct.Q4_K_M.gguf",
        local_dir="models/tier4",
        local_dir_use_symlinks=False,
        resume_download=True
    )
    target = Path("models/tier4/model.gguf")
    if Path(downloaded).name != "model.gguf":
        shutil.move(downloaded, target)
    size = target.stat().st_size / (1024**3)
    print(f"✓ Tier 4: {size:.2f} GB")
except Exception as e:
    print(f"✗ Tier 4 error: {e}")
    sys.exit(1)
PYEOF

echo ""
echo "=== Final Status ==="
python3 << 'PYEOF'
from pathlib import Path

for tier in [1, 2, 3, 4]:
    model = Path(f"models/tier{tier}/model.gguf")
    if model.exists():
        size = model.stat().st_size
        if size > 0:
            size_mb = size / (1024**2)
            size_gb = size / (1024**3)
            if size_gb >= 1:
                print(f"✓ Tier {tier}: {size_gb:.2f} GB")
            else:
                print(f"✓ Tier {tier}: {size_mb:.2f} MB")
        else:
            print(f"✗ Tier {tier}: 0 bytes")
    else:
        print(f"✗ Tier {tier}: Not found")
PYEOF


