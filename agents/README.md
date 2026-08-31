# Agents

Reusable, public-safe subagent definitions: portable Markdown with `name` and `description` frontmatter and an instruction body. dotagents distributes them through `[[subagents]]` entries and writes the tool-native files (`.claude/agents/<name>.md`, `.codex/agents/<name>.toml`).

Subagents are for delegated, read-heavy work that benefits from a clean context window: bulk review and auditing. Interactive workflows belong in `../skills/` instead.

- `docs-style-reviewer.md` — read-only bulk style review of many files against the shared style guide.
- `docs-link-auditor.md` — read-only integrity sweep: relative links, missing/orphaned assets, `.pages` navigation.

## Adding one

1. Create `agents/<name>.md` with `name` (equal to the file name) and `description` frontmatter and a body. dotagents keeps only `name`, `description`, and the body for every target, so state behavioral limits such as "read-only, never edit files" in the body; a `tools:` or `model:` field would be silently dropped and the validator rejects it.
1. Add a `[[subagents]]` entry to `agents.toml` with `source = "path:."` and `path = "agents/<name>.md"`, and one to `examples/agents.toml` with the GitHub source.
1. Run `python3 scripts/validate.py` and `npx --yes @sentry/dotagents@3.0.1 --project sync`.
