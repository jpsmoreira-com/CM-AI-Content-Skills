# 0003 — Flatten the repository layout (retire `ai/`)

- **Date:** 2026-08-30
- **Status:** accepted

## Decision

Everything lives at the repository root: `skills/`, `agents/`, `instructions/`, `docs/` (with `docs/decisions/`), `examples/`, `evals/`, `manifest.json`, `CHANGELOG.md`. The `ai/` folder is retired.

## Why

`ai/` made sense when it held the whole asset library. After skills and agents moved to the root for dotagents discovery, it was a rump holding a grab-bag of unrelated content, and every consumer path carried a meaningless `ai/` prefix. Flattening happened before the first tagged release of the new layout (v0.4.0), so no published consumer contract was broken; the deprecated Bash installer falls back to the pre-0.4.0 `ai/` layout for old refs.

## Consequences

All documentation, the validator, the legacy installer default (`AI_ASSETS_PATH=.`), the wiring script, and the TFS pipeline sync script reference root paths. `projects/` remains in place — moving it to its own repository is a separate, still-open decision.
