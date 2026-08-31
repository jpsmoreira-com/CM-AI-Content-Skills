# Changelog

## 1.0.0 (unreleased)

First release of the dotagents-based contract. Breaking: nothing from 0.x is carried over.

### Consumers get

- Skills (`style-guide-validator`, `tutorial-source-to-mkdocs`, `docs-change-summary`) and subagents (`docs-style-reviewer`, `docs-link-auditor`) through [dotagents](https://github.com/getsentry/dotagents): copy `examples/agents.toml` (wildcard skills, explicit subagents, `[trust]`) pinned to `@v1.0.0`, run `npx --yes @sentry/dotagents@3.0.1 --project install`.
- Always-on rules through `scripts/sync-repo-wiring.sh`, run remotely with `curl ... | bash -s -- .`. It fetches the managed block from the release pinned in the portal's `agents.toml`, maintains the block inside the portal's `AGENTS.md`, creates `CLAUDE.md` once, and appends the dotagents runtime entries to `.gitignore`. `--check` reports drift for CI.
- `examples/devcontainer.json` wiring both steps into `postCreateCommand`.

### Changed

- Layout flattened to the repository root: `skills/`, `agents/`, `instructions/AGENTS.md`, `examples/`, `docs/`, `evals/`. The old `ai/` folder, the Copilot `.instructions.md`/`.prompt.md` files, `manifest.json`, and the Bash installer are gone (decision records 0002, 0003, 0005).
- The managed block is portal-agnostic (no pipeline or dashboard rules) and points at the style guide installed with the skill; the wiring script no longer copies `style-guide-full.md` to the portal root.
- Skill descriptions state what each skill does and when to use it; subagents drop the `tools:` field that dotagents does not propagate.
- New subagents `docs-style-reviewer` and `docs-link-auditor`; terminology glossary and golden examples bundled with the skills; decision records, eval fixtures, and `CONTRIBUTING.md` added.
- Validation is `scripts/validate.py` (structure, `agents.toml` ↔ disk, example pins ↔ changelog, links) plus GitHub Actions: CI on every PR (validate, dotagents install/doctor, shellcheck, markdownlint, wiring smoke tests) and a release workflow on `v*` tags that installs from the pushed tag and publishes release notes from this file.
- The TFS documentation automation pipeline moved to the `CM-AI-Content-Tools` repository (decision record 0004).
- Licensed under BSD 3-Clause (`LICENSE`); each skill declares `license: BSD-3-Clause`.

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
