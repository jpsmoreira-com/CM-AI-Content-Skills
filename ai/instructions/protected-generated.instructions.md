---
description: "Use when a task touches generated output or protected documentation artifacts."
name: "Protected And Generated Files"
applyTo:
  - "site/**"
  - "**/full_index.md"
---

# Protected And Generated Files

- Treat generated output and protected index files as explicit-request work.
- Do not edit generated files unless the user explicitly asks for that exact file or generated output.
- Prefer changing the source content or generator instead of patching generated artifacts directly.
- Call out any generated or protected file that would need a separate build or regeneration step.
