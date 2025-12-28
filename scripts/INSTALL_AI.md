# Cosmic OS - AI Installation Guide

## Quick Install (Everything)

**One command installs everything:**

```bash
cd ~/cosmic-os
./scripts/install-all.sh
```

This will:
- ✅ Install `llama-cpp-python` (compiles from source, takes 5-10 min)
- ✅ Detect your hardware tier automatically
- ✅ Download AI models to `./models/` (base folder - persists across installs)
- ✅ Create symlinks for compatibility
- ✅ Set up all 3 validators

## Model Storage

**Models are stored in the base folder:**
- Location: `./models/` (in project root)
- **This folder persists across installs!**
- Models are NOT re-downloaded if they already exist

**Why base folder?**
- Models are large (2-8GB each)
- Don't want to re-download every time you reinstall
- Can be shared across VMs/containers
- Easy to backup/restore

## Manual Installation

If you prefer step-by-step:

```bash
# 1. Install llama-cpp-python
pip3 install --user llama-cpp-python

# 2. Download models (auto-detects tier)
./scripts/install-models.sh --tier 2

# 3. Restart daemon
./scripts/start-cosmic-test.sh
```

## Custom Base Folder

To use a different base folder:

```bash
export BASE_MODEL_DIR="/path/to/your/models"
./scripts/install-all.sh
```

Or set it in your environment:
```bash
export BASE_MODEL_DIR="$HOME/cosmic-os-models"
```

## Verification

After installation, check:

```bash
# Check llama-cpp-python
python3 -c "from llama_cpp import Llama; print('OK')"

# Check models
ls -lh ./models/tier*/model.gguf
ls -lh ./models/validators/*.gguf

# Test AI
./scripts/start-cosmic-test.sh
```

## Troubleshooting

**"llama-cpp-python not installed"**
```bash
pip3 install --user llama-cpp-python
```

**"Model not found"**
```bash
./scripts/install-models.sh --tier 2
```

**"Compilation failed"**
```bash
sudo apt-get install cmake build-essential python3-dev
pip3 install --user llama-cpp-python
```

## Model Sizes

- **Tier 1**: ~2GB (SmolLM 1.7B)
- **Tier 2**: ~4GB (Qwen2.5 3B) 
- **Tier 3**: ~8GB (Qwen2.5 7B)
- **Validators**: ~2GB total (3x 0.7GB each)

Total for Tier 2: ~6GB

