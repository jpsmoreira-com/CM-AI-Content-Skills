---
name: docs-change-summary
description: 'Use when writing commit messages, PR titles, PR descriptions, or changelog summaries for MkDocs documentation changes and changelog feeds.'
---

# Docs Change Summary

Use this skill when the user asks for a commit message, PR title, PR description, changelog entry, or release-note summary for documentation work.

## Required Inputs

- A Git diff, changed file list, or user-provided change summary
- Any repository-specific commit, pull request, or changelog guidance when available

If the user does not provide a diff or summary, inspect the local Git changes before drafting the output.

## Workflow

1. Identify reader-visible documentation changes.
1. Describe what changed in the documentation and why it matters to the reader.
1. Keep the first sentence usable as a changelog summary.
1. Prefer specific verbs such as Add, Clarify, Document, Remove, or Update.
1. Avoid generic wording such as "update docs" or "fix content".
1. Avoid internal process details such as PR checklists, reviewers, branch names, work item IDs, cherry-picks, or build status.
1. Preserve product names, feature names, UI labels, and technical meaning.
1. If the change is mostly structural, explain the reader-facing effect, such as easier navigation, clearer prerequisites, or corrected guidance.
1. If no reader-visible documentation change is present, say so and ask whether the user wants a process-focused summary instead.

## Output Guidance

For commit messages and PR titles, return one concise sentence unless the user asks for alternatives.

For PR descriptions, start with a changelog-ready summary sentence, then add short bullets for the main reader-visible changes when useful.

For changelog entries, use a sentence fragment or sentence that can stand alone in a release feed.

## Examples

- Clarify when sampling plan warnings appear while managing sampling plan instances.
- Add the optional Note field step to the Create Production Order procedure.
- Document that completed qualification checks allow materials to be merged or terminated.
