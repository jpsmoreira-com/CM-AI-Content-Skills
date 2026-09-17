# 0002 — Distribute skills with dotagents; guardrails via managed AGENTS.md block

- **Date:** 2026-08-30
- **Status:** distribution superseded by [0007](0007-distribute-with-apm.md); the reasoning that guardrails must load unconditionally stands

## Decision

Skills and subagents are distributed to portals with dotagents (`agents.toml` pinned to a release tag). Always-on guardrails live in a managed block synced into each portal's `AGENTS.md` by `scripts/sync-repo-wiring.sh`. Copilot `.instructions.md`/`.prompt.md` files were retired.

## Why

Skills are the cross-tool standard for on-demand workflows (Claude Code, Codex, Copilot all load them), so the prompt files were duplicates. Path-scoped instruction files only load probabilistically in non-Copilot tools; guardrails must load unconditionally, which `AGENTS.md` guarantees everywhere. dotagents replaces a hand-rolled Bash installer with lockstep versioning.

## Consequences

`ai/skills` → `skills/`, `ai/agents` → `agents/`; legacy installer deprecated (removal in 0.5.0); portals migrate per `docs/getting-started.md`.
