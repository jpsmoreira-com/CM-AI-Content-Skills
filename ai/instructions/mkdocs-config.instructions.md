---
description: "Use when editing MkDocs configuration, navigation, environment-specific YAML files, or docs build settings."
name: "MkDocs Config Guidelines"
applyTo:
  - "mkdocs.yml"
  - "mkdocs-*.yml"
---

# MkDocs Config Guidelines

- Treat MkDocs configuration changes as explicit-request work.
- Keep changes minimal and limited to the requested build, navigation, plugin, or environment behavior.
- Preserve existing splits between base config and environment-specific overrides.
- Avoid unrelated navigation churn when adding or moving content.
- Prefer changing source content or generators instead of patching generated artifacts directly.
