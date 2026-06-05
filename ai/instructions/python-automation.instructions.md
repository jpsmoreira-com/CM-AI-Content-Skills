---
description: "Use when editing Python automation, synchronization, indexing, or documentation helper scripts."
name: "Python Automation Guidelines"
applyTo:
  - "**/*.py"
---

# Python Automation Guidelines

- Keep edits focused and preserve current script entry points and CLI behavior unless the request says otherwise.
- Avoid broad refactors in maintenance scripts and generators.
- Preserve existing output shapes for generated documentation or index content unless explicitly requested.
- Prefer the standard library unless the repository already depends on a package that clearly solves the problem.
- Do not write or refresh generated output as part of a normal code change unless explicitly requested.
