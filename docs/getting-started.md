# Getting Started

End-to-end setup for every role: maintainers of this repository, portal repositories that consume the assets, and content writers using them day to day.

## What this repository provides

| Asset | What it is | How it reaches a portal |
| --- | --- | --- |
| `skills/` | On-demand workflows ([Agent Skills](https://code.claude.com/docs/en/skills): a folder with a `SKILL.md`) usable from Claude Code, Codex, and GitHub Copilot / VS Code | [dotagents](https://github.com/getsentry/dotagents), from the portal's committed `agents.toml` |
| `agents/` | Reusable subagents (`docs-style-reviewer`, `docs-link-auditor`) for delegated bulk review | dotagents `[[subagents]]` entries |
| `instructions/AGENTS.md` | Always-on shared rules (docs Markdown, protected/generated files, MkDocs config, Python automation) | `scripts/sync-repo-wiring.sh`, as a managed block inside the portal's [`AGENTS.md`](https://agents.md/) |
| `skills/style-guide-validator/references/style-guide-full.md` | The shared documentation style guide | bundled with the skill, plus a managed copy written by the wiring script |

## Prerequisites

- **Node.js 20+** — runs dotagents via `npx`. In a devcontainer add the [Node feature](https://containers.dev/features): `"ghcr.io/devcontainers/features/node:1": {}`.
- **Git and curl** — fetch the wiring script.
- An AI coding tool that supports Agent Skills: [Claude Code](https://code.claude.com/docs/en/skills), [Codex](https://developers.openai.com/codex/skills), or [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills).

## Setup 1 — a new portal repository (one-time, per repo)

From the portal root:

```bash
# 1. Declare the skills (writes agents.toml — commit it)
npx --yes @sentry/dotagents@3.0.1 --project init
npx --yes @sentry/dotagents@3.0.1 --project add usulpt/CM-AI-Content-Skills@v0.4.0

# 2. Install them (creates .agents/skills/ and the tool symlinks — gitignored)
npx --yes @sentry/dotagents@3.0.1 --project install

# 3. Install the shared rules, CLAUDE.md stub, and style guide
bash <(curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/v0.4.0/scripts/sync-repo-wiring.sh) .
```

Instead of steps 1–2 you can copy `examples/agents.toml` and edit the pinned tag.

Then wire it into the devcontainer so every writer gets the same setup automatically:

1. Copy `examples/sync-ai-assets.sh` to `.devcontainer/sync-ai-assets.sh`.
1. Add to `.devcontainer/devcontainer.json` (see `examples/devcontainer-pinned-ref.json` and the [devcontainer.json reference](https://containers.dev/implementors/json_reference/)):

```json
{
  "postCreateCommand": "bash .devcontainer/sync-ai-assets.sh",
  "remoteEnv": { "AI_ASSETS_REF": "v0.4.0" },
  "features": { "ghcr.io/devcontainers/features/node:1": {} }
}
```

1. Commit `agents.toml`, `AGENTS.md`, `CLAUDE.md`, `style-guide-full.md`, and the `.devcontainer/` changes.
1. Add portal-specific guidance to `AGENTS.md` **below** the `<!-- cm-ai-content:managed:end -->` marker — never inside the managed block.

Full details and the CI drift check: [consuming-from-devcontainers.md](consuming-from-devcontainers.md).

## Setup 2 — a writer's machine (usually nothing)

Inside a portal devcontainer, `postCreateCommand` does everything. Outside one, run the same three commands from Setup 1 in the portal checkout, or install the skills globally for all projects:

```bash
npx --yes @sentry/dotagents@3.0.1 add usulpt/CM-AI-Content-Skills@v0.4.0
npx --yes @sentry/dotagents@3.0.1 install
```

(Without `--project`, dotagents manages the global `~/.agents/` scope.)

## Setup 3 — working on this repository

```bash
npx --yes @sentry/dotagents@3.0.1 --project install   # link the local skills into the tool folders
bash scripts/validate-ai-assets.sh                    # before publishing
npx --yes @sentry/dotagents@3.0.1 --project doctor    # check dotagents state
```

Authoring rules, versioning, and the release flow: [publishing-and-versioning.md](publishing-and-versioning.md) and the root `AGENTS.md`.

## Daily use for writers

Skills load on demand — mention the task or invoke them directly:

| Task | Skill | Invoke |
| --- | --- | --- |
| Validate a file/folder against the style guide | `style-guide-validator` | `/style-guide-validator docs/module-x report` |
| Convert a DOCX/tutorial package to MkDocs pages | `tutorial-source-to-mkdocs` | `/tutorial-source-to-mkdocs <sources> <target folder>` |
| Draft a commit message, PR text, or changelog entry | `docs-change-summary` | `/docs-change-summary` |

For bulk work, delegate to the shared subagents instead of running everything in your main chat:

| Task | Subagent |
| --- | --- |
| Review a whole folder or PR against the style guide | `docs-style-reviewer` — e.g. "use the docs-style-reviewer agent on docs/module-x" |
| Sweep for broken links, missing/orphaned assets, `.pages` mismatches | `docs-link-auditor` — e.g. "run the docs-link-auditor on docs/" |

Both are read-only: they report findings and never edit files.

The always-on rules (don't touch generated files, MkDocs config only on explicit request, etc.) apply automatically through `AGENTS.md`; there is nothing to invoke.

## Reference documentation

**Contributing knowledge back**

The system compounds through use: if you correct the AI twice for the same thing, it belongs in this repository — see [`CONTRIBUTING.md`](../CONTRIBUTING.md) for where each kind of knowledge goes (style guide, glossary, golden examples, decision records) and how releases work.

**This repository**

- [consuming-from-devcontainers.md](consuming-from-devcontainers.md) — the consumer contract in detail
- [publishing-and-versioning.md](publishing-and-versioning.md) — releasing new asset versions
- [troubleshooting.md](troubleshooting.md) — common installation issues

**dotagents**

- [getsentry/dotagents](https://github.com/getsentry/dotagents) — README and source
- [dotagents guide](https://dotagents.sentry.dev/guide/) and [CLI reference](https://dotagents.sentry.dev/cli/)
- [Sentry docs: dotagents](https://docs.sentry.io/ai/dotagents/)
- [dotagents.io](https://dotagents.io/) — the `.agents/` directory convention

**Agent Skills and AGENTS.md**

- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills)
- [VS Code / GitHub Copilot: Use Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Codex: Build skills](https://developers.openai.com/codex/skills) and [openai/codex docs/skills.md](https://github.com/openai/codex/blob/main/docs/skills.md)
- [AGENTS.md convention](https://agents.md/)
- [Dev Container specification](https://containers.dev/implementors/json_reference/)
