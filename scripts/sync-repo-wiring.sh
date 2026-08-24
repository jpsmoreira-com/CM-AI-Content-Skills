#!/usr/bin/env bash
# Sync the repo-level AI wiring into a consuming repository (a documentation portal):
#
#   ai/instructions/*.instructions.md -> <repo>/.github/instructions/
#   ai/instructions/*.prompt.md       -> <repo>/.github/prompts/
#   AGENTS.md / CLAUDE.md             -> generated stubs when absent
#
# Usage:
#   scripts/sync-repo-wiring.sh /path/to/PortalRepo            # install missing, report drift
#   scripts/sync-repo-wiring.sh --check /path/to/PortalRepo    # report only, exit 1 on drift/missing
#   scripts/sync-repo-wiring.sh --force /path/to/PortalRepo    # overwrite drifted files too
#
# Existing files that differ are NOT overwritten by default: portals are allowed to
# carry small repo-specific adjustments (extra applyTo globs, local style-guide
# links). Review reported drift and either merge it back here or --force.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/ai/instructions"

MODE="sync"
case "${1:-}" in
    --check) MODE="check"; shift ;;
    --force) MODE="force"; shift ;;
esac
TARGET="${1:?usage: sync-repo-wiring.sh [--check|--force] /path/to/PortalRepo}"
[ -d "$TARGET" ] || { echo "ERROR: $TARGET is not a directory" >&2; exit 2; }

DRIFT=0

sync_file() {
    local src="$1" dest="$2"
    if [ ! -f "$dest" ]; then
        if [ "$MODE" = "check" ]; then
            echo "MISSING: ${dest#"$TARGET"/}"
            DRIFT=1
        else
            mkdir -p "$(dirname "$dest")"
            cp "$src" "$dest"
            echo "installed: ${dest#"$TARGET"/}"
        fi
    elif ! diff -q "$src" "$dest" >/dev/null; then
        if [ "$MODE" = "force" ]; then
            cp "$src" "$dest"
            echo "overwritten: ${dest#"$TARGET"/}"
        else
            echo "DRIFT (kept): ${dest#"$TARGET"/}"
            DRIFT=1
        fi
    fi
}

for f in "$SRC"/*.instructions.md; do
    sync_file "$f" "$TARGET/.github/instructions/$(basename "$f")"
done
for f in "$SRC"/*.prompt.md; do
    sync_file "$f" "$TARGET/.github/prompts/$(basename "$f")"
done

# The style guide the skills and AGENTS.md reference — canonical copy lives with
# the style-guide-validator skill; consumer repos carry a managed copy.
sync_file "$REPO_ROOT/ai/skills/style-guide-validator/references/style-guide-full.md"     "$TARGET/style-guide-full.md"

if [ ! -f "$TARGET/AGENTS.md" ] && [ "$MODE" != "check" ]; then
    cat > "$TARGET/AGENTS.md" <<'EOF'
# AGENTS.md

## Purpose

This repository contains MkDocs documentation. AI agents assisting here must keep
changes minimal, preserve technical meaning and product terminology, and output
MkDocs-compatible Markdown.

## Repo-Wide Rules

- Prefer one topic per file; use relative Markdown links.
- Put images in a nearby `images/` folder.
- Do not update `mkdocs.yml` or other MkDocs config files unless explicitly requested.
- Do not edit generated output or indexes unless explicitly requested.

## Style And Validation

- Follow the repository style guide (`style-guide-full.md`) when present.
- Shared skills (style-guide-validator, tutorial-source-to-mkdocs, docs-change-summary)
  are installed by the devcontainer from CM-AI-Content-Skills; use them for
  validation, conversion, and change-summary work.
EOF
    echo "installed: AGENTS.md (stub — tailor it to this repository)"
fi

if [ ! -f "$TARGET/CLAUDE.md" ] && [ "$MODE" != "check" ]; then
    cat > "$TARGET/CLAUDE.md" <<'EOF'
# CLAUDE.md

Follow the rules in [AGENTS.md](AGENTS.md).

Shared documentation skills (style-guide-validator, tutorial-source-to-mkdocs,
docs-change-summary) are installed into `~/.claude/skills` by the devcontainer
post-create (from the CM-AI-Content-Skills repository).
EOF
    echo "installed: CLAUDE.md"
fi
if [ "$MODE" = "check" ]; then
    [ -f "$TARGET/AGENTS.md" ] || { echo "MISSING: AGENTS.md"; DRIFT=1; }
    [ -f "$TARGET/CLAUDE.md" ] || { echo "MISSING: CLAUDE.md"; DRIFT=1; }
fi

if [ "$DRIFT" = "0" ]; then
    echo "OK: wiring in sync."
else
    [ "$MODE" = "check" ] && exit 1
    echo "NOTE: drifted files were kept — merge portal improvements back into ai/instructions/ or re-run with --force."
fi
