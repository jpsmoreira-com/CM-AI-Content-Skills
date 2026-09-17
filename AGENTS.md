# AGENTS.md

Rules for agents working on this repository. What it is and how it is consumed: `README.md`. How knowledge gets in and how releases go out: `CONTRIBUTING.md`, `docs/releasing.md`.

## Layout

- `.apm/skills/<name>/SKILL.md` — a skill; `name` equals the directory name, `description` says what it does and when to use it. Extra material goes in `references/`. Published automatically (`includes: auto` in `apm.yml`).
- `.apm/agents/<name>.agent.md` — a subagent; `name` equals the file name without `.agent.md`. Deployed verbatim to Copilot and transformed for Claude Code and Codex, so keep behavioral limits in the body. APM treats every file in this directory as an agent: no README or notes here.
- `.apm/instructions/cm-ai-content.instructions.md` — the always-on guardrails. `description` only, never `applyTo`: it must load unconditionally, on every turn, in every portal, so keep it short and portal-agnostic.
- `apm.yml` — the package manifest. Its `version` is the next release, matched by `CHANGELOG.md` and `examples/apm.yml`.
- `examples/` — the consumer contract (`apm.yml`, `devcontainer.json`), pinned to the next release tag.
- `scripts/` — `validate.py` (structure, no network) and `smoke-portal.sh` (installs into a portal and asserts every harness). Both run in CI.
- `docs/decisions/` — one record per decision, never rewritten; supersede with a new record.
- `evals/` — fixtures with deliberate problems; never "fix" them.

## Rules

- Public content only: no secrets, internal URLs, customer data, or proprietary details. `jpsmoreira-com/CM-AI-Content-Skills` is the published source.
- The git tag is the only version. `CHANGELOG.md` gets a line for every change under the next release heading; `apm.yml` and the examples carry that release.
- Do not add a second distribution path (installer scripts, per-tool prompt files, managed blocks): everything ships through APM from `.apm/`.
- Never run `apm compile` in this repository: this file is hand-authored contributor guidance, not a published primitive. `apm install` (dogfood) is fine; its output is gitignored.
- Before finishing: `python3 scripts/validate.py` and `apm compile --validate`; `apm install` after editing anything under `.apm/`.
- Do not push, tag, or publish unless explicitly asked.
