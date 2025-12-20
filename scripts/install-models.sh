#!/bin/bash
# Model Installer for Cosmic OS (Real GGUF Downloads)

set -e

# Import jq if not available, we might need a python oneliner or just install jq
# For now, let's assume python3 is available since we set it up
PYTHON_CMD="python3 -c"

get_json_val() {
    python3 -c "import json, sys; print(json.load(open('config/model-urls.json'))['$1']['$2'])"
}

get_validator_url() {
    python3 -c "import json, sys; print(json.load(open('config/model-urls.json'))['$1']['validators']['$2'])"
}

if [ -f /tmp/cosmic_tier ]; then
    TIER_NUM=$(cat /tmp/cosmic_tier)
else
    # Default to tier 1 if detection hasn't run
     echo "Hardware detection not found. Defaulting to Tier 1."
     TIER_NUM=1
fi

TIER="tier$TIER_NUM"
MODEL_DIR="core/ai_engine/models/$TIER"
mkdir -p "$MODEL_DIR"

echo "Detected $TIER. Fetching model configuration..."

MAIN_URL=$(get_json_val $TIER "main")

echo "Downloading Main Model for $TIER..."
echo "URL: $MAIN_URL"

# Check if model already exists
if [ -f "$MODEL_DIR/model.gguf" ]; then
    echo "Model already exists. Skipping download (delete to re-download)."
else
    # Use wget with progress bar
    wget -O "$MODEL_DIR/model.gguf" "$MAIN_URL"
    echo "Main model downloaded."
fi

# Validators (Common for all tiers for now, but configured per tier in JSON)
VALIDATOR_DIR="core/ai_engine/models/validators"
mkdir -p "$VALIDATOR_DIR"

for v in safety logic efficiency; do
    echo "Downloading $v validator..."
    V_URL=$(get_validator_url $TIER $v)
    if [ ! -f "$VALIDATOR_DIR/$v.gguf" ]; then
         wget -O "$VALIDATOR_DIR/$v.gguf" "$V_URL"
    else
         echo "Validator $v exists."
    fi
done

echo "All models installed successfully."
