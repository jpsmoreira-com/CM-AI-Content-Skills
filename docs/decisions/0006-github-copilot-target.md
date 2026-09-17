# 0006 — Add GitHub Copilot as a declared dotagents target (skills only)

- **Date:** 2026-09-17
- **Status:** superseded by [0007](0007-distribute-with-apm.md)

## Decision

`agents.toml` and `examples/agents.toml` declare `agents = ["claude", "codex", "copilot"]`, and the dotagents pin moves from 3.0.1 to 3.1.0. Subagent `targets` stay `["claude", "codex"]`: Copilot receives the skills and the managed `AGENTS.md` block, not the subagents.

## Why

3.0.1 has no Copilot target at all. Its `vscode` target is named "VS Code Copilot" but defines only MCP and hooks — no `skillsParentDir`, no subagent format — so listing it changes nothing and putting it in a subagent's `targets` only warns. 3.1.0 adds a real `copilot` target.

Copilot, like Codex, reads `.agents/skills/` natively, so at project scope the entry writes no files and the installed tree is byte-identical with or without it. We add it anyway because it states the supported set in one place, makes CI install and doctor against Copilot, and selects `~/.copilot` for anyone installing at user scope. Skills already reached Copilot in practice; what was missing was a declaration and a test.

The `copilot` definition has no subagent serializer (and raises `UnsupportedFeature` for hooks), so `docs-style-reviewer` and `docs-link-auditor` cannot be distributed to it. Hand-writing `.github/agents/*.agent.md` copies was rejected: they would sit outside dotagents and drift from `agents/*.md`. The guardrails need no work — Copilot reads `AGENTS.md`, which is the reasoning already recorded in [0002](0002-dotagents-for-distribution.md) for retiring the Copilot instruction files.

## Consequences

Portals adopting this release bump the dotagents version in `devcontainer.json` and add `"copilot"` to `agents`. `validate.py` now pins the expected agent list, forbids `"copilot"` in subagent `targets`, and fails when the dotagents version disagrees across docs, CI, and the devcontainer. The compatibility table in `docs/consuming.md` continues to show `—` for Copilot subagents.
