---
name: "Validate File or Folder Against Style Guide"
description: "Use when validating a file, folder, or pasted content against repository documentation style rules."
argument-hint: "file or folder path and optional mode: report or fix"
agent: "agent"
---

Validate the file or folder I specify against this repository's documentation style rules.

Use the style-guide-validator skill for the validation workflow.

Inputs to use:

- Target path: the file or folder path I provide in this chat.
- Validation mode: default to validation-only unless I explicitly ask for fixes.
- Style guide: the repository style guide, if one exists.

Requirements:

- Review the Markdown or text file I specify, or the Markdown or text files in the target folder.
- Validate the content against the repository style guide.
- Preserve technical meaning and product terminology.
- Do not edit files unless I explicitly ask for corrections.
- If I ask for corrections, make only the minimal edits required.

When reporting validation results:

- Group findings into must fix, should fix, and optional improvements.
- Cite the relevant rule, the problematic text, and the suggested correction for each issue.
- Say explicitly when the style guide is silent or ambiguous.

At the end, report:

- files or folders reviewed
- summary of compliance
- violations found
- manual follow-up needed
