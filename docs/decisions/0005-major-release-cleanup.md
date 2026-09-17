# 0005 — 1.0.0: the tag is the version; drop the manifest, installer, and style guide copy

- **Date:** 2026-08-31
- **Status:** accepted (supersedes the "removal in 0.5.0" and `ai/` fallback consequences of 0002 and 0003)

## Decision

The first release of the dotagents-based contract is `v1.0.0`, cut as a clean break:

- The git tag is the only version. `manifest.json` (and its version fields) and the deprecated Bash installer are removed rather than carried for one more release; no consumer had adopted the never-tagged 0.4.0 layout.
- `agents.toml` uses a wildcard for skills and `path =` on subagents, so nothing has to be registered by hand and repeated installs are idempotent.
- The wiring script is self-contained (fetches the managed block from the pinned release when not run from a checkout), reads the pin from the portal's `agents.toml`, and no longer copies `style-guide-full.md` into the portal: the skill already installs it under `.agents/skills/style-guide-validator/references/`.
- Validation is a Python script plus CI (structure, dotagents install, shellcheck, markdownlint, wiring smoke tests) and a release workflow that verifies tag ↔ changelog ↔ examples and installs from the pushed tag.

## Why

A DevOps and a dotagents review of the branch found the documented consumer path broken (the piped wiring script could not find its inputs; every doc pinned a tag that did not exist), a manifest nothing read, four places to register each asset, three version fields, and docs that overstated what dotagents does (it only symlinks `.claude/skills`, never gitignores the tool folders, and drops `tools:` from subagents). Fixing forward under a major version is cheaper than preserving compatibility with a contract no one consumes yet.

## Consequences

Portals adopt by copying `examples/agents.toml` and `examples/devcontainer.json` at `v1.0.0`; the `AI_ASSETS_REF` variable now only selects which copy of the wiring script to fetch and must equal the pin. The Tools repository appends its own pipeline rules below the managed block instead of shipping them to every portal.
