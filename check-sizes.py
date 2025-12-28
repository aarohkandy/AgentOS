#!/usr/bin/env python3
from pathlib import Path
import os

os.chdir(Path(__file__).parent)

print("=== Model File Sizes ===")
for tier in [1, 2, 3, 4]:
    p = Path(f"models/tier{tier}/model.gguf")
    if p.exists():
        size = p.stat().st_size
        if size > 1_000_000:
            print(f"✓ Tier {tier}: {size / (1024**2):.1f} MB")
        else:
            print(f"✗ Tier {tier}: {size} bytes (INCOMPLETE)")
    else:
        print(f"✗ Tier {tier}: NOT FOUND")

# Also check core/ai_engine/models
p = Path("core/ai_engine/models/tier3/model.gguf")
if p.exists():
    size = p.stat().st_size
    print(f"\ncore/ai_engine/models/tier3: {size / (1024**2):.1f} MB")

