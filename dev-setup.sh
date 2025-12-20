#!/bin/bash
# Dev Setup

set -e
echo "Setting up dev environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
chmod +x scripts/*.sh core/system-config/*.sh

echo "Done."
