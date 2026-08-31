#!/usr/bin/env bash
# Smoke tests for scripts/sync-repo-wiring.sh. Runs offline; exits non-zero on the first failure.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/sync-repo-wiring.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

block_of() {
  sed -n '/cm-ai-content:managed:start/,/cm-ai-content:managed:end/p' "$1"
}

# Serve the managed block over file:// to exercise the remote (piped) mode without network.
mkdir -p "$WORK/raw/v1.0.0/instructions"
cp "$ROOT/instructions/AGENTS.md" "$WORK/raw/v1.0.0/instructions/"
export AI_ASSETS_BASE_URL="file://$WORK/raw"

echo "1. fresh portal, local mode"
mkdir -p "$WORK/p1"
"$SCRIPT" "$WORK/p1" >/dev/null
[ -f "$WORK/p1/AGENTS.md" ] || fail "AGENTS.md not created"
[ -f "$WORK/p1/CLAUDE.md" ] || fail "CLAUDE.md not created"
diff -q <(block_of "$WORK/p1/AGENTS.md") "$ROOT/instructions/AGENTS.md" >/dev/null || fail "block differs"
grep -qxF 'agents.lock' "$WORK/p1/.gitignore" || fail ".gitignore entry missing"
"$SCRIPT" --check "$WORK/p1" >/dev/null || fail "--check reports drift on a fresh install"
"$SCRIPT" "$WORK/p1" >/dev/null
[ "$(grep -c 'dotagents local state' "$WORK/p1/.gitignore")" = 1 ] || fail "re-run is not idempotent"

echo "2. existing AGENTS.md without markers is preserved below the block"
mkdir -p "$WORK/p2"
printf '# Portal\n\nOwn rules.\n' > "$WORK/p2/AGENTS.md"
"$SCRIPT" "$WORK/p2" >/dev/null
grep -q '^# Portal' "$WORK/p2/AGENTS.md" || fail "portal heading lost"
grep -q 'Own rules' "$WORK/p2/AGENTS.md" || fail "portal content lost"
head -n 1 "$WORK/p2/AGENTS.md" | grep -q 'managed:start' || fail "block not prepended"

echo "3. drift inside the block is detected and repaired; CRLF files are handled"
sed -i 's/$/\r/' "$WORK/p2/AGENTS.md"
sed -i '3s/.*/TAMPERED\r/' "$WORK/p2/AGENTS.md"
if "$SCRIPT" --check "$WORK/p2" >/dev/null; then fail "--check did not detect drift"; fi
"$SCRIPT" "$WORK/p2" >/dev/null
grep -q TAMPERED "$WORK/p2/AGENTS.md" && fail "drift not repaired"
grep -q '^# Portal' "$WORK/p2/AGENTS.md" || fail "portal content lost on repair"

echo "4. piped invocation with --ref (remote mode)"
mkdir -p "$WORK/p3"
bash -s -- --ref v1.0.0 "$WORK/p3" < "$SCRIPT" >/dev/null
diff -q <(block_of "$WORK/p3/AGENTS.md") "$ROOT/instructions/AGENTS.md" >/dev/null || fail "remote block differs"

echo "5. remote mode takes the release from agents.toml and rejects a mismatching AI_ASSETS_REF"
mkdir -p "$WORK/p4"
cp "$ROOT/examples/agents.toml" "$WORK/p4/"
bash -s -- "$WORK/p4" < "$SCRIPT" >/dev/null
if AI_ASSETS_REF=v9.9.9 bash -s -- "$WORK/p4" < "$SCRIPT" >/dev/null 2>&1; then fail "mismatching ref accepted"; fi

echo "6. remote mode without any release fails clearly"
mkdir -p "$WORK/p5"
if bash -s -- "$WORK/p5" < "$SCRIPT" >/dev/null 2>&1; then fail "missing ref accepted"; fi

echo "7. usage errors"
if "$SCRIPT" --bogus "$WORK/p1" >/dev/null 2>&1; then fail "unknown option accepted"; fi
if "$SCRIPT" >/dev/null 2>&1; then fail "missing target accepted"; fi

echo "OK: wiring tests passed"
