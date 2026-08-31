# Contributing

This repository only compounds in value if what the team learns flows back into it. The core rule:

> **If you correct the AI twice for the same thing, it belongs here.**
> A wording fix → the style guide or glossary. A recurring workflow → a skill. A "never do this" → the managed `AGENTS.md` block. A "we chose X over Y" → a decision record.

## Where each kind of knowledge goes

| You learned... | Put it in | Ships to portals via |
| --- | --- | --- |
| A wording/formatting rule | `skills/style-guide-validator/references/style-guide-full.md` | bundled with the skill + wiring script |
| An approved/forbidden term | `skills/style-guide-validator/references/terminology-glossary.md` | bundled with the skill |
| A repeatable workflow | a skill under `skills/` | dotagents |
| A delegated review/audit routine | a subagent under `agents/` | dotagents |
| An always-on guardrail | the managed block in `instructions/AGENTS.md` — keep it short, it loads every turn | wiring script |
| Why we decided something | `docs/decisions/` | stays here (reference) |
| A great page worth imitating | `skills/tutorial-source-to-mkdocs/references/golden-examples/` | bundled with the skill |

## How to contribute

1. Branch, make the change, and update `CHANGELOG.md` (and `manifest.json` + `agents.toml` for new skills/agents).
1. Run `bash scripts/validate-ai-assets.sh`.
1. If you touched a skill with an eval suite, run the eval (see `evals/README.md`) and update expected findings if the change intends a behavior change.
1. Open a PR. A content lead reviews rule changes; anything in the managed block gets extra scrutiny because every portal inherits it unconditionally.
1. Releases are tagged (`vX.Y.Z`); portals adopt by bumping the tag in their `agents.toml` and `AI_ASSETS_REF` in a reviewed PR. See `docs/publishing-and-versioning.md`.

## Quality bar

- Public-safe only: no secrets, internal URLs, customer data, or proprietary details.
- Prefer editing an existing asset over adding a near-duplicate. Five maintained assets beat twenty stale ones.
- Every rule should say *why* when the why isn't obvious — that's what makes it stick, for people and for models.
