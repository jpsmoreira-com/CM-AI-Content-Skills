#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DASHBOARD_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DASHBOARD_ROOT="${DASHBOARD_ROOT:-$DEFAULT_DASHBOARD_ROOT}"
DASHBOARD_VENV="${DASHBOARD_VENV:-/home/vscode/.venvs/content-portals-dashboard}"

if [ ! -f "$DASHBOARD_ROOT/requirements.txt" ]; then
    echo "Content Portals Dashboard was not found at $DASHBOARD_ROOT"
    exit 0
fi

echo "Preparing Content Portals Dashboard environment..."
python3 -m venv "$DASHBOARD_VENV"
"$DASHBOARD_VENV/bin/python" -m pip install --upgrade pip
"$DASHBOARD_VENV/bin/python" -m pip install -r "$DASHBOARD_ROOT/requirements.txt"
