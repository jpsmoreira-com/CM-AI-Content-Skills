# Using the Skills

Once a portal is set up ([consuming.md](consuming.md)) nothing needs to be installed on a writer's machine: the deployed files are committed, and the devcontainer's `postCreateCommand` keeps them in sync.

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

Both are available in Claude Code, Codex, and GitHub Copilot (pick them from the agent list, or mention them by name).

## Always-on rules

The shared guardrails (don't touch generated files, MkDocs config only on explicit request, follow the style guide, and so on) apply automatically: they are compiled into `AGENTS.md` and installed in each tool's native rules folder. There is nothing to invoke. Portal-specific rules live in the portal's own `.apm/instructions/` and compile into the same `AGENTS.md`.

## When the AI keeps getting something wrong

If you correct it twice for the same thing, the fix belongs in this repository — see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
