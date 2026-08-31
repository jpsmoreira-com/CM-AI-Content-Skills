# AGENTS.md

## Purpose

This repository is the source of truth for reusable public AI assets used by the content-writing team across documentation portals. Assets are consumed in two ways:

- **Skills and subagents** — via [dotagents](https://github.com/getsentry/dotagents): consumers declare them in `agents.toml`, pinned to a release tag.
- **Shared rules** — via `scripts/sync-repo-wiring.sh`, which maintains a managed block inside each consumer's root `AGENTS.md`, a `CLAUDE.md` stub, and a copy of the style guide.

## Asset Layout

- `skills/` — shared skills for Claude Code, Codex, and GitHub Copilot / VS Code. Each skill is a directory with a valid `SKILL.md` that includes at least `name` and `description` metadata.
- `agents/` — reusable subagent definitions (portable Markdown with `name`/`description` frontmatter), registered in `manifest.json` and declared as `[[subagents]]` in `agents.toml`.
- `instructions/AGENTS.md` — the managed rules block. It must start with `<!-- cm-ai-content:managed:start -->` and end with `<!-- cm-ai-content:managed:end -->`.
- `examples/` — generic consumer examples (`agents.toml`, devcontainer snippets).
- `manifest.json` — machine-readable inventory; paths are relative to the repository root.
- `agents.toml` — this repository's own dotagents manifest; every skill under `skills/` must be listed with a `path:` source.
- `docs/decisions/` — decision records; `evals/` — maintainer-only regression fixtures; `CONTRIBUTING.md` — the contribution loop.
- Internal tooling that consumes these assets (for example the TFS documentation automation pipeline) lives in the separate `CM-AI-Content-Tools` repository. Keep tools out of this repository; it only publishes the shared assets.

There are no Copilot `.instructions.md` or `.prompt.md` files: on-demand workflows are skills, always-on guardrails live in the managed `AGENTS.md` block.

## Public Content Rules

- Do not include secrets, internal URLs, customer data, private credentials, proprietary information, or environment-specific tokens.
- Keep examples generic and safe to publish.
- Prefer neutral placeholders such as `usulpt/CM-AI-Content-Skills`, `cm-ai-content`, and `example`.
- Preserve compatibility for existing consumers whenever possible.

## Change Management

- Update `manifest.json` and `agents.toml` when adding, removing, or renaming skills or agents.
- Update `CHANGELOG.md` for every asset-library change.
- Prefer backward-compatible changes to skills, agents, the managed block, and scripts.
- Use Git tags for stable releases; consumers pin to tags.

## Validation

- Run `scripts/validate-ai-assets.sh` before publishing changes.
- When a skill or agent with an eval suite changes (or the style guide / glossary it depends on), run the suite in `evals/` and update expected findings only for intended behavior changes.
- Run `npx @sentry/dotagents --project sync` after editing skills or agents, and `npx @sentry/dotagents --project doctor` to check the local dotagents state.
- Run `shellcheck` on shell scripts when it is available.
- Do not publish to npm, push to GitHub, or create tags unless explicitly requested.
