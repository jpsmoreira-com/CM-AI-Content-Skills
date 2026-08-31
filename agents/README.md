# Agents

Reusable, public-safe subagent definitions: portable Markdown with `name` and `description` frontmatter, distributed to consumers via dotagents `[[subagents]]` entries and materialized into the tool-native folders (`.claude/agents/`, `.codex/agents/`, ...).

Subagents are for delegated, read-heavy work that benefits from a clean context window — bulk review and auditing. Interactive workflows belong in `../skills/` instead.

- `docs-style-reviewer.md` — read-only bulk style review of many files against the shared style guide.
- `docs-link-auditor.md` — read-only integrity sweep: relative links, missing/orphaned assets, `.pages` navigation.

When adding one, register it in `manifest.json` and add a `[[subagents]]` entry to `agents.toml` (`source = "path:."` — dotagents scans this repository's `agents/` folder) and to `examples/agents.toml` (`source = "usulpt/CM-AI-Content-Skills@<tag>"`).

Note: dotagents currently propagates only `name` and `description` frontmatter into the generated runtime files. A `tools:` field in the source is not enforced downstream — state behavioral limits (such as "read-only, never edit files") explicitly in the agent body.
