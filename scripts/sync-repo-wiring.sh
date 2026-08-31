#!/usr/bin/env bash
# Sync the repo-level AI wiring into a consuming repository (a documentation portal).
#
# Skills and subagents are NOT handled here — they are installed by dotagents from the
# portal's agents.toml (see docs/consuming-from-devcontainers.md). This script covers
# the pieces dotagents has no concept of:
#
#   instructions/AGENTS.md  -> managed block inside <repo>/AGENTS.md
#                                 (created if absent; only the block between the
#                                 cm-ai-content:managed markers is replaced, anything
#                                 outside it is the portal's own and is left alone)
#   CLAUDE.md                  -> generated stub when absent (points at AGENTS.md)
#   style-guide-full.md        -> managed copy of the bundled style guide
#
# Usage:
#   scripts/sync-repo-wiring.sh /path/to/PortalRepo            # install/update, report drift
#   scripts/sync-repo-wiring.sh --check /path/to/PortalRepo    # report only, exit 1 on drift/missing
#   scripts/sync-repo-wiring.sh --force /path/to/PortalRepo    # also overwrite a drifted style guide
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE="$REPO_ROOT/instructions/AGENTS.md"
STYLE_GUIDE="$REPO_ROOT/skills/style-guide-validator/references/style-guide-full.md"
START_MARK='<!-- cm-ai-content:managed:start -->'
END_MARK='<!-- cm-ai-content:managed:end -->'

MODE="sync"
case "${1:-}" in
    --check) MODE="check"; shift ;;
    --force) MODE="force"; shift ;;
esac
TARGET="${1:?usage: sync-repo-wiring.sh [--check|--force] /path/to/PortalRepo}"
[ -d "$TARGET" ] || { echo "ERROR: $TARGET is not a directory" >&2; exit 2; }
[ -f "$BASELINE" ] || { echo "ERROR: baseline not found: $BASELINE" >&2; exit 2; }

DRIFT=0

# --- AGENTS.md managed block ---------------------------------------------------------
agents_file="$TARGET/AGENTS.md"
if [ ! -f "$agents_file" ]; then
    if [ "$MODE" = "check" ]; then
        echo "MISSING: AGENTS.md"; DRIFT=1
    else
        {
            cat "$BASELINE"
            printf '\n## Repository-Specific Guidance\n\nAdd guidance that only applies to this repository below. This section is never touched by the sync.\n'
        } > "$agents_file"
        echo "installed: AGENTS.md (managed block + empty repository section)"
    fi
elif ! grep -qF "$START_MARK" "$agents_file" || ! grep -qF "$END_MARK" "$agents_file"; then
    if [ "$MODE" = "check" ]; then
        echo "MISSING: AGENTS.md has no managed block"; DRIFT=1
    else
        tmp="$(mktemp)"
        { cat "$BASELINE"; printf '\n'; cat "$agents_file"; } > "$tmp"
        mv "$tmp" "$agents_file"
        echo "installed: managed block prepended to existing AGENTS.md"
    fi
else
    current_block="$(awk -v s="$START_MARK" -v e="$END_MARK" '$0==s{p=1} p{print} $0==e{p=0}' "$agents_file")"
    if [ "$current_block" != "$(cat "$BASELINE")" ]; then
        if [ "$MODE" = "check" ]; then
            echo "DRIFT: AGENTS.md managed block"; DRIFT=1
        else
            tmp="$(mktemp)"
            awk -v s="$START_MARK" -v e="$END_MARK" -v b="$BASELINE" '
                $0==s { while ((getline line < b) > 0) print line; skip=1; next }
                $0==e { skip=0; next }
                !skip { print }
            ' "$agents_file" > "$tmp"
            mv "$tmp" "$agents_file"
            echo "updated: AGENTS.md managed block"
        fi
    fi
fi

# --- CLAUDE.md stub -------------------------------------------------------------------
if [ ! -f "$TARGET/CLAUDE.md" ]; then
    if [ "$MODE" = "check" ]; then
        echo "MISSING: CLAUDE.md"; DRIFT=1
    else
        cat > "$TARGET/CLAUDE.md" <<'STUB'
# CLAUDE.md

@AGENTS.md
STUB
        echo "installed: CLAUDE.md"
    fi
fi

# --- style guide copy -----------------------------------------------------------------
dest="$TARGET/style-guide-full.md"
if [ ! -f "$dest" ]; then
    if [ "$MODE" = "check" ]; then
        echo "MISSING: style-guide-full.md"; DRIFT=1
    else
        cp "$STYLE_GUIDE" "$dest"; echo "installed: style-guide-full.md"
    fi
elif ! diff -q "$STYLE_GUIDE" "$dest" >/dev/null; then
    if [ "$MODE" = "force" ]; then
        cp "$STYLE_GUIDE" "$dest"; echo "overwritten: style-guide-full.md"
    else
        echo "DRIFT (kept): style-guide-full.md"; DRIFT=1
    fi
fi

if [ "$DRIFT" = "0" ]; then
    echo "OK: wiring in sync."
else
    [ "$MODE" = "check" ] && exit 1
    echo "NOTE: drifted files were kept — merge portal improvements back into this repository or re-run with --force."
fi
