## What changed and why

<!-- Reader-facing summary. What does a portal get, or what does a maintainer gain? -->

## Checklist

- [ ] `CHANGELOG.md` has an entry under the next release heading.
- [ ] `python3 scripts/validate.py` passes.
- [ ] If a skill, agent, the style guide, or the glossary changed: the eval in `evals/` still matches, or `expected-findings.md` was updated on purpose.
- [ ] Anything inside the managed block (`instructions/AGENTS.md`) was reviewed by a content lead: every portal inherits it unconditionally.
