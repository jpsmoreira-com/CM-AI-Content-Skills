# CM AI Content Skills

Reusable AI assets for the Critical Manufacturing content team: skills, subagents, and shared rules that documentation portals consume with [dotagents](https://github.com/getsentry/dotagents), pinned to a release tag.

## What is published

| Asset                                            | Where                    | How a portal gets it                                                          |
| ------------------------------------------------ | ------------------------ | ----------------------------------------------------------------------------- |
| Skills — ([Agent Skills](https://agentskills.io) | `skills/<name>/`         | dotagents `[[skills]]` (wildcard) — Claude Code, Codex, Copilot               |
| Subagents — delegated, read-only bulk review     | `agents/<name>.md`       | dotagents `[[subagents]]` — Claude Code and Codex only                        |
| Shared rules — always-on guardrails              | `instructions/AGENTS.md` | `scripts/sync-repo-wiring.sh`, as a managed block in the portal's `AGENTS.md` |

| Name                        | Kind     | Purpose                                                                          |
| --------------------------- | -------- | -------------------------------------------------------------------------------- |
| `style-guide-validator`     | skill    | Validate wording and MD against the shared style guide and terminology glossary. |
| `tutorial-source-to-mkdocs` | skill    | Convert DOCX / Markdown / HTML tutorial packages with media into MkDocs pages.   |
| `docs-change-summary`       | skill    | Draft reader-focused commit messages, PR text, and changelog entries.            |
| `docs-style-reviewer`       | subagent | Bulk style review of a folder, PR, or converted tutorial. Read-only.             |
| `docs-link-auditor`         | subagent | Broken links, missing/orphaned assets, `.pages` mismatches. Read-only.           |

## Use it in a portal

From the portal root (Node.js 20+ required):

```bash
cp <this repo>/examples/agents.toml agents.toml                                   # 1. declare, pinned to a release
npx --yes @sentry/dotagents@3.1.0 --project install                               # 2. skills + subagents -> .agents/, .claude/, .codex/
curl -fsSL https://raw.githubusercontent.com/jpsmoreira-com/CM-AI-Content-Skills/v1.0.0/scripts/sync-repo-wiring.sh | bash -s -- .   # 3. rules
```

Commit `agents.toml`, `AGENTS.md`, `CLAUDE.md`, and `.gitignore`. In a devcontainer, `examples/devcontainer.json` runs steps 2–3 on every rebuild. Full contract: [docs/consuming.md](docs/consuming.md). Day-to-day use of the skills: [docs/using-the-skills.md](docs/using-the-skills.md).

## Work on it

```bash
npx --yes @sentry/dotagents@3.1.0 --project install   # link the local assets into the tool folders
python3 scripts/validate.py                           # structural validation (what CI runs)
bash scripts/test-wiring.sh                           # wiring script smoke tests
npx --yes @sentry/dotagents@3.1.0 --project sync      # after editing skills/ or agents/
```

Releases are git tags; see [docs/releasing.md](docs/releasing.md). How knowledge flows back into this repository: [CONTRIBUTING.md](CONTRIBUTING.md).

## Repository map

- `skills/`, `agents/`, `instructions/AGENTS.md` — the published assets (above).
- `agents.toml` — this repository's own dotagents manifest (dogfooding the assets).
- `examples/` — `agents.toml` and `devcontainer.json` for portals.
- `scripts/` — `sync-repo-wiring.sh` (consumer), `validate.py` and `test-wiring.sh` (maintainer/CI).
- `docs/` — consuming, using, releasing, troubleshooting; `docs/decisions/` — why things are the way they are.
- `evals/` — regression fixtures for the skills and subagents (maintainers only, not shipped).
- `.github/` — CI on every PR, release workflow on every `v*` tag.

Internal tools that consume these assets (such as the TFS documentation automation pipeline) live in the separate `CM-AI-Content-Tools` repository.

## License

[BSD 3-Clause](LICENSE), the same license as the other public Critical Manufacturing repositories.
