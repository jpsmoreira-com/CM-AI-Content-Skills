# 0004 — Move internal tools to `CM-AI-Content-Tools`

- **Date:** 2026-08-31
- **Status:** accepted

## Decision

Internal AI tooling for the Content Team lives in its own repository, `CM-AI-Content-Tools`, one top-level folder per tool. `projects/tfs-doc-automation-mvp` moved there (with history) as `tfs-doc-automation-mvp/`. This repository publishes only the shared assets (skills, subagents, managed rules).

## Why

Decision 0003 left `projects/` as an open question. Keeping the pipeline here mixed a public, versioned asset contract with private tooling that has its own release cadence, dependencies, and devcontainer image, and it forced every asset release to carry the tool. More tools are planned, so they need a home that is not the asset library.

## Consequences

The pipeline consumes the assets from a sibling checkout (`CONTENT_AI_REPO_PATH`, default `/workspaces/CM-AI-Content-Skills`) and its own checkout is `CONTENT_AI_TOOLS_REPO_PATH` (default `/workspaces/CM-AI-Content-Tools`). Devcontainer images seed both. `projects/` and the `projects/_backups/` ignore rule are gone from this repository.
