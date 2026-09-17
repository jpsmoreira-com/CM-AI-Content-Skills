# Releasing

The git tag is the only version. Consumers pin `@vX.Y.Z` in `agents.toml`; nothing else identifies a release.

## Public surface

A release promises consumers:

- the skill names under `skills/` and the subagent names under `agents/`;
- the managed-block markers in `instructions/AGENTS.md`;
- the command line and environment variables of `scripts/sync-repo-wiring.sh`;
- the shape of `examples/agents.toml` and `examples/devcontainer.json`.

Semantic versioning against that surface:

- **Patch** — wording, fixes, reference updates that change no names or behavior.
- **Minor** — new skills, subagents, or managed-block rules; new script options.
- **Major** — renamed or removed assets, marker changes, script CLI changes, new consumer requirements.

Tags are immutable: never move or delete a published tag; cut a new one.

## Flow

1. **Every PR** adds a line to `CHANGELOG.md` under the next release heading (`## 1.1.0 (unreleased)` — create it if missing). CI runs `scripts/validate.py`, the wiring tests, lint, and a dotagents install from the tree.
2. **Release PR**: set the heading to `## X.Y.Z - YYYY-MM-DD`, and set the pin in `examples/agents.toml` and `examples/devcontainer.json` to `vX.Y.Z`. `validate.py` fails if the three disagree.
3. Merge, then tag and push:

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

4. The `Release` workflow verifies the tag against `CHANGELOG.md` and the examples, installs the assets into a scratch portal **from the pushed tag** (dotagents install, doctor, wiring script), and publishes a GitHub Release whose notes are the changelog section.

If the release workflow fails, fix forward with a new patch tag; do not retag.

## Before tagging

- `python3 scripts/validate.py`, `bash scripts/test-wiring.sh`, and `npx --yes @sentry/dotagents@3.1.0 --project install && ... doctor` pass locally (CI runs the same).
- If a skill, subagent, the style guide, or the glossary changed, run the affected eval in `evals/` and confirm `expected-findings.md` still matches — or was updated on purpose, with a changelog line.
- Anything inside the managed block was reviewed by a content lead; every portal inherits it unconditionally.

## Public-safe content

Nothing in this repository may contain secrets, internal URLs, customer data, or proprietary details. GitHub secret scanning is enabled on the repository; keep examples generic.
