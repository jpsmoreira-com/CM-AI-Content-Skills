# Evals

Regression fixtures for the shared skills and agents. Not shipped to consumers and not run in CI: the runs need a model, so maintainers run them by hand before tagging a release and whenever a skill, agent, the style guide, or the glossary changes.

## How to run

Each suite has `cases/` (or `fixture/`) with planted problems and an `expected-findings.md` listing what a correct run must report. Run the skill/agent on the fixture and compare:

```bash
# style-guide-validator (from this repo root, in any tool with the skill installed)
/style-guide-validator evals/style-guide-validator/cases report

# docs-link-auditor
#   "run the docs-link-auditor agent on evals/docs-link-auditor/fixture/docs"
```

Grade manually (or paste both into the model and ask for a diff):

- **Recall**: every finding in `expected-findings.md` is reported. Missing must-fix findings = fail.
- **Precision**: no invented rules; false positives on the clean passages = fail.
- Report wording may differ; only the *findings* are graded.

If a deliberate behavior change alters the expected output, update `expected-findings.md` in the same PR and say so in the changelog.

## Adding cases

When a real-world miss is found (the validator let something through, the auditor missed a broken link), add a minimal case reproducing it. Keep cases small and one-problem-per-line where possible so grading stays easy.
