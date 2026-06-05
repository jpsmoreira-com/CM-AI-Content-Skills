# AGENTS.md

## Purpose

This repository is the source of truth for reusable public AI assets that can be installed into devcontainers and other development environments.

## Asset Layout

- Put reusable shared skills for Codex, GitHub Copilot, and Claude Code under `ai/skills/`.
- Each skill must be a directory with a valid `SKILL.md`.
- Each `SKILL.md` must include at least `name` and `description` metadata.
- Put reusable agent files under `ai/agents/`.
- Put reusable instruction files under `ai/instructions/`.
- Put generic examples under `ai/examples/`.
- Keep repository-specific project instructions separate from reusable shared instructions.

## Public Content Rules

- Do not include secrets, internal URLs, customer data, private credentials, proprietary information, or environment-specific tokens.
- Keep examples generic and safe to publish.
- Prefer neutral placeholders such as `usulpt/CM-AI-Content-Skills`, `cm-ai-content`, and `example`.
- Preserve compatibility for existing consumers whenever possible.

## Change Management

- Update `ai/manifest.json` when adding, removing, renaming, or changing assets.
- Update `ai/CHANGELOG.md` for every asset-library change.
- Prefer backward-compatible changes to skills, agents, instructions, and installer behavior.
- Use Git tags for stable releases.

## Validation

- Run `scripts/validate-ai-assets.sh` before publishing changes.
- Run `shellcheck` on shell scripts when it is available.
- Do not publish to npm, push to GitHub, or create tags unless explicitly requested.
