# Contributing

This repository only compounds in value if what the team learns flows back into it. The core rule:

> **If you correct the AI twice for the same thing, it belongs here.**
> A wording fix → the style guide or glossary. A recurring workflow → a skill. A "never do this" → the guardrails instruction. A "we chose X over Y" → a decision record.

## Where each kind of knowledge goes

| You learned... | Put it in | Ships to portals via |
| --- | --- | --- |
| A wording/formatting rule | `.apm/skills/style-guide-validator/references/style-guide-full.md` | bundled with the skill |
| An approved/forbidden term | `.apm/skills/style-guide-validator/references/terminology-glossary.md` | bundled with the skill |
| A repeatable workflow | a skill under `.apm/skills/` | `apm install` (picked up automatically) |
| A delegated review/audit routine | a subagent under `.apm/agents/` | `apm install`, to Copilot, Claude Code, and Codex |
| An always-on guardrail | `.apm/instructions/cm-ai-content.instructions.md` — keep it short, it loads every turn | `apm install` + `apm compile` |
| Why we decided something | `docs/decisions/` | stays here (reference) |
| A great page worth imitating | `.apm/skills/tutorial-source-to-mkdocs/references/golden-examples/` | bundled with the skill |

## Adding a subagent

1. Create `.apm/agents/<name>.agent.md` with `name` (equal to the file name without `.agent.md`) and `description` frontmatter, then the body. The description is what Copilot and Claude Code show when surfacing the agent, so say what it does and when to use it.
1. State behavioral limits such as "read-only, never edit files" in the body. APM deploys the file verbatim to Copilot and converts it for Claude Code and Codex; the body is the only part every harness reads the same way.
1. Nothing else may live in `.apm/agents/`: APM treats every file there as an agent. Notes go here or in `docs/`.
1. Run `python3 scripts/validate.py` and `apm compile --validate`, then `apm install` to see it land in `.github/agents/`, `.claude/agents/`, and `.codex/agents/`.

Skills follow the same pattern under `.apm/skills/<name>/SKILL.md`; the wildcard `includes: auto` in `apm.yml` publishes them without registration.

## How to contribute

1. Branch, make the change, and add a line to `CHANGELOG.md` under the next release heading.
1. Run `python3 scripts/validate.py` and `apm compile --validate`. CI runs the same, plus a dogfood `apm install` and `apm audit --ci`, a consumer smoke test (`scripts/smoke-portal.sh`), and markdownlint.
1. If you touched a skill or agent with an eval suite — or the style guide or glossary they read — run the eval (see `evals/README.md`) and update `expected-findings.md` only for an intended behavior change.
1. Open a PR. A content lead reviews rule changes; anything in the guardrails instruction gets extra scrutiny because every portal inherits it unconditionally.
1. Releases are tags; portals adopt by bumping the `#vX.Y.Z` in their `apm.yml`. See `docs/releasing.md`.

## Quality bar

- Public-safe only: no secrets, internal URLs, customer data, or proprietary details.
- Prefer editing an existing asset over adding a near-duplicate. Five maintained assets beat twenty stale ones.
- Every rule should say *why* when the why isn't obvious — that's what makes it stick, for people and for models.
- Skill descriptions say what the skill does *and* when to use it; subagent constraints ("read-only") go in the body.
- Names are part of the contract and must stay specific (`style-guide-validator`, not `validator`): a portal may install other packages alongside this one, and APM handles cross-package name clashes badly (see `docs/consuming.md`).
- The guardrails instruction never sets `applyTo`: it must load on every turn in every harness, and `validate.py` enforces that.
