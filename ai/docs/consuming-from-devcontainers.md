# Consuming AI Assets from Devcontainers

Use the public AI assets repository to install shared skills, agents, instructions, and examples into a devcontainer without copying those files into every consuming repository.

The installer writes to `$HOME/.config/cm-ai-content` by default. It also installs shared skills into Codex, GitHub Copilot, and Claude Code user-level skill folders. It does not write generated assets into the consuming repository working tree.

## Direct `curl` from `postCreateCommand`

Add a `postCreateCommand` to `.devcontainer/devcontainer.json`:

```json
{
  "postCreateCommand": "curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | bash"
}
```

Use this form when the consuming repository can track the latest `main` version of the public asset repository.

By default, this installs all supported targets:

- base content under `$HOME/.config/cm-ai-content`
- Codex-compatible skills under `$HOME/.agents/skills`
- GitHub Copilot skills under `$HOME/.copilot/skills`
- Claude Code skills under `$HOME/.claude/skills`

## Pinned Version or Tag

Pin consumers to a stable release tag when repeatable builds matter:

```json
{
  "postCreateCommand": "curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/v0.1.0/scripts/install-ai-assets.sh | AI_ASSETS_REF=v0.1.0 bash"
}
```

In this pattern, both the downloaded installer and fetched asset content are pinned to the same release tag.

## Local Wrapper Script

Create `.devcontainer/sync-ai-assets.sh` in the consuming repository:

```bash
#!/usr/bin/env bash
set -euo pipefail

export AI_ASSETS_REPO_URL="https://github.com/usulpt/CM-AI-Content-Skills.git"
export AI_ASSETS_REF="${AI_ASSETS_REF:-main}"

bash <(curl -fsSL "https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/${AI_ASSETS_REF}/scripts/install-ai-assets.sh")
```

Then call the wrapper from `.devcontainer/devcontainer.json`:

```json
{
  "postCreateCommand": "bash .devcontainer/sync-ai-assets.sh"
}
```

## Installer Settings

The installer supports these environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `AI_ASSETS_REPO_URL` | `https://github.com/usulpt/CM-AI-Content-Skills.git` | Public Git repository to fetch. |
| `AI_ASSETS_REF` | `main` | Branch, tag, or commit-ish to install. |
| `AI_ASSETS_PATH` | `ai` | Path to the asset library inside the repository. |
| `AI_INSTALL_DIR` | `$HOME/.config/cm-ai-content` | Destination for installed assets. |
| `AI_CACHE_DIR` | `$HOME/.cache/cm-ai-content-skills` | Temporary clone/cache location. |
| `AI_INSTALL_TARGETS` | `all` | Comma-separated targets: `all`, `base`, `codex`, `copilot`, `claude`. |

## Targeted Installs

Install only Codex-compatible content:

```json
{
  "postCreateCommand": "curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | AI_INSTALL_TARGETS=codex bash"
}
```

Install only GitHub Copilot and Claude Code skills:

```json
{
  "postCreateCommand": "curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | AI_INSTALL_TARGETS=copilot,claude bash"
}
```

## Installed Layout

After the base installation, consumers receive:

```text
$AI_INSTALL_DIR/
  agents/
  skills/
  instructions/
  examples/
  manifest.json
```

Shared skills are also copied to tool-native user folders when their target is enabled:

```text
$HOME/.agents/skills/
$HOME/.copilot/skills/
$HOME/.claude/skills/
```

## Compatibility Matrix

| Asset type | Codex | GitHub Copilot | Claude Code |
| --- | --- | --- | --- |
| `ai/skills/*/SKILL.md` | Shared skill source | Shared skill source | Shared skill source |
| `AGENTS.md` | Repository guidance | Useful context when supported | Use `CLAUDE.md` for native memory |
| `.github/copilot-instructions.md` | Not native | Repository-wide instructions | Not native |
| `.github/instructions/*.instructions.md` | Not native | Path-specific instructions | Not native |
| `CLAUDE.md` | Not native | Not native | Project or user memory |

This installer keeps consuming repositories home-only by default. If a repository needs Copilot cloud instructions or Claude project memory, add a small repository-owned wrapper or checked-in file that references this shared source.
