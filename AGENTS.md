# AGENTS.md

Rules for agents working on this repository. What it is and how it is consumed: `README.md`. How knowledge gets in and how releases go out: `CONTRIBUTING.md`, `docs/releasing.md`.

## Layout

- `skills/<name>/SKILL.md` — a skill; `name` equals the directory name, `description` says what it does and when to use it. Extra material goes in `references/`. Picked up automatically by the wildcard in `agents.toml`.
- `agents/<name>.md` — a subagent; `name` equals the file name. Only `name`, `description`, and the body survive distribution, so constraints live in the body. Each one needs a `[[subagents]]` entry in `agents.toml` (`source = "path:."`, `path = "agents/<name>.md"`) and in `examples/agents.toml`.
- `instructions/AGENTS.md` — the managed rules block. It must start with `<!-- cm-ai-content:managed:start -->` and end with `<!-- cm-ai-content:managed:end -->`; it is loaded on every turn in every portal, so keep it short and portal-agnostic.
- `examples/` — the consumer contract (`agents.toml`, `devcontainer.json`), pinned to the next release tag.
- `scripts/` — `sync-repo-wiring.sh` (shipped to consumers), `validate.py` and `test-wiring.sh` (maintainers and CI).
- `docs/decisions/` — one record per decision, never rewritten; supersede with a new record.
- `evals/` — fixtures with deliberate problems; never "fix" them.

## Rules

- Public content only: no secrets, internal URLs, customer data, or proprietary details. `jpsmoreira-com/CM-AI-Content-Skills` is the published source.
- The git tag is the only version. `CHANGELOG.md` gets a line for every change under the next release heading; the examples pin that release.
- Do not add a manifest, an installer, or per-tool prompt/instruction files: skills and subagents ship through dotagents, guardrails through the managed block.
- Before finishing: `python3 scripts/validate.py`; `bash scripts/test-wiring.sh` when the wiring script changed; `npx --yes @sentry/dotagents@3.1.0 --project sync` after editing `skills/` or `agents/`.
- Do not push, tag, or publish unless explicitly asked.
