# Troubleshooting

## Installing the CLI

### `apm: command not found`

The installer puts `apm` in `~/.local/bin`, which must be on `PATH`. `examples/devcontainer.json` sets it through `remoteEnv`; in a shell, `export PATH="$HOME/.local/bin:$PATH"`.

### Python version errors from the installer

The APM CLI needs Python 3.10+. In a devcontainer, start from `mcr.microsoft.com/devcontainers/python:3.12` (as the example does) or add the Python feature.

## `apm install`

### `Invalid APM dependency ... Invalid shorthand port`

The dependency is not in a form APM accepts. Use `owner/repo#vX.Y.Z`, a full HTTPS or SSH git URL, or a local path starting with `./`, `../`, or `/`. `file://` URLs are refused.

### The tag is not found

Check which tags exist: `apm view jpsmoreira-com/CM-AI-Content-Skills versions`, or `git ls-remote --tags https://github.com/jpsmoreira-com/CM-AI-Content-Skills.git`. Release notes list what each tag contains; an asset may postdate the tag you pinned.

### `--frozen` refuses to install

`apm.lock.yaml` is missing or no longer matches `apm.yml` (typically after bumping the pin). Run `apm install` without the flag, review the lockfile diff, and commit it.

### `Could not determine org from git remote` / `No org policy found at unknown`

APM's policy engine reads the organization from the portal's git remote and skipped enforcement because there is none (a fresh `mktemp` directory, for example). Harmless locally. To fail closed instead, set `policy.fetch_failure_default: block` in `apm.yml`.

### An unexpected subagent appears (for example `README`)

APM treats every file under `.apm/agents/` as an agent. On the portal side, keep that folder for agents only. On the publishing side, `scripts/validate.py` rejects anything there that is not `*.agent.md`.

## `apm compile`

### `Protected AGENTS.md: hand-authored file will not be overwritten`

The portal has an `AGENTS.md` without APM's generated marker, so compile left it alone — which means Codex is reading the old file, not the current guardrails. Move the portal-specific text into `.apm/instructions/portal-rules.instructions.md`, delete `AGENTS.md`, and run `apm compile` again (see the migration section in [consuming.md](consuming.md)).

### `No 'applyTo' pattern specified -- instruction will apply globally`

Expected for the shared guardrails and for any portal rule meant to load on every turn. Add `applyTo:` only to rules that should attach to matching files.

### `Referenced file not found: ... (in link ...)`

APM resolves Markdown links inside primitives at compile time. Prose that merely shows link syntax can trigger it; the warning does not block anything. Real broken links in a portal's own instructions should be fixed.

### `CLAUDE.md not generated -- Claude Code reads .claude/rules/ directly`

Informational. Claude Code loads the guardrails from `.claude/rules/cm-ai-content.md`; a `CLAUDE.md` is not needed.

## `apm audit --ci` reports drift

### After adding a second package

Two packages ship a primitive with the same name. APM deploys different copies to different harness folders instead of picking one, and the lockfile records both. Rename or drop the clashing package; `apm install --force` only hides the problem.

### After editing an installed file

A deployed file differs from what the lockfile recorded, usually a hand edit to an installed copy (for example `.github/instructions/cm-ai-content.instructions.md`). Installed files are overwritten on the next install; put the change in the portal's own `.apm/instructions/` instead, or in this repository if every portal should get it. `apm install` restores the recorded content.

## `postCreateCommand` failure

Run the command by hand inside the container to see the full output. The usual causes are no network, Python older than 3.10, `~/.local/bin` not on `PATH`, or a tag that does not exist.
