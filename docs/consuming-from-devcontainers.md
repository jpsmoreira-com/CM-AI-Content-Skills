# Consuming AI Assets from Devcontainers

A documentation portal consumes this repository in two steps that run from `postCreateCommand`:

1. **Skills and subagents** — installed by [dotagents](https://github.com/getsentry/dotagents) from a committed `agents.toml`.
2. **Shared rules** — a managed block in the root `AGENTS.md`, a `CLAUDE.md` stub, and `style-guide-full.md`, installed by `scripts/sync-repo-wiring.sh`.

Nothing else is written into the portal's working tree.

## 1. Skills with dotagents

Add an `agents.toml` to the portal root and commit it (copy `examples/agents.toml`):

```toml
version = 1
agents = ["claude", "codex", "vscode"]

[[skills]]
name = "style-guide-validator"
source = "usulpt/CM-AI-Content-Skills@v0.4.0"
```

Or let dotagents write it:

```bash
npx @sentry/dotagents --project init
npx @sentry/dotagents --project add usulpt/CM-AI-Content-Skills@v0.4.0
```

`install` then materialises the skills:

```bash
npx @sentry/dotagents --project install
```

It creates `.agents/skills/<name>/` and symlinks the tool-native folders (`.claude/skills`, `.codex/skills`, `.vscode/skills`) to it. `agents.lock`, `.agents/` and the symlinks are local state; dotagents adds them to `.gitignore` for you. Version pinning is the `@v0.4.0` in the source string — bump it in a reviewed PR.

`--project` is required: dotagents defaults to the user's global `~/.agents/` scope.

Requirements: Node.js 20+. Nothing else.

## 2. Shared rules with the wiring script

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/v0.4.0/scripts/sync-repo-wiring.sh) .
```

The script:

- creates `AGENTS.md` if absent, or inserts/updates the block between `<!-- cm-ai-content:managed:start -->` and `<!-- cm-ai-content:managed:end -->`. Everything outside the block is the portal's own and is never touched.
- creates `CLAUDE.md` (`@AGENTS.md`) if absent.
- copies `style-guide-full.md` if absent; a drifted copy is reported but kept unless `--force`.

`--check` reports drift and exits 1 without writing; use it in CI. Use the same tag for the script as for the skills in `agents.toml`.

## Devcontainer wiring

Direct, tracking `main`:

```json
{
  "postCreateCommand": "npx --yes @sentry/dotagents@3.0.1 --project install && bash <(curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/sync-repo-wiring.sh) ."
}
```

Pinned, through a wrapper (`examples/sync-ai-assets.sh` → `.devcontainer/sync-ai-assets.sh`):

```json
{
  "postCreateCommand": "bash .devcontainer/sync-ai-assets.sh",
  "remoteEnv": { "AI_ASSETS_REF": "v0.4.0" }
}
```

## Installed layout in a portal

```text
agents.toml                 committed
AGENTS.md                   committed — managed block + portal-specific sections
CLAUDE.md                   committed — "@AGENTS.md"
style-guide-full.md         committed — managed copy
.agents/skills/<name>/      local, gitignored
.claude/skills -> .agents/skills   local, gitignored (same for .codex, .vscode)
agents.lock                 local, gitignored
```

## Compatibility matrix

| Asset | Claude Code | Codex | GitHub Copilot / VS Code |
| --- | --- | --- | --- |
| `skills/*/SKILL.md` | `.claude/skills` (symlink) | `.agents/skills` | `.vscode/skills` / `.agents/skills` |
| Managed rules block | via `CLAUDE.md` → `AGENTS.md` | `AGENTS.md` | `AGENTS.md` |
| Subagents (`agents/`) | `.claude/agents` via `[[subagents]]` | — | — |

On-demand workflows are skills, invoked as `/skill-name` in every tool. There are no Copilot `.prompt.md` or path-scoped `.instructions.md` files; always-on guardrails live in the managed block.

## Legacy Bash installer

`scripts/install-ai-assets.sh` (user-level copies under `$HOME/.config/cm-ai-content` and `~/.{agents,copilot,claude}/skills`) still works against this layout but is deprecated and prints a warning. It will be removed in 0.5.0; migrate consumers to the two steps above.
