#!/usr/bin/env bash
# .devcontainer/sync-ai-assets.sh for a documentation portal.
#
# 1. Skills and subagents: dotagents, driven by the committed agents.toml.
# 2. AGENTS.md managed block, CLAUDE.md stub, style guide copy: sync-repo-wiring.sh
#    from the same release the skills are pinned to.
set -euo pipefail

AI_ASSETS_REF="${AI_ASSETS_REF:-v0.4.0}"
DOTAGENTS_VERSION="${DOTAGENTS_VERSION:-3.0.1}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"
npx --yes "@sentry/dotagents@${DOTAGENTS_VERSION}" --project install

bash <(curl -fsSL "https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/${AI_ASSETS_REF}/scripts/sync-repo-wiring.sh") "$REPO_ROOT"
