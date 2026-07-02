# AGENTS.md

## Purpose

This repository is a target workspace for Content AI automation. The automation may inspect work item context, linked implementation pull requests, specifications, local repository instructions, and managed Content AI skills before proposing changes.

## Operating Rules

- Keep changes focused on the requested work item and avoid unrelated refactors.
- Preserve technical meaning, product terminology, and existing repository structure.
- Prefer minimal edits over rewrites unless the task explicitly requires a larger restructure.
- Do not create pull requests, push branches, or change branch workflow from the agent. The dashboard owns branch, push, and PR operations.
- Read the generated context package when present, especially `.automation-context/copilot/**/capture/INSTRUCTIONS.md` and `summary.md`.
- Follow repository-local instructions under `.github/instructions/`, `.github/prompts/`, and `.agents/content-ai/` when relevant.
- Use managed skills under `.agents/content-ai/skills/` when a skill matches the requested work.

## Documentation Work

- Write MkDocs-compatible Markdown.
- Preserve heading hierarchy and nearby formatting conventions.
- Use relative Markdown links.
- Store new images near the topic that uses them, usually under a local `images/` folder.
- Follow `style-guide-full.md` when it exists in the repository.
- Do not edit generated output under `site/` unless explicitly requested.
- Do not edit protected generated index files such as `docs/introduction/full_index.md` unless explicitly requested.

## Code Or Automation Work

- Follow the repository's existing patterns, scripts, and validation commands.
- Keep dependencies and tooling changes scoped to the requested task.
- Run lightweight validation when the repository makes the command obvious.

## Result Reporting

When finishing, report:

- files changed;
- what changed and why;
- specs, pull requests, or work item evidence used;
- validation performed;
- remaining reviewer concerns.
