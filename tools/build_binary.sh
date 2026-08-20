#!/usr/bin/env bash
# Build a standalone Linux binary of the launcher with PyInstaller.
# Output: dist/vice-launcher
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .build-venv ]; then
    python3 -m venv .build-venv
    .build-venv/bin/pip install --upgrade pip pyinstaller
fi

.build-venv/bin/pyinstaller vice-launcher.spec

echo
echo "Built: dist/vice-launcher"
