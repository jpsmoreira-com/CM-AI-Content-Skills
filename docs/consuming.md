# Consuming the Assets in a Portal

A documentation portal consumes this repository in two steps, both run from `postCreateCommand` in a devcontainer or by hand:

1. **Skills and subagents** — installed by [dotagents](https://github.com/getsentry/dotagents) from a committed `agents.toml`.
2. **Shared rules** — a managed block in the root `AGENTS.md` plus a `CLAUDE.md` stub, installed by `scripts/sync-repo-wiring.sh`.

Both are pinned to the same release tag: the wiring script reads the tag from `agents.toml`.

## Requirements

- Node.js 20+ (runs dotagents through `npx`). In a devcontainer: `"ghcr.io/devcontainers/features/node:1": {}`.
- `curl` for the wiring script (or vendor the script — see below).
- An AI tool that supports Agent Skills: [Claude Code](https://code.claude.com/docs/en/skills), [Codex](https://developers.openai.com/codex/skills), or [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills).

## 1. Skills and subagents with dotagents

Copy [`examples/agents.toml`](../examples/agents.toml) to the portal root and commit it:

```toml
version = 1
agents = ["claude", "codex", "copilot"]

[[skills]]
name = "*"
source = "jpsmoreira-com/CM-AI-Content-Skills@v1.0.0"

[[subagents]]
name = "docs-style-reviewer"
source = "jpsmoreira-com/CM-AI-Content-Skills@v1.0.0"
targets = ["claude", "codex"]

[[subagents]]
name = "docs-link-auditor"
source = "jpsmoreira-com/CM-AI-Content-Skills@v1.0.0"
targets = ["claude", "codex"]

[trust]
github_repos = ["jpsmoreira-com/CM-AI-Content-Skills"]
```

- `name = "*"` installs every skill the release publishes; subagents have no wildcard and are listed one by one.
- `@v1.0.0` is the version pin. Bump it in a reviewed PR to adopt a new release.
- `agents` names the tools to configure: `claude` gets `.claude/skills` (a symlink to `.agents/skills`) and `.claude/agents/*.md`; `codex` gets `.codex/agents/*.toml`. Codex and Copilot read `.agents/skills/` natively, so `copilot` writes no project files of its own — it declares the support that CI verifies, and selects `~/.copilot` if you ever install at user scope. There is no `vscode` id for skills; the `vscode` target covers MCP and hooks only.
- Subagent `targets` stay `["claude", "codex"]`. dotagents has no Copilot subagent format, so adding `"copilot"` there only produces `Agent "GitHub Copilot" does not support custom subagents`. Copilot gets the skills and the managed rules block — see [Compatibility](#compatibility).
- `[trust]` restricts sources to this repository.

Then install:

```bash
npx --yes @sentry/dotagents@3.1.0 --project install
```

`--project` is required — without it dotagents manages the user's global `~/.agents/` scope. The command writes `.agents/skills/<name>/`, the tool-native files, and `agents.lock`; all of it is local state. dotagents ignores `agents.lock` and `.agents/.gitignore` for you only when you run `init` or `doctor --fix`; the wiring script (step 2) adds those entries plus `.claude/skills`, `.claude/agents/`, and `.codex/agents/` to the portal's `.gitignore`, so a plain `install` is enough.

## 2. Shared rules with the wiring script

```bash
curl -fsSL https://raw.githubusercontent.com/jpsmoreira-com/CM-AI-Content-Skills/v1.0.0/scripts/sync-repo-wiring.sh | bash -s -- .
```

The script takes the release from the `@tag` in `agents.toml` (or from `--ref <tag>` / `AI_ASSETS_REF`; if both are present they must match) and fetches the managed block from that release. It then:

- creates `AGENTS.md` if absent, or inserts/updates the block between `<!-- cm-ai-content:managed:start -->` and `<!-- cm-ai-content:managed:end -->`. Everything outside the markers belongs to the portal and is never touched.
- creates `CLAUDE.md` containing `@AGENTS.md` if absent (never updated afterwards).
- appends the dotagents runtime entries to `.gitignore` once.

`--check` reports `MISSING`/`DRIFT` lines and exits 1 without writing; use it in the portal's CI to catch a stale block after a pin bump. If a portal must not fetch scripts at build time, vendor `scripts/sync-repo-wiring.sh` from the pinned tag into `.devcontainer/` and run it from there; it behaves the same.

## Devcontainer

[`examples/devcontainer.json`](../examples/devcontainer.json):

```json
{
  "features": { "ghcr.io/devcontainers/features/node:1": {} },
  "remoteEnv": { "AI_ASSETS_REF": "v1.0.0" },
  "postCreateCommand": "npx --yes @sentry/dotagents@3.1.0 --project install && curl -fsSL \"https://raw.githubusercontent.com/jpsmoreira-com/CM-AI-Content-Skills/${AI_ASSETS_REF}/scripts/sync-repo-wiring.sh\" | bash -s -- ."
}
```

`AI_ASSETS_REF` selects which copy of the script to fetch; the script then verifies it equals the pin in `agents.toml`, so the two cannot drift silently.

## What ends up in the portal

```text
agents.toml                     committed — the pin
AGENTS.md                       committed — managed block + portal-specific sections below it
CLAUDE.md                       committed — "@AGENTS.md"
.gitignore                      committed — dotagents runtime entries appended
.agents/skills/<name>/          local — installed skills (Codex and Copilot read these)
.agents/agents/<name>.md        local — portable subagents
.claude/skills -> .agents/skills   local — symlink for Claude Code
.claude/agents/<name>.md        local — Claude Code subagents
.codex/agents/<name>.toml       local — Codex subagents
agents.lock                     local — dotagents state
```

## Compatibility

| Asset | Claude Code | Codex | GitHub Copilot / VS Code |
| --- | --- | --- | --- |
| Skills | `.claude/skills` (symlink), invoked as `/name` | `.agents/skills`, invoked as `$name` | `.agents/skills`, invoked as `/name` |
| Subagents | `.claude/agents/*.md` | `.codex/agents/*.toml` | — |
| Managed rules block | `CLAUDE.md` → `AGENTS.md` | `AGENTS.md` | `AGENTS.md` |

## Updating to a new release

1. Change every `@vX.Y.Z` in `agents.toml` and `AI_ASSETS_REF` in `devcontainer.json` to the new tag.
2. Rebuild the devcontainer, or run the two commands above by hand.
3. Review the diff of `AGENTS.md` (the managed block may have changed) and commit.

Release notes live on the [GitHub Releases](https://github.com/jpsmoreira-com/CM-AI-Content-Skills/releases) page and in `CHANGELOG.md`.
