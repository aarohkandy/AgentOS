# AI Models

AgentOS uses AI models that are **not included in this repository** due to their large size (16GB+ total).

## Quick Setup

Models are automatically downloaded when you run:

```bash
./scripts/install-models.sh --tier [1-4]
```

Or use the auto-setup:

```bash
anos --setup
```

## Direct Download Links

All model URLs are stored in `config/model-urls.json`. Here are direct links for manual download:

### Tier 1 - Easy (<2GB RAM)
- **TinyLlama 1.1B Chat** (~640MB)
  - URL: `https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`
  - Save to: `models/tier1/model.gguf`

### Tier 2 - Mid (2-8GB RAM)
- **Qwen 2.5 0.5B Instruct** (~400MB)
  - URL: `https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf`
  - Save to: `models/tier2/model.gguf`

### Tier 3 - Hard (8-16GB RAM)
- **Llama 3.2 3B Instruct** (~2GB)
  - URL: `https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf`
  - Save to: `models/tier3/model.gguf`

### Tier 4 - Very Powerful (16GB+ RAM or 8GB+ VRAM)
- **Llama 3.1 8B Instruct** (~4.9GB)
  - URL: `https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q4_K_M.gguf`
  - Save to: `models/tier4/model.gguf`

### Tier 5 - Frontier (64GB+ RAM or 40GB+ VRAM)
- **Llama 3.1 70B Instruct** (~38GB)
  - URL: `https://huggingface.co/TheBloke/Llama-3.1-70B-Instruct-GGUF/resolve/main/llama-3.1-70b-instruct.Q4_K_M.gguf`
  - Save to: `models/tier5/model.gguf`
- **DeepSeek-V3** (~40GB)
  - URL: `https://huggingface.co/TheBloke/DeepSeek-V3-GGUF/resolve/main/deepseek-v3.Q4_K_M.gguf`
  - Save to: `models/tier5/deepseek-v3.gguf`

### Validator Models (Optional)
- **TinyLlama 1.1B** (for all 3 validators, ~700MB each)
  - URL: `https://huggingface.co/TheBloke/TinyLlama-1.1B-GGUF/resolve/main/tinyllama-1.1b.Q4_K_M.gguf`
  - Save to: `models/validators/safety.gguf`, `logic.gguf`, `efficiency.gguf`

## Manual Download Example

```bash
# Create directory
mkdir -p models/tier3

# Download using wget
wget -O models/tier3/model.gguf \
  "https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf"

# Or using curl
curl -L -o models/tier3/model.gguf \
  "https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf"

# Or using Python huggingface_hub (recommended)
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='TheBloke/Llama-3.2-3B-Instruct-GGUF',
    filename='llama-3.2-3b-instruct.Q4_K_M.gguf',
    local_dir='models/tier3',
    local_dir_use_symlinks=False
)
"
```

## Model Configuration

All model URLs and metadata are stored in:
- **`config/model-urls.json`** - Complete model database with URLs, sizes, and metadata

The `install-models.sh` script reads from this file automatically.

## Storage Locations

Models are stored in (checked in this order):
1. `models/tier[1-5]/model.gguf` (project root)
2. `~/.local/share/cosmic-os/models/tier[1-5]/model.gguf` (user install)
3. `/opt/cosmic-os/models/tier[1-5]/model.gguf` (system install)

The system automatically finds models in any of these locations.

## Why Not in Git?

- Models are 16GB+ total (too large for GitHub)
- Models are already on HuggingFace (standard ML practice)
- Auto-download is faster than cloning 16GB
- Users only download the tier they need
- Direct links allow manual download if scripts fail
