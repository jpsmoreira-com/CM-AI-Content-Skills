# CM AI Content Skills

Reusable public AI assets for the content-writing team: skills, subagents, and shared rules that documentation portals consume without copying repository-specific guidance into each one.

## Contents

- `skills/` — shared skills for Claude Code, Codex, and GitHub Copilot / VS Code (one directory per skill, with `SKILL.md`).
- `agents/` — reusable subagents: `docs-style-reviewer` and `docs-link-auditor` for delegated, read-only bulk review.
- `instructions/AGENTS.md` — the managed rules block synced into each consumer's root `AGENTS.md`.
- `examples/` — consumer examples (`agents.toml`, devcontainer snippets, wrapper script).
- `manifest.json` — machine-readable asset inventory.
- `docs/` — consumer, publishing, and troubleshooting guides.
- `agents.toml` — this repository's own [dotagents](https://github.com/getsentry/dotagents) manifest.
- `scripts/sync-repo-wiring.sh` — installs the managed `AGENTS.md` block, a `CLAUDE.md` stub, and the style guide into a consumer.
- `scripts/validate-ai-assets.sh` — validates the asset layout before publishing.
- `scripts/install-ai-assets.sh` — **deprecated** Bash installer, kept for existing consumers until 0.5.0.
- `evals/` — regression fixtures for skills and agents (maintainers only, not shipped).
- `docs/decisions/` — decision records: the why behind rules.
- `CONTRIBUTING.md` — how team knowledge flows back into this repository.

Internal tools that consume these assets (such as the TFS documentation automation pipeline) live in the separate `CM-AI-Content-Tools` repository.

## How consumers use it

Skills and subagents are installed with dotagents. In a portal repository:

```bash
npx @sentry/dotagents --project init
npx @sentry/dotagents --project add usulpt/CM-AI-Content-Skills@v0.4.0
```

That writes `agents.toml` (commit it) and links the skills into `.agents/skills/`, `.claude/skills/`, and the other tool folders (local state, gitignored).

Shared rules are installed with the wiring script:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/v0.4.0/scripts/sync-repo-wiring.sh) .
```

Wire both into the devcontainer `postCreateCommand` — see `examples/` and `docs/consuming-from-devcontainers.md`.

## Work on assets

1. Put reusable skills under `skills/` and register them in `manifest.json` and `agents.toml`.
1. Put reusable subagents under `agents/`.
1. Put always-on rules in the managed block in `instructions/AGENTS.md`; put on-demand workflows in skills.
1. Update `CHANGELOG.md`.
1. Run validation before publishing.

```bash
bash scripts/validate-ai-assets.sh
npx @sentry/dotagents --project install && npx @sentry/dotagents --project doctor
shellcheck scripts/*.sh
```

## Public Content Rules

Keep all shared content safe to publish. Do not include secrets, internal URLs, customer data, private credentials, proprietary information, or environment-specific tokens.

Use neutral placeholders such as `usulpt/CM-AI-Content-Skills`, `cm-ai-content`, and `example`.

## Documentation

- `docs/getting-started.md` — end-to-end setup for maintainers, portals, and writers, with links to the dotagents and Agent Skills documentation.
- `docs/consuming-from-devcontainers.md` — consumer installation patterns.
- `docs/publishing-and-versioning.md` — release and versioning expectations.
- `docs/troubleshooting.md` — common installation issues.

Do not publish to npm, push to GitHub, or create Git tags unless that release action has been explicitly requested.
