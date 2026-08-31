# Changelog

## 0.4.0 - 2026-08-30

- Integrated the TFS pipeline with dotagents: `sync-content-ai-assets.sh` now also installs shared skills and subagents into target workspaces via `@sentry/dotagents` (honoring a committed portal `agents.toml`, otherwise generating a git-excluded one sourced from the synced `.agents/content-ai/` copy), so agents load skills from the standard `.agents/skills/` location.
- Moved the TFS documentation automation pipeline (`projects/tfs-doc-automation-mvp`) to the new `CM-AI-Content-Tools` repository, the home for the Content Team's internal AI tools (decision record 0004). This repository now publishes only the shared assets; the pipeline consumes them from a sibling checkout via `CONTENT_AI_REPO_PATH`.
- Flattened the layout: the former `ai/` folder is gone — `docs/`, `docs/decisions/`, `examples/`, `instructions/`, `manifest.json`, and `CHANGELOG.md` now live at the repository root (decision record 0003).
- Adopted [dotagents](https://github.com/getsentry/dotagents) for distributing skills and subagents. Consumers declare them in a committed `agents.toml` pinned to a release tag; this repository ships its own `agents.toml` and an example under `examples/agents.toml`.
- Moved `ai/skills/` to `skills/` and `ai/agents/` to `agents/` at the repository root so dotagents discovers them by convention.
- Removed the Copilot `.instructions.md` and `.prompt.md` files. The two prompt files duplicated the `tutorial-source-to-mkdocs` and `style-guide-validator` skills; the `docs-change-summary` and `tutorial-conversion` instructions duplicated their skills; the four guardrail instructions (docs Markdown, protected/generated files, MkDocs config, Python automation) now live in the managed `AGENTS.md` block so they load unconditionally in every tool.
- Reworked the shared rules (now `instructions/AGENTS.md`) into a managed block delimited by `<!-- cm-ai-content:managed:start/end -->` markers.
- Rewrote `scripts/sync-repo-wiring.sh` to maintain that block inside a consumer's `AGENTS.md` (creating, prepending, or updating it while leaving everything outside the markers untouched), plus the `CLAUDE.md` stub and the style guide copy.
- Manifest paths are now relative to the repository root; install targets are `dotagents` and `wiring`.
- Deprecated `scripts/install-ai-assets.sh`. It still works against the new layout and prints a warning; it will be removed in 0.5.0.
- Added an `argument-hint` to the `docs-change-summary` skill.
- Added the first two shared subagents: `docs-style-reviewer` (bulk style review, read-only) and `docs-link-auditor` (link, asset, and `.pages` integrity sweep, read-only), distributed via dotagents `[[subagents]]` entries.
- Added the knowledge-base scaffolding: a terminology glossary bundled with `style-guide-validator`, golden examples bundled with `tutorial-source-to-mkdocs`, decision records under `docs/decisions/`, eval fixtures under `evals/` for the validator skill and the link auditor agent, and a root `CONTRIBUTING.md` with the contribution loop ("corrected twice → PR it").
- Added `docs/getting-started.md` — end-to-end setup guide for maintainers, portal repositories, and writers, with links to the dotagents, Agent Skills, and AGENTS.md documentation.

## 0.3.0 - 2026-06-30

- Added a managed root `AGENTS.md` baseline for repositories that consume Content AI automation.
- Updated the TFS Autonomous Pipeline asset sync flow to publish the managed root `AGENTS.md` into target repositories while keeping the full asset copy under `.agents/content-ai/`.

## 0.2.0 - 2026-06-05

- Added the `docs-change-summary` skill for reader-focused commit messages, PR titles, PR descriptions, and changelog summaries for documentation changes.
- Added reusable documentation change-summary instructions for repositories that generate MkDocs documentation and changelog feeds.

## 0.1.0 - 2026-06-03

- Added the initial public AI asset library layout.
- Added reusable Codex skills for style-guide validation and tutorial-source conversion.
- Added the shared documentation style guide as a bundled `style-guide-validator` reference.
- Added shared instruction files and devcontainer usage examples.
- Added the GitHub-based installer and validation workflow.
- Added install target metadata and user-level skill installation for Codex, GitHub Copilot, and Claude Code.
