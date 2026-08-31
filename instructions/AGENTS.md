<!-- cm-ai-content:managed:start -->
# Content AI Shared Rules

These rules are managed by the CM-AI-Content-Skills repository. Do not edit inside the
managed block; changes here are overwritten on the next sync. Add repository-specific
guidance below the managed block instead.

## Purpose

This repository is a documentation portal maintained with the help of AI coding assistants.
Assistants may inspect the repository, its local instructions, and the shared skills before
proposing changes.

## Operating Rules

- Keep changes focused on the requested work and avoid unrelated refactors.
- Preserve technical meaning, product terminology, and existing repository structure.
- Prefer minimal edits over rewrites unless the task explicitly requires a larger restructure.
- Do not create pull requests, push branches, or change the branch workflow unless the user explicitly asks for it.
- Use the shared skills (`style-guide-validator`, `tutorial-source-to-mkdocs`, `docs-change-summary`) when one matches the requested work. They are installed under `.agents/skills/`.
- For bulk review, delegate to the shared subagents `docs-style-reviewer` and `docs-link-auditor`. Both are read-only: they report, they never edit.

## Docs Markdown

Applies to Markdown under `docs/`.

- Write MkDocs-compatible Markdown.
- Preserve the existing heading hierarchy and split content into one topic per file when sensible.
- Use relative Markdown links.
- Keep terminology and technical meaning intact; prefer minimal edits over rewrites.
- For new tutorial or module pages, follow nearby examples for frontmatter, `.pages` files, and local asset placement.
- Store images in a nearby `images/` folder and videos in a nearby `videos/` folder.
- Preserve tables as Markdown when practical; if conversion would be lossy, call that out.
- Follow the shared style guide at `.agents/skills/style-guide-validator/references/style-guide-full.md` and the terminology glossary beside it, plus any repository-specific style rules given below this block.
- When editing ordered lists, match the repository's existing Markdown linting convention.

## Protected And Generated Files

- Treat generated output and protected index files as explicit-request work.
- Do not edit generated files unless the user explicitly asks for that exact file or generated output.
- Prefer changing the source content or generator instead of patching generated artifacts directly.
- Call out any generated or protected file that would need a separate build or regeneration step.

## MkDocs Configuration

Applies to `mkdocs.yml` and `mkdocs-*.yml`.

- Treat MkDocs configuration changes as explicit-request work.
- Keep changes minimal and limited to the requested build, navigation, plugin, or environment behavior.
- Preserve existing splits between base config and environment-specific overrides.
- Avoid unrelated navigation churn when adding or moving content.

## Python Automation

- Keep edits focused and preserve current script entry points and CLI behavior unless the request says otherwise.
- Avoid broad refactors in maintenance scripts and generators.
- Preserve existing output shapes for generated documentation or index content unless explicitly requested.
- Prefer the standard library unless the repository already depends on a package that clearly solves the problem.
- Do not write or refresh generated output as part of a normal code change unless explicitly requested.

## Result Reporting

When finishing, report:

- files changed;
- what changed and why;
- specifications, pull requests, or other sources used;
- validation performed;
- remaining reviewer concerns.
<!-- cm-ai-content:managed:end -->
