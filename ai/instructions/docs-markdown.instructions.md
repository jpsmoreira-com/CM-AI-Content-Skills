---
description: "Use when writing or editing Markdown documentation in MkDocs-compatible repositories."
name: "Docs Markdown Guidelines"
applyTo:
  - "docs/**/*.md"
---

# Docs Markdown Guidelines

- Write MkDocs-compatible Markdown.
- Preserve the existing heading hierarchy and split content into one topic per file when sensible.
- Use relative Markdown links.
- Keep terminology and technical meaning intact; prefer minimal edits over rewrites.
- For new tutorial or module pages, follow nearby examples for frontmatter, `.pages` files, and local asset placement.
- Store extracted images in a nearby `images/` folder when appropriate.
- Preserve tables as Markdown when practical; if conversion would be lossy, call that out.
- Follow the repository style guide when wording or formatting is unclear.
- When editing ordered lists, match the repository's existing Markdown linting convention.
