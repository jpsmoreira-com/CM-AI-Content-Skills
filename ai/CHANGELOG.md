# Changelog

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
