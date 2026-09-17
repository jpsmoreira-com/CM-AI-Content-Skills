# Releasing

The git tag is the only version. Consumers pin `#vX.Y.Z` in `apm.yml`; nothing else identifies a release.

## Public surface

A release promises consumers:

- the skill names under `.apm/skills/` and the subagent names under `.apm/agents/`;
- the guardrails instruction `.apm/instructions/cm-ai-content.instructions.md`, unconditional (no `applyTo`);
- the shape of `examples/apm.yml` and `examples/devcontainer.json`, including the pinned APM CLI version.

Semantic versioning against that surface:

- **Patch** — wording, fixes, reference updates that change no names or behavior.
- **Minor** — new skills, subagents, or guardrail rules.
- **Major** — renamed or removed assets, a new instruction name, a new consumer requirement (for example a newer APM CLI with breaking changes).

Tags are immutable: never move or delete a published tag; cut a new one.

## Flow

1. **Every PR** adds a line to `CHANGELOG.md` under the next release heading (`## 0.5.0 (unreleased)` — create it if missing, and set `version:` in `apm.yml` and the pin in `examples/apm.yml` to match). CI runs `scripts/validate.py`, `apm compile --validate`, a dogfood install with `apm audit --ci`, the consumer smoke test, and lint.
2. **Release PR**: set the heading to `## X.Y.Z - YYYY-MM-DD`. `validate.py` fails if `apm.yml`, the changelog, and `examples/apm.yml` disagree.
3. Merge, then tag and push:

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

4. The `Release` workflow verifies the tag against `apm.yml`, `CHANGELOG.md`, and the example pin, installs the package into a scratch portal **from the pushed tag** (`scripts/smoke-portal.sh` asserts every primitive reached every harness), and publishes a GitHub Release whose notes are the changelog section.

If the release workflow fails, fix forward with a new patch tag; do not retag.

## Before tagging

- `python3 scripts/validate.py`, `apm compile --validate`, and `apm install && apm audit --ci` pass locally.
- The consumer smoke test passes against the checkout:

  ```bash
  portal="$(mktemp -d)"
  sed -e "s#- jpsmoreira-com/CM-AI-Content-Skills\#v.*#- $PWD#" examples/apm.yml > "$portal/apm.yml"
  bash scripts/smoke-portal.sh "$portal"
  ```

- If a skill, subagent, the style guide, or the glossary changed, run the affected eval in `evals/` and confirm `expected-findings.md` still matches — or was updated on purpose, with a changelog line.
- Anything in the guardrails instruction was reviewed by a content lead; every portal inherits it unconditionally.

## Bumping the APM CLI

The CLI version appears in `examples/devcontainer.json`, both workflows, and the docs; `validate.py` fails when they disagree. APM is pre-1.0, so bump deliberately: run the smoke test on the new version first, and treat a bump that changes what lands in portals as a minor release at least.

## Public-safe content

Nothing in this repository may contain secrets, internal URLs, customer data, or proprietary details. GitHub secret scanning is enabled on the repository; keep examples generic.
