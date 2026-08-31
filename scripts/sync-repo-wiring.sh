#!/usr/bin/env bash
# Install or update the repo-level AI wiring in a consuming repository (a documentation portal).
#
# Skills and subagents are installed by dotagents from the portal's agents.toml. This script
# covers what dotagents has no concept of:
#
#   instructions/AGENTS.md -> managed block inside <portal>/AGENTS.md (created if absent;
#                             only the block between the cm-ai-content:managed markers is
#                             replaced, everything outside it belongs to the portal)
#   CLAUDE.md              -> created once when absent (contains "@AGENTS.md")
#   .gitignore             -> the dotagents runtime entries, appended once when missing
#
# Usage:
#   sync-repo-wiring.sh [--check] [--ref <tag>] <portal-dir>
#
#   --check        report drift and exit 1 without writing anything (for CI)
#   --ref <tag>    release to fetch the managed block from (same as AI_ASSETS_REF)
#
# Run from a checkout of CM-AI-Content-Skills, the block comes from that checkout. Run remotely
# (curl ... | bash -s -- <portal-dir>), it is fetched from GitHub at the pinned release. The
# release is taken from --ref / AI_ASSETS_REF, or from the @tag in the portal's agents.toml;
# when both are present they must match, so rules and skills never drift apart.
#
# Environment:
#   AI_ASSETS_REF        release tag (see above)
#   AI_ASSETS_REPO       GitHub repository, default usulpt/CM-AI-Content-Skills
#   AI_ASSETS_BASE_URL   raw-content base URL, default https://raw.githubusercontent.com/$AI_ASSETS_REPO
set -euo pipefail

START_MARK='<!-- cm-ai-content:managed:start -->'
END_MARK='<!-- cm-ai-content:managed:end -->'
AI_ASSETS_REPO="${AI_ASSETS_REPO:-usulpt/CM-AI-Content-Skills}"
AI_ASSETS_BASE_URL="${AI_ASSETS_BASE_URL:-https://raw.githubusercontent.com/$AI_ASSETS_REPO}"
GITIGNORE_ENTRIES=(agents.lock .agents/.gitignore .claude/skills .claude/agents/ .codex/agents/)

usage() {
  sed -n '2,/^set -euo/p' "$0" 2>/dev/null | sed '$d' | sed 's/^# \{0,1\}//'
}

die() {
  echo "ERROR: $*" >&2
  exit 2
}

MODE="sync"
REF="${AI_ASSETS_REF:-}"
TARGET=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --ref) [ $# -ge 2 ] || die "--ref needs a value"; REF="$2"; shift ;;
    --ref=*) REF="${1#--ref=}" ;;
    -h | --help) usage; exit 0 ;;
    --*) die "unknown option: $1" ;;
    *) [ -z "$TARGET" ] || die "unexpected argument: $1"; TARGET="$1" ;;
  esac
  shift
done
[ -n "$TARGET" ] || die "usage: sync-repo-wiring.sh [--check] [--ref <tag>] <portal-dir>"
[ -d "$TARGET" ] || die "$TARGET is not a directory"

# --- locate the managed block -----------------------------------------------------------
tmp_dir=""
cleanup() { [ -z "$tmp_dir" ] || rm -rf "$tmp_dir"; }
trap cleanup EXIT

# The @tag pinned in the portal's agents.toml, if any (source = "owner/repo@tag" or ref = "tag").
portal_ref() {
  local toml="$TARGET/agents.toml"
  [ -f "$toml" ] || return 0
  sed -n -E 's/^[[:space:]]*source[[:space:]]*=[[:space:]]*"[^"@]*CM-AI-Content-Skills@([^"]+)".*/\1/p; s/^[[:space:]]*ref[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$toml" | sort -u
}

script_dir=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

if [ -n "$script_dir" ] && [ -f "$script_dir/../instructions/AGENTS.md" ]; then
  BASELINE="$(cd "$script_dir/.." && pwd)/instructions/AGENTS.md"
  SOURCE_DESC="local checkout"
else
  pinned="$(portal_ref)"
  if [ "$(printf '%s\n' "$pinned" | grep -c .)" -gt 1 ]; then
    die "agents.toml in $TARGET pins more than one release: $(printf '%s ' "$pinned")"
  fi
  if [ -n "$REF" ] && [ -n "$pinned" ] && [ "$REF" != "$pinned" ]; then
    die "AI_ASSETS_REF is $REF but agents.toml pins $pinned; use the same release for rules and skills"
  fi
  REF="${REF:-$pinned}"
  [ -n "$REF" ] || die "no release given: pass --ref <tag>, set AI_ASSETS_REF, or pin CM-AI-Content-Skills@<tag> in $TARGET/agents.toml"
  command -v curl >/dev/null 2>&1 || die "curl is required to fetch the managed block"
  tmp_dir="$(mktemp -d)"
  BASELINE="$tmp_dir/AGENTS.md"
  url="$AI_ASSETS_BASE_URL/$REF/instructions/AGENTS.md"
  curl -fsSL "$url" -o "$BASELINE" || die "could not fetch $url"
  SOURCE_DESC="$AI_ASSETS_REPO@$REF"
