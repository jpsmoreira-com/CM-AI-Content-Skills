#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AI_DIR="$ROOT_DIR/ai"
MANIFEST="$AI_DIR/manifest.json"

failures=0

info() {
  printf '[validate-ai-assets] %s\n' "$*"
}

error() {
  printf '[validate-ai-assets] ERROR: %s\n' "$*" >&2
  failures=$((failures + 1))
}

require_path() {
  if [ ! -e "$1" ]; then
    error "Missing required path: ${1#$ROOT_DIR/}"
  fi
}

check_skill_metadata() {
  local skill_dir="$1"
  local skill_file="$skill_dir/SKILL.md"
  local skill_name

  skill_name="$(basename "$skill_dir")"

  if [ ! -f "$skill_file" ]; then
    error "Skill '$skill_name' is missing SKILL.md"
    return
  fi

  if ! awk 'BEGIN { in_meta=0; found=0 } /^---[[:space:]]*$/ { if (in_meta == 0) { in_meta=1; next } else { exit } } in_meta == 1 && /^name:[[:space:]]*/ { found=1 } END { exit(found ? 0 : 1) }' "$skill_file"; then
    error "Skill '$skill_name' SKILL.md is missing name metadata"
  fi

  if ! awk 'BEGIN { in_meta=0; found=0 } /^---[[:space:]]*$/ { if (in_meta == 0) { in_meta=1; next } else { exit } } in_meta == 1 && /^description:[[:space:]]*/ { found=1 } END { exit(found ? 0 : 1) }' "$skill_file"; then
    error "Skill '$skill_name' SKILL.md is missing description metadata"
  fi
}

check_manifest_json() {
  if command -v jq >/dev/null 2>&1; then
    if ! jq empty "$MANIFEST" >/dev/null; then
      error "ai/manifest.json is not valid JSON"
    fi
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    if ! python3 -m json.tool "$MANIFEST" >/dev/null; then
      error "ai/manifest.json is not valid JSON"
    fi
    return
  fi

  error "Cannot validate manifest JSON because jq and python3 are missing"
}

manifest_values() {
  local query="$1"

  if command -v jq >/dev/null 2>&1; then
    jq -r "$query" "$MANIFEST"
    return
  fi

  python3 - "$MANIFEST" "$query" <<'PY'
import json
import sys

manifest_path, query = sys.argv[1], sys.argv[2]
with open(manifest_path, encoding="utf-8") as handle:
    data = json.load(handle)

if query.endswith("[].path"):
    section = query.split("[", 1)[0].lstrip(".")
    field = "path"
elif query.endswith("[].name"):
    section = query.split("[", 1)[0].lstrip(".")
    field = "name"
elif query == ".skills[].references[]?":
    for item in data.get("skills", []):
        for value in item.get("references", []):
            print(value)
    sys.exit(0)
else:
    sys.exit(0)

for item in data.get(section, []):
    value = item.get(field)
    if value:
        print(value)
PY
}

manifest_has_path() {
  local expected_path="$1"
  local query="$2"

  manifest_values "$query" | grep -Fx -- "$expected_path" >/dev/null 2>&1
}

check_manifest_paths() {
  local path
  local target

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if [ ! -e "$AI_DIR/$path" ]; then
      error "Manifest entry points to missing path: ai/$path"
    fi
  done < <(manifest_values '.agents[].path')

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if [ ! -d "$AI_DIR/$path" ]; then
      error "Manifest skill entry is not a directory: ai/$path"
    fi
  done < <(manifest_values '.skills[].path')

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if [ ! -f "$AI_DIR/$path" ]; then
      error "Manifest instruction entry is not a file: ai/$path"
    fi
  done < <(manifest_values '.instructions[].path')

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if [ ! -e "$AI_DIR/$path" ]; then
      error "Manifest skill reference points to missing path: ai/$path"
    fi
  done < <(manifest_values '.skills[].references[]?')

  for target in base codex copilot claude; do
    if ! manifest_values '.install_targets[].name' | grep -Fx -- "$target" >/dev/null 2>&1; then
      error "Manifest is missing install target: $target"
    fi
  done

  while IFS= read -r -d '' skill_dir; do
    path="skills/$(basename "$skill_dir")"
    if ! manifest_has_path "$path" '.skills[].path'; then
      error "Skill directory is missing from manifest: ai/$path"
    fi
  done < <(find "$AI_DIR/skills" -mindepth 1 -maxdepth 1 -type d -print0)

  while IFS= read -r -d '' instruction_file; do
    path="instructions/$(basename "$instruction_file")"
    if ! manifest_has_path "$path" '.instructions[].path'; then
      error "Instruction file is missing from manifest: ai/$path"
    fi
  done < <(find "$AI_DIR/instructions" -mindepth 1 -maxdepth 1 -type f -name '*.md' -print0)

  while IFS= read -r -d '' agent_file; do
    path="agents/$(basename "$agent_file")"
    if ! manifest_has_path "$path" '.agents[].path'; then
      error "Agent file is missing from manifest: ai/$path"
    fi
  done < <(find "$AI_DIR/agents" -mindepth 1 -maxdepth 1 -type f ! -name 'README.md' -print0)
}

check_secret_patterns() {
  local findings

  findings="$(
    grep -RInE \
      --exclude-dir=.git \
      --exclude='validate-ai-assets.sh' \
      '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|(password|passwd|secret|api[_-]?key|token)[[:space:]]*[:=][[:space:]]*["'\'']?[A-Za-z0-9_./+=-]{12,})' \
      "$AI_DIR" 2>/dev/null || true
  )"

  if [ -n "$findings" ]; then
    error "Possible secret patterns found:"
    printf '%s\n' "$findings" >&2
  fi
}

main() {
  require_path "$AI_DIR"
  require_path "$AI_DIR/agents"
  require_path "$AI_DIR/skills"
  require_path "$AI_DIR/instructions"
  require_path "$AI_DIR/examples"
  require_path "$MANIFEST"
  require_path "$AI_DIR/README.md"
  require_path "$AI_DIR/CHANGELOG.md"
  require_path "$AI_DIR/skills/style-guide-validator/references/style-guide-full.md"
  require_path "$AI_DIR/docs/consuming-from-devcontainers.md"
  require_path "$AI_DIR/docs/publishing-and-versioning.md"
  require_path "$AI_DIR/docs/troubleshooting.md"

  check_manifest_json

  if [ -d "$AI_DIR/skills" ]; then
    while IFS= read -r -d '' skill_dir; do
      check_skill_metadata "$skill_dir"
    done < <(find "$AI_DIR/skills" -mindepth 1 -maxdepth 1 -type d -print0)
  fi

  check_manifest_paths
  check_secret_patterns

  if [ "$failures" -gt 0 ]; then
    fail_count="$failures"
    printf '[validate-ai-assets] Failed with %s issue(s).\n' "$fail_count" >&2
    exit 1
  fi

  info "AI assets validation passed."
}

main "$@"
