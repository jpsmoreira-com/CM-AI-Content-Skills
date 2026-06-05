---
name: style-guide-validator
description: 'Use for style-guide validation requests such as reviewing documentation wording, checking Markdown consistency, validating a folder, or fixing documentation style deviations against a repository style guide.'
argument-hint: 'target file, folder, or pasted text and optional mode: report or fix'
---

# Style Guide Validator

Use this skill when the user asks to:

- validate text against a style guide
- review one or more files for writing consistency
- check whether content follows documentation style rules
- propose or apply edits that align content with the house style

## Bundled Reference

This skill includes a shared style guide at [references/style-guide-full.md](references/style-guide-full.md).

Use the bundled guide as the default source of truth for reusable documentation style rules. If a consuming repository also has local guidance, apply the local guidance only for repository-specific rules and do not fork the bundled guide per branch.

## Required Inputs

- One or more target files, selections, or pasted text blocks

## Workflow

1. Read the bundled style guide at [references/style-guide-full.md](references/style-guide-full.md) before validating content.
1. Check whether the consuming repository has additional local guidance, such as `AGENTS.md`, `.github/instructions/`, `style-guide.md`, or `docs/style-guide.md`.
1. Treat the bundled style guide as the shared baseline and local guidance as repository-specific additions or overrides.
1. Read the target text or files.
1. Validate content against the guide, focusing on:
   - tone and voice
   - terminology consistency
   - heading style
   - sentence length and clarity
   - active vs passive voice
   - list style
   - punctuation and capitalization
   - UI labels and product naming
   - prohibited words or discouraged phrasing
1. Preserve technical meaning. Do not introduce factual changes.
1. If the user asked only for validation, report findings without editing files.
1. If the user asked for corrections, make minimal edits needed to comply.
1. When reporting, group findings by:
   - must fix
   - should fix
   - optional improvements
1. For each issue, cite:
   - the relevant rule from the style guide
   - the problematic text
   - the suggested correction
1. If the style guide is ambiguous or silent on a point, say so explicitly instead of inventing a rule.

## Output Modes

### Validation Report

Return:

- summary of compliance
- list of violations
- suggested fixes
- manual follow-up needed

### Direct Edit Mode

If explicitly requested, update the target files and then summarize:

- files modified
- categories of fixes applied
- items needing manual review

## Conventions

- Prefer minimal edits over broad rewrites.
- Keep product names, UI labels, code, commands, paths, and version numbers unchanged unless the style guide explicitly says otherwise.
- Do not normalize examples inside code blocks unless explicitly requested.
