# 0007 — Distribute with APM; retire dotagents and the wiring script

- **Date:** 2026-09-17
- **Status:** accepted (supersedes the distribution half of 0002; its reasoning about unconditional guardrails stands)

## Decision

Skills, subagents, and the always-on guardrails ship as one [APM](https://github.com/microsoft/apm) package: `apm.yml` at the root, primitives under `.apm/`. Portals pin `jpsmoreira-com/CM-AI-Content-Skills#vX.Y.Z` in their own `apm.yml`, run `apm install` and `apm compile`, and commit the deployed tree. dotagents, `agents.toml`, and `scripts/sync-repo-wiring.sh` are retired. 1.0.0 was never tagged on the dotagents contract, so the first release ships APM directly.

## Why

Two gaps were structural in dotagents 3.1.0, verified against its config schema rather than its docs: no Copilot subagent serializer (`Agent "GitHub Copilot" does not support custom subagents`), and no instructions primitive at all, which is why a 193-line Bash script existed to maintain a managed block inside each portal's `AGENTS.md`. APM has both. `.apm/agents/*.agent.md` deploys verbatim to `.github/agents/`, and an instruction without `applyTo` folds unconditionally into `AGENTS.md`, `.github/copilot-instructions.md`, and `.claude/rules/`, which is the exact requirement [0002](0002-dotagents-for-distribution.md) recorded. One tool replaces two.

Verified in a scratch portal on APM 0.31.0 before deciding: all three skills land in `.agents/skills/` (the path dotagents used, so `/name` and `$name` invocations do not move); both subagents reach Copilot, Claude Code, and Codex; a portal-local `.apm/instructions/` rule compiles into the same `AGENTS.md` ahead of the shared block; `apm install --frozen` and `apm audit --ci` pass; repeated installs change nothing.

Risks accepted: APM is 0.x with minor releases roughly every two weeks, so the CLI version is pinned in one place per surface and `validate.py` fails when they disagree. The install gesture moves from `npx` to a binary that needs Python 3.10+. `file://` sources are refused, so the GitHub `#tag` pin is proven by the release smoke test rather than locally.

Rejected: hand-written `.github/agents/*.agent.md` copies beside dotagents (unmanaged, would drift from the source); keeping the wiring script for the `AGENTS.md` block while using APM for everything else (two ownership models for one file).

## Consequences

Breaking against the 0.x releases, and against the unreleased dotagents contract any portal may have adopted from `main`: `agents.toml` becomes `apm.yml`; `npx @sentry/dotagents … install` plus `curl … sync-repo-wiring.sh` become `apm install && apm compile`; deployed files are committed instead of gitignored, so cloud agents such as the Copilot coding agent see them without running APM. Portal-specific rules move from text below the managed block into the portal's own `.apm/instructions/*.instructions.md`. `apm compile` never overwrites a hand-authored `AGENTS.md` (one without its marker), so an unmigrated portal keeps its file, but Codex would then miss the guardrails; `scripts/smoke-portal.sh` asserts the compiled output to catch that.

In this repository `apm install` dogfoods the primitives and the deployed copies are gitignored; `apm compile` is never run here because the root `AGENTS.md` is contributor guidance, not a published primitive. APM parses every file under `.apm/agents/` as an agent, so authoring notes live in `CONTRIBUTING.md` and `validate.py` rejects anything there that is not `*.agent.md`.
