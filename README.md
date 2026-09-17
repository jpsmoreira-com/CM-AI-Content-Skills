# CM AI Content Skills

Reusable AI assets for the Critical Manufacturing content team: skills, subagents, and shared rules that documentation portals consume with [APM](https://github.com/microsoft/apm), pinned to a release tag.

## What is published

| Asset | Where | How a portal gets it |
| --- | --- | --- |
| Skills — on-demand workflows ([Agent Skills](https://agentskills.io): a folder with a `SKILL.md`) | `.apm/skills/<name>/` | `apm install` → `.agents/skills/` (Copilot, Codex) and `.claude/skills/` |
| Subagents — delegated, read-only bulk review | `.apm/agents/<name>.agent.md` | `apm install` → `.github/agents/`, `.claude/agents/`, `.codex/agents/` |
| Shared rules — always-on guardrails | `.apm/instructions/cm-ai-content.instructions.md` | `apm install` → `.github/instructions/`, `.claude/rules/`; `apm compile` → `AGENTS.md` |

| Name | Kind | Purpose |
| --- | --- | --- |
| `style-guide-validator` | skill | Validate wording and Markdown against the shared style guide and terminology glossary. |
| `tutorial-source-to-mkdocs` | skill | Convert DOCX / Markdown / HTML tutorial packages with media into MkDocs pages. |
| `docs-change-summary` | skill | Draft reader-focused commit messages, PR text, and changelog entries. |
| `docs-style-reviewer` | subagent | Bulk style review of a folder, PR, or converted tutorial. Read-only. |
| `docs-link-auditor` | subagent | Broken links, missing/orphaned assets, `.pages` mismatches. Read-only. |

## Use it in a portal

From the portal root (Python 3.10+ for the APM CLI):

```bash
curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.31.0   # 1. the APM CLI, once per machine or devcontainer
cp <this repo>/examples/apm.yml apm.yml                # 2. declare, pinned to a release
apm install                                           # 3. skills + subagents + rules -> .agents/, .claude/, .codex/, .github/
apm compile                                           # 4. fold the rules into AGENTS.md
```

Commit `apm.yml`, `apm.lock.yaml`, and everything APM wrote. In a devcontainer, `examples/devcontainer.json` runs steps 1, 3, and 4 on every rebuild with `--frozen`. Full contract: [docs/consuming.md](docs/consuming.md). Day-to-day use of the skills: [docs/using-the-skills.md](docs/using-the-skills.md).

## Work on it

```bash
curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.31.0   # the APM CLI, pinned to the version CI uses
python3 scripts/validate.py                           # structural validation (what CI runs)
apm compile --validate                                # every primitive parses
apm install                                           # dogfood: deploy this checkout's primitives (gitignored)
```

Consumer smoke test against the checkout (what the release workflow runs from the tag):

```bash
portal="$(mktemp -d)"
sed -e "s#- jpsmoreira-com/CM-AI-Content-Skills\#v.*#- $PWD#" examples/apm.yml > "$portal/apm.yml"
bash scripts/smoke-portal.sh "$portal"
```

Releases are git tags; see [docs/releasing.md](docs/releasing.md). How knowledge flows back into this repository: [CONTRIBUTING.md](CONTRIBUTING.md).

## Repository map

- `.apm/` — the published package: `skills/`, `agents/`, `instructions/` (above).
- `apm.yml` — the package manifest; its `version` is the next release.
- `examples/` — `apm.yml` and `devcontainer.json` for portals.
- `scripts/` — `validate.py` and `smoke-portal.sh` (maintainer/CI).
- `docs/` — consuming, using, releasing, troubleshooting; `docs/decisions/` — why things are the way they are.
- `evals/` — regression fixtures for the skills and subagents (maintainers only, not shipped).
- `.github/` — CI on every PR, release workflow on every `v*` tag.

Internal tools that consume these assets (such as the TFS documentation automation pipeline) live in the separate `CM-AI-Content-Tools` repository.

## License

[BSD 3-Clause](LICENSE), the same license as the other public Critical Manufacturing repositories.
