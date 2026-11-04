#!/usr/bin/env bash
# SaveToken 1-Click Installer for macOS and Linux
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect Python interpreter
PY_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PY_BIN="$candidate"
        break
    fi
done

if [ -z "$PY_BIN" ]; then
    echo "Error: Python 3.10+ is required but not found on PATH." >&2
    exit 1
fi

"$PY_BIN" "$SCRIPT_DIR/scripts/install_antigravity.py"
