#!/usr/bin/env bash
set -euo pipefail

INSTALLER_VERSION="0.1.0"

AI_ASSETS_REPO_URL="${AI_ASSETS_REPO_URL:-https://github.com/usulpt/CM-AI-Content-Skills.git}"
AI_ASSETS_REF="${AI_ASSETS_REF:-main}"
AI_ASSETS_PATH="${AI_ASSETS_PATH:-ai}"
AI_INSTALL_DIR="${AI_INSTALL_DIR:-$HOME/.config/cm-ai-content}"
AI_CACHE_DIR="${AI_CACHE_DIR:-$HOME/.cache/cm-ai-content-skills}"
AI_INSTALL_TARGETS="${AI_INSTALL_TARGETS:-all}"

log() {
  printf '[cm-ai-content-skills] %s\n' "$*"
}

fail() {
  printf '[cm-ai-content-skills] ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "$1 is required but was not found. Install $1 in the devcontainer image or feature configuration."
  fi
}

copy_tree() {
  local source_dir="$1"
  local target_dir="$2"

  mkdir -p "$target_dir"

  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "$source_dir"/ "$target_dir"/
    return
  fi

  rm -rf "$target_dir"
  mkdir -p "$(dirname "$target_dir")"
  cp -a "$source_dir" "$target_dir"
}

sync_owned_children() {
  local source_dir="$1"
  local target_dir="$2"
  local ownership_file="$target_dir/.cm-ai-content-skills.installed"
  local current_file
  local previous_name
  local child
  local child_name

  mkdir -p "$target_dir"
  current_file="$(mktemp)"

  shopt -s nullglob
  for child in "$source_dir"/*; do
    child_name="$(basename "$child")"
    printf '%s\n' "$child_name" >>"$current_file"
    copy_tree "$child" "$target_dir/$child_name"
  done
  shopt -u nullglob

  if [ -f "$ownership_file" ]; then
    while IFS= read -r previous_name; do
      [ -n "$previous_name" ] || continue
      if ! grep -Fx -- "$previous_name" "$current_file" >/dev/null 2>&1; then
        rm -rf "$target_dir/$previous_name"
      fi
    done <"$ownership_file"
  fi

  sort -u "$current_file" >"$ownership_file"
  rm -f "$current_file"
}

target_enabled() {
  local requested_target="$1"
  local target
  local targets_csv

  targets_csv=",$(printf '%s' "$AI_INSTALL_TARGETS" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]'),"

  if [[ "$targets_csv" == *",all,"* ]]; then
    return 0
  fi

  IFS=',' read -ra targets <<<"${targets_csv#,}"
  for target in "${targets[@]}"; do
    target="${target%,}"
    if [ "$target" = "$requested_target" ]; then
      return 0
    fi
  done

  return 1
}

validate_targets() {
  local target
  local targets_csv

  targets_csv="$(printf '%s' "$AI_INSTALL_TARGETS" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"

  if [ -z "$targets_csv" ]; then
    fail "AI_INSTALL_TARGETS cannot be empty. Use all, base, codex, copilot, or claude."
  fi

  IFS=',' read -ra targets <<<"$targets_csv"
  for target in "${targets[@]}"; do
    case "$target" in
      all | base | codex | copilot | claude) ;;
      *) fail "Unsupported AI_INSTALL_TARGETS value '$target'. Use all, base, codex, copilot, or claude." ;;
    esac
  done
}

clone_assets() {
  local clone_dir="$1"

  rm -rf "$clone_dir"
  mkdir -p "$(dirname "$clone_dir")"

  log "Fetching ${AI_ASSETS_REPO_URL} at ${AI_ASSETS_REF}"

  if git clone --depth 1 --filter=blob:none --sparse --branch "$AI_ASSETS_REF" "$AI_ASSETS_REPO_URL" "$clone_dir" >/dev/null 2>&1; then
    if git -C "$clone_dir" sparse-checkout set "$AI_ASSETS_PATH" >/dev/null 2>&1; then
      return
    fi

    log "Sparse checkout failed; retrying with a regular shallow clone"
  fi

  rm -rf "$clone_dir"
  if ! git clone --depth 1 --branch "$AI_ASSETS_REF" "$AI_ASSETS_REPO_URL" "$clone_dir" >/dev/null 2>&1; then
    fail "Could not fetch repository, ref, or tag. Check AI_ASSETS_REPO_URL=${AI_ASSETS_REPO_URL} and AI_ASSETS_REF=${AI_ASSETS_REF}."
  fi
}

validate_source() {
  local assets_dir="$1"

  if [ ! -d "$assets_dir" ]; then
    fail "Asset path '${AI_ASSETS_PATH}' was not found in the fetched repository."
  fi

  for required_path in agents skills instructions examples; do
    if [ ! -d "$assets_dir/$required_path" ]; then
      fail "Required folder '$AI_ASSETS_PATH/$required_path' is missing."
    fi
  done

  if [ ! -f "$assets_dir/manifest.json" ]; then
    fail "Required file '$AI_ASSETS_PATH/manifest.json' is missing."
  fi
}

install_assets() {
  local assets_dir="$1"

  if ! target_enabled base; then
    return
  fi

  mkdir -p "$AI_INSTALL_DIR"

  copy_tree "$assets_dir/agents" "$AI_INSTALL_DIR/agents"
  copy_tree "$assets_dir/skills" "$AI_INSTALL_DIR/skills"
  copy_tree "$assets_dir/instructions" "$AI_INSTALL_DIR/instructions"
  copy_tree "$assets_dir/examples" "$AI_INSTALL_DIR/examples"
  cp "$assets_dir/manifest.json" "$AI_INSTALL_DIR/manifest.json"
}

install_skill_targets() {
  local assets_dir="$1"
  local installed_targets=()

  if target_enabled codex; then
    sync_owned_children "$assets_dir/skills" "$HOME/.agents/skills"
    installed_targets+=("$HOME/.agents/skills")
  fi

  if target_enabled copilot; then
    sync_owned_children "$assets_dir/skills" "$HOME/.copilot/skills"
    installed_targets+=("$HOME/.copilot/skills")
  fi

  if target_enabled claude; then
    sync_owned_children "$assets_dir/skills" "$HOME/.claude/skills"
    installed_targets+=("$HOME/.claude/skills")
  fi

  if [ "${#installed_targets[@]}" -gt 0 ]; then
    log "Installed shared skills to: ${installed_targets[*]}"
  fi
}

main() {
  require_command git

  local clone_dir="$AI_CACHE_DIR/source"
  local assets_dir="$clone_dir/$AI_ASSETS_PATH"

  log "Installer version ${INSTALLER_VERSION}"
  validate_targets
  clone_assets "$clone_dir"
  validate_source "$assets_dir"
  install_assets "$assets_dir"
  install_skill_targets "$assets_dir"

  if target_enabled base; then
    log "Installed AI assets to ${AI_INSTALL_DIR}"
    log "Installed manifest:"
    cat "$AI_INSTALL_DIR/manifest.json"
  else
    log "Base install skipped because AI_INSTALL_TARGETS=${AI_INSTALL_TARGETS}"
  fi
}

main "$@"
