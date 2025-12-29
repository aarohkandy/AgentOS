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

## Manual Download

Models are hosted on HuggingFace and downloaded automatically. The `install-models.sh` script handles:
- Detecting your hardware tier
- Downloading the appropriate model
- Verifying downloads
- Setting up model paths

## Model Tiers

| Tier | RAM | Model | Size |
|------|-----|-------|------|
| 1 | <2GB | TinyLlama 1.1B | ~640MB |
| 2 | 2-8GB | Llama 3.2 3B | ~2GB |
| 3 | 8-16GB | Qwen2.5 7B | ~4GB |
| 4 | 16GB+ | Llama 3.1 70B | ~40GB |

## Why Not in Git?

- Models are 16GB+ total (too large for GitHub)
- Models are already on HuggingFace (standard ML practice)
- Auto-download is faster than cloning 16GB
- Users only download the tier they need

## Storage Locations

Models are stored in:
- `models/tier[1-4]/model.gguf` (project root)
- Or `~/.local/share/cosmic-os/models/` (system install)

The system automatically finds models in either location.
