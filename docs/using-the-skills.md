# Using the Skills

Once a portal is set up ([consuming.md](consuming.md)) nothing needs to be installed on a writer's machine: the devcontainer's `postCreateCommand` does it.

## Skills

Skills load on demand. Describe the task, or invoke them directly — `/name` in Claude Code and GitHub Copilot, `$name` in Codex.

| Task | Skill | Example |
| --- | --- | --- |
| Validate a file or folder against the style guide | `style-guide-validator` | `/style-guide-validator docs/module-x report` |
| Convert a DOCX or tutorial package to MkDocs pages | `tutorial-source-to-mkdocs` | `/tutorial-source-to-mkdocs <sources> <target folder>` |
| Draft a commit message, PR text, or changelog entry | `docs-change-summary` | `/docs-change-summary` |

## Subagents

For bulk work, delegate to a subagent instead of running everything in the main chat. Both are read-only: they report findings and never edit files.

| Task | Say |
| --- | --- |
| Review a whole folder or PR against the style guide | "use the docs-style-reviewer agent on docs/module-x" |
| Sweep for broken links, missing or orphaned assets, `.pages` mismatches | "run the docs-link-auditor on docs/" |

Subagents are available in Claude Code and Codex only — dotagents has no Copilot subagent format. In Copilot, use the `style-guide-validator` skill on the folder instead.

## Always-on rules

The managed block in `AGENTS.md` (don't touch generated files, MkDocs config only on explicit request, follow the style guide, and so on) applies automatically. There is nothing to invoke. Portal-specific rules go below the block's end marker.

## When the AI keeps getting something wrong

If you correct it twice for the same thing, the fix belongs in this repository — see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
