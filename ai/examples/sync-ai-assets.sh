#!/usr/bin/env bash
set -euo pipefail

export AI_ASSETS_REPO_URL="https://github.com/usulpt/CM-AI-Content-Skills.git"
export AI_ASSETS_REF="${AI_ASSETS_REF:-main}"

bash <(curl -fsSL "https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/${AI_ASSETS_REF}/scripts/install-ai-assets.sh")
