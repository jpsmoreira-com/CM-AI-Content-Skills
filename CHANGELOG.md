# Changelog

## 1.0.0 (unreleased)

First release of the APM-based contract. Breaking: nothing from 0.x is carried over. Portals consume one package with [APM](https://github.com/microsoft/apm), Microsoft's Agent Package Manager (decision record 0007). dotagents was adopted and replaced before this release shipped (decision records 0002, 0006, 0007); a portal set up from `main` in between follows the migration section in `docs/consuming.md`.

### Consumers get

- Skills (`style-guide-validator`, `tutorial-source-to-mkdocs`, `docs-change-summary`), subagents (`docs-style-reviewer`, `docs-link-auditor`), and the always-on guardrails through one `apm.yml` pinned to `#v1.0.0`: `apm install` deploys them, `apm compile` folds the guardrails, together with any portal-local instructions, into `AGENTS.md`.
- Subagents in GitHub Copilot (`.github/agents/`), Claude Code (`.claude/agents/`), and Codex (`.codex/agents/`).
- Guardrails delivered natively per harness: `.github/instructions/` and `.github/copilot-instructions.md` for Copilot, `.claude/rules/` for Claude Code, compiled `AGENTS.md` for Codex.
- A lockfile with content hashes (`apm.lock.yaml`), `apm install --frozen` as the CI gate, `apm audit --ci` for drift and hidden-Unicode scanning, and `examples/devcontainer.json` wiring it all into `postCreateCommand`.

### Changed

- Layout: the package lives under `.apm/` (`skills/`, `agents/<name>.agent.md`, `instructions/cm-ai-content.instructions.md` with no `applyTo`, so it loads unconditionally) with `apm.yml` at the root. The old `ai/` folder, the Copilot `.instructions.md`/`.prompt.md` files, `manifest.json`, and the Bash installer are gone (decision records 0002, 0003, 0005, 0007).
- The guardrails are portal-agnostic (no pipeline or dashboard rules) and point at the style guide installed with the skill. Portal-specific rules are the portal's own `.apm/instructions/*.instructions.md`.
- Skill descriptions state what each skill does and when to use it; subagent constraints live in the body.
- New subagents `docs-style-reviewer` and `docs-link-auditor`; terminology glossary and golden examples bundled with the skills; decision records, eval fixtures, and `CONTRIBUTING.md` added.
- Validation is `scripts/validate.py` (`.apm/` layout, `apm.yml` ↔ disk, the unconditional guardrails, release pin ↔ changelog ↔ examples, one APM CLI version, links) and `scripts/smoke-portal.sh` (every primitive reaches every harness), plus GitHub Actions: CI on every PR (validate, `apm compile --validate`, dogfood install and audit, smoke test, markdownlint) and a release workflow on `v*` tags that installs from the pushed tag with `owner/repo#vX.Y.Z` and publishes release notes from this file.
- The devcontainer needs Python 3.10+ for the APM CLI; Node.js is not required.
- The TFS documentation automation pipeline moved to the `CM-AI-Content-Tools` repository (decision record 0004).
- Licensed under BSD 3-Clause (`LICENSE`); each skill declares `license: BSD-3-Clause`.
- `docs/consuming.md` documents installing other packages alongside this one and the cross-package name-clash hazard in APM 0.31.0.

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
