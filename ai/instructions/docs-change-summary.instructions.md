---
description: "Use when writing commit messages, PR titles, PR descriptions, or changelog summaries for documentation changes."
name: "Documentation Change Summaries"
applyTo:
  - "docs/**/*.md"
  - "**/CHANGELOG.md"
---

# Documentation Change Summaries

- Focus on reader-visible documentation changes.
- Describe what changed in the documentation and why it matters to the reader.
- Keep the first sentence usable as a changelog summary.
- Avoid internal process details such as PR checklists, reviewers, branch names, work item IDs, cherry-picks, or build status.
- Avoid generic wording such as "update docs" or "fix content".
- Prefer specific verbs such as Add, Clarify, Document, Remove, or Update.

Good examples:

- Clarify when sampling plan warnings appear while managing sampling plan instances.
- Add the optional Note field step to the Create Production Order procedure.
- Document that completed qualification checks allow materials to be merged or terminated.
