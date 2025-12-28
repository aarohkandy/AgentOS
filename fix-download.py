#!/usr/bin/env python3
"""
Download verified working GGUF models for AgentOS
"""
import os
import sys
import shutil
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

print("=" * 60)
print("AgentOS Model Downloader")
print("=" * 60)
print()

# Create directories
for tier in [1, 2, 3, 4]:
    Path(f"models/tier{tier}").mkdir(parents=True, exist_ok=True)

# Check if huggingface_hub is available
try:
    from huggingface_hub import hf_hub_download
    print("✓ huggingface_hub available")
except ImportError:
    print("✗ huggingface_hub not installed")
    print("Installing...")
    os.system("pip3 install --user huggingface_hub")
    from huggingface_hub import hf_hub_download

print()

# Verified working models (these repos definitely exist)
MODELS = {
    # Tier 1: Already downloaded - TinyLlama
    1: {
        "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "name": "TinyLlama 1.1B",
        "size": "~638MB"
    },
    # Tier 2: Llama 2 7B (verified working)
    2: {
        "repo": "TheBloke/Llama-2-7B-Chat-GGUF",
        "file": "llama-2-7b-chat.Q4_K_M.gguf",
        "name": "Llama 2 7B Chat",
        "size": "~4GB"
    },
    # Tier 3: Mistral 7B (verified working)
    3: {
        "repo": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "file": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "name": "Mistral 7B Instruct",
        "size": "~4.4GB"
    },
    # Tier 4: Llama 2 13B (verified working, smaller than 70B)
    4: {
        "repo": "TheBloke/Llama-2-13B-chat-GGUF",
        "file": "llama-2-13b-chat.Q4_K_M.gguf",
        "name": "Llama 2 13B Chat",
        "size": "~7.4GB"
    }
}

def download_model(tier):
    model_info = MODELS[tier]
    target_dir = Path(f"models/tier{tier}")
    target_file = target_dir / "model.gguf"
    
    # Check if already downloaded
    if target_file.exists() and target_file.stat().st_size > 1000000:  # >1MB
        size_mb = target_file.stat().st_size / (1024**2)
        print(f"✓ Tier {tier} ({model_info['name']}): Already downloaded ({size_mb:.1f}MB)")
        return True
    
    # Remove 0-byte file if exists
    if target_file.exists():
        target_file.unlink()
    
    print(f"📥 Tier {tier}: Downloading {model_info['name']} ({model_info['size']})...")
    print(f"   Repo: {model_info['repo']}")
    print(f"   File: {model_info['file']}")
    sys.stdout.flush()
    
    try:
        downloaded = hf_hub_download(
            repo_id=model_info['repo'],
            filename=model_info['file'],
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        # Rename to model.gguf
        downloaded_path = Path(downloaded)
        if downloaded_path.name != "model.gguf":
            shutil.move(downloaded_path, target_file)
        
        size_mb = target_file.stat().st_size / (1024**2)
        print(f"✓ Tier {tier}: Downloaded successfully ({size_mb:.1f}MB)")
        return True
        
    except Exception as e:
        print(f"✗ Tier {tier}: Download failed - {e}")
        return False

# Download each tier
print("Starting downloads...")
print()

for tier in [1, 2, 3, 4]:
    download_model(tier)
    print()

# Final status
print("=" * 60)
print("Final Status")
print("=" * 60)
for tier in [1, 2, 3, 4]:
    target_file = Path(f"models/tier{tier}/model.gguf")
    if target_file.exists():
        size = target_file.stat().st_size
        if size > 1000000:
            size_mb = size / (1024**2)
            size_gb = size / (1024**3)
            if size_gb >= 1:
                print(f"✓ Tier {tier}: {size_gb:.2f}GB")
            else:
                print(f"✓ Tier {tier}: {size_mb:.1f}MB")
        else:
            print(f"✗ Tier {tier}: {size} bytes (incomplete)")
    else:
        print(f"✗ Tier {tier}: Not found")

print()
print("Done!")

