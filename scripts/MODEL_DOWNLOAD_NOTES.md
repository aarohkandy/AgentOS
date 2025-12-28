# Model Download Notes

## Current Status

The 4-tier model system is implemented and ready. However, some HuggingFace repositories may require:
- Accepting terms of use on HuggingFace website
- HuggingFace account authentication
- Repository may be gated/private

## Manual Download Option

If automatic download fails, you can manually download models:

### Using HuggingFace CLI

1. Install: `pip3 install --break-system-packages --user huggingface-hub`
2. Login: `huggingface-cli login` (or use Python: `python3 -c "from huggingface_hub import login; login()"`)
3. Download models to `./models/tierX/model.gguf`

### Direct Download

Visit HuggingFace and download GGUF files directly, then place them in:
- `./models/tier1/model.gguf` (Tier 1)
- `./models/tier2/model.gguf` (Tier 2)  
- `./models/tier3/model.gguf` (Tier 3)
- `./models/tier4/model.gguf` (Tier 4)

## Model Recommendations

**Tier 1 (EXTREME Easy)**: TinyLlama 1.1B or Qwen 2.5 0.5B
**Tier 2 (Low)**: Llama 3.2 3B
**Tier 3 (Medium)**: Llama 3.1 8B or Qwen 2.5 7B
**Tier 4 (Very Powerful)**: Llama 3.1 70B

## Verification

After downloading models, verify with:
```bash
ls -lh ./models/tier*/model.gguf
anos --status
```