fi

head -n 1 "$BASELINE" | grep -qF "$START_MARK" || die "managed block from $SOURCE_DESC does not start with the start marker"
tail -n 1 "$BASELINE" | grep -qF "$END_MARK" || die "managed block from $SOURCE_DESC does not end with the end marker"

DRIFT=0
report() { echo "$1: $2"; DRIFT=1; }

# --- AGENTS.md ------------------------------------------------------------------------
agents_file="$TARGET/AGENTS.md"
write_file() { # write_file <path> <content-producing function>
  local path="$1" tmp
  tmp="$(mktemp "$path.XXXXXX")"
  "$2" > "$tmp"
  mv "$tmp" "$path"
}
emit_new_agents() {
  cat "$BASELINE"
  printf '\n## Repository-Specific Guidance\n\nAdd guidance that only applies to this repository below. This section is never touched by the sync.\n'
}
emit_prepended_agents() {
  cat "$BASELINE"
  printf '\n'
  tr -d '\r' < "$agents_file"
}
emit_updated_agents() {
  tr -d '\r' < "$agents_file" | awk -v s="$START_MARK" -v e="$END_MARK" -v b="$BASELINE" '
    $0==s { while ((getline line < b) > 0) print line; skip=1; next }
    $0==e { skip=0; next }
    !skip { print }
  '
}

if [ ! -f "$agents_file" ]; then
  if [ "$MODE" = "check" ]; then
    report MISSING "AGENTS.md"
  else
    write_file "$agents_file" emit_new_agents
    echo "installed: AGENTS.md (managed block + empty repository section)"
  fi
elif ! grep -qF "$START_MARK" "$agents_file" || ! grep -qF "$END_MARK" "$agents_file"; then
  if [ "$MODE" = "check" ]; then
    report MISSING "AGENTS.md has no managed block"
  else
    write_file "$agents_file" emit_prepended_agents
    echo "installed: managed block prepended to existing AGENTS.md"
  fi
else
  current_block="$(tr -d '\r' < "$agents_file" | awk -v s="$START_MARK" -v e="$END_MARK" '$0==s{p=1} p{print} $0==e{p=0}')"
  if [ "$current_block" != "$(cat "$BASELINE")" ]; then
    if [ "$MODE" = "check" ]; then
      report DRIFT "AGENTS.md managed block (expected $SOURCE_DESC)"
    else
      write_file "$agents_file" emit_updated_agents
      echo "updated: AGENTS.md managed block ($SOURCE_DESC)"
    fi
  fi
fi

# --- CLAUDE.md (created once, never updated) ----------------------------------------------
if [ ! -f "$TARGET/CLAUDE.md" ]; then
  if [ "$MODE" = "check" ]; then
    report MISSING "CLAUDE.md"
  else
    printf '# CLAUDE.md\n\n@AGENTS.md\n' > "$TARGET/CLAUDE.md"
    echo "installed: CLAUDE.md"
  fi
fi

# --- .gitignore: dotagents runtime state ------------------------------------------------------
gitignore="$TARGET/.gitignore"
missing=()
for entry in "${GITIGNORE_ENTRIES[@]}"; do
  if [ ! -f "$gitignore" ] || ! grep -qxF -- "$entry" "$gitignore"; then
    missing+=("$entry")
  fi
done
if [ "${#missing[@]}" -gt 0 ]; then
  if [ "$MODE" = "check" ]; then
    report MISSING ".gitignore entries: ${missing[*]}"
  else
    lead=""
    if [ -s "$gitignore" ] && [ "$(tail -c 1 "$gitignore")" != "" ]; then lead="\n"; fi
    {
      printf '%b\n# dotagents local state (managed by CM-AI-Content-Skills wiring)\n' "$lead"
      printf '%s\n' "${missing[@]}"
    } >> "$gitignore"
    echo "updated: .gitignore (${missing[*]})"
  fi
fi

if [ "$DRIFT" = "0" ]; then
  echo "OK: wiring in sync with $SOURCE_DESC."
else
  exit 1
fi
