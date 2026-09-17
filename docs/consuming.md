# Consuming the Assets in a Portal

A documentation portal consumes this repository with [APM](https://github.com/microsoft/apm), Microsoft's Agent Package Manager. One manifest, two commands, one commit:

1. `apm install` deploys the skills, the subagents, and the always-on guardrails into the folders each AI tool reads.
2. `apm compile` folds the guardrails, together with any portal-specific rules, into `AGENTS.md`.

Everything is pinned to one release tag in the portal's `apm.yml`; `apm.lock.yaml` records the exact content hashes.

## Requirements

- Python 3.10+ (the APM CLI is a Python program; the installer sets up its own environment).
- `curl` to fetch the installer.
- An AI tool that supports Agent Skills: [Claude Code](https://code.claude.com/docs/en/skills), [Codex](https://developers.openai.com/codex/skills), or [GitHub Copilot](https://code.visualstudio.com/docs/agent-customization/agent-skills).

## 1. Install the APM CLI

```bash
curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.31.0
```

The binary lands in `~/.local/bin`; make sure that is on `PATH`. Pin the version: APM is pre-1.0 and releases often. Windows: `irm https://aka.ms/apm-windows | iex` (see the [APM install docs](https://microsoft.github.io/apm/getting-started/installation/) for pinning).

## 2. Declare the dependency

Copy [`examples/apm.yml`](../examples/apm.yml) to the portal root and commit it:

```yaml
name: my-docs-portal
version: 0.1.0
targets:
  - copilot
  - claude
  - codex
dependencies:
  apm:
    - jpsmoreira-com/CM-AI-Content-Skills#v0.4.0
  mcp: []
```

- `#v0.4.0` is the version pin. Bump it in a reviewed PR to adopt a new release.
- `targets` names the tools to deploy to. Pinning them keeps every machine and CI run producing the same files; without it APM guesses from what it finds on disk.
- `name` and `version` describe the portal itself (APM requires both) and never need to change.

## 3. Install and compile

```bash
apm install
apm compile
```

`apm install` writes `apm.lock.yaml` and deploys every primitive. `apm compile` generates `AGENTS.md` (and `.github/copilot-instructions.md`) from the installed guardrails plus the portal's own instructions. Commit all of it:

```text
apm.yml                          committed — the pin
apm.lock.yaml                    committed — exact content hashes, what `--frozen` reproduces
AGENTS.md                        committed — compiled: portal rules first, then the shared guardrails
.github/copilot-instructions.md  committed — compiled, same content, for Copilot
.github/instructions/            committed — the guardrails, Copilot's native form
.github/agents/                  committed — the subagents for Copilot
.claude/rules/, .claude/agents/, .claude/skills/   committed — Claude Code
.codex/agents/                   committed — Codex
.agents/skills/                  committed — the skills, read natively by Codex and Copilot
.gitignore                       committed — APM adds `apm_modules/` (its package cache)
```

Committing the deployed tree is APM's model: a fresh clone, CI, and cloud agents such as the Copilot coding agent all see the same files without running anything. `apm install --frozen` refuses to run if the lockfile and `apm.yml` disagree, and `apm audit --ci` fails on drift between the lockfile and what is on disk.

## 4. Portal-specific skills, subagents, and rules

A portal authors its own primitives in its own `.apm/`, next to `apm.yml`. No configuration is needed: `apm install` treats the portal root as a package and deploys them alongside the installed ones, to the same folders.

```text
.apm/
  skills/<name>/SKILL.md              -> .agents/skills/, .claude/skills/
  agents/<name>.agent.md              -> .github/agents/, .claude/agents/, .codex/agents/
  instructions/<name>.instructions.md -> .github/instructions/, .claude/rules/, and AGENTS.md
```

A rule that should load on every turn:

```markdown
---
description: Rules for this portal's build pipeline
---
- Never edit files under `generated/`; change the generator instead.
```

`apm compile` folds it into `AGENTS.md` ahead of the shared guardrails. Add `applyTo: "docs/**/*.md"` to scope a rule to matching files instead. Skills and subagents use the same frontmatter as the shared ones (`name` equal to the directory or file name, plus `description`); `apm compile --validate` checks them.

Keep local names distinct from the shared ones. A local primitive with the same name as an installed one wins everywhere, but `apm audit --ci` then reports the installed copy as drifted and stays red. To change a shared skill, change it in this repository, so every portal gets it; to disable one, do not shadow it, delete it from the portal after install.

Commit `.apm/` with the rest of the deployed tree. Skills or subagents that several portals need belong in a package of their own, installed beside this one (see [Using more than one package](#using-more-than-one-package)).

## 5. Devcontainer

[`examples/devcontainer.json`](../examples/devcontainer.json) installs the pinned CLI and runs `apm install --frozen && apm compile` on every rebuild, so a writer's machine needs nothing else. Node.js is not required. Merge its `postCreateCommand` and `remoteEnv` into the portal's existing devcontainer rather than replacing it, and commit `apm.lock.yaml` before the first rebuild: `--frozen` refuses to run without it.

## Compatibility

| Asset | GitHub Copilot | Claude Code | Codex |
| --- | --- | --- | --- |
| Skills | `.agents/skills/`, invoked as `/name` | `.claude/skills/`, invoked as `/name` | `.agents/skills/`, invoked as `$name` |
| Subagents | `.github/agents/<name>.agent.md` | `.claude/agents/<name>.md` | `.codex/agents/<name>.toml` |
| Always-on guardrails | `.github/instructions/` and `.github/copilot-instructions.md` | `.claude/rules/cm-ai-content.md` | compiled into `AGENTS.md` |

Codex reads the guardrails only from `AGENTS.md`, so `apm compile` is not optional.

## Using more than one package

`dependencies.apm` is a list, and any git repository is a package, so a portal can combine this one with others:

```yaml
dependencies:
  apm:
    - jpsmoreira-com/CM-AI-Content-Skills#v0.4.0
    - some-org/other-skills#v3.2.0
  mcp: []
```

Every package's skills, subagents, and instructions deploy side by side; instructions from all of them compile into `AGENTS.md`. `apm deps list` shows what each package contributed.

Names must be unique across every package a portal declares. When two packages ship a skill with the same name, APM 0.31.0 deploys one package's copy to `.agents/skills/` and the other's to `.claude/skills/`, so Copilot and Claude Code run different skills under one name; the only signal is a misleading `1 file skipped -- local files exist` line at install time and a `Drift detected` failure from `apm audit --ci`. Keep the audit in portal CI, and drop or rename the clashing package rather than forcing the install.

## Updating to a new release

1. Change the `#vX.Y.Z` in `apm.yml` to the new tag.
2. Run `apm install` (without `--frozen`: the manifest changed) and `apm compile`.
3. Review the diff of `AGENTS.md` and the deployed files, then commit everything including `apm.lock.yaml`.

## Migrating from the unreleased dotagents contract

No release ever shipped dotagents, but `main` carried that contract for a while; a portal set up from it migrates like this:

1. Delete `agents.toml`, `agents.lock`, the `.claude/skills` symlink, `.claude/agents/`, `.codex/agents/`, and the dotagents entries in `.gitignore`.
2. In `AGENTS.md`, move everything below the old managed block's end marker into `.apm/instructions/portal-rules.instructions.md` (add the `description` frontmatter), then delete `AGENTS.md`. `apm compile` never overwrites a hand-authored `AGENTS.md`, so an old one would silently keep Codex on the stale rules.
3. Keep `CLAUDE.md` if it exists; it is harmless.
4. Follow steps 1 to 3 above and replace the devcontainer's `postCreateCommand`.

## Recommended portal CI

```yaml
- run: curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.31.0 && echo "$HOME/.local/bin" >> "$GITHUB_PATH"
- run: apm install --frozen
- run: apm audit --ci
- run: apm compile
- run: git diff --exit-code   # the committed tree matches the lockfile
```
