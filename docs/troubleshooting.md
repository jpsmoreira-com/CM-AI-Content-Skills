# Troubleshooting AI Asset Installation

## dotagents

### `npm error ... Could not read package.json`

Something on the machine is rewriting the command (a shell alias, or a wrapper such as a token-saving proxy that intercepts anything containing `install`). Run the command through the wrapper's bypass or from a plain shell:

```bash
npx --yes @sentry/dotagents@3.0.1 --project install
```

### Skills went to `~/.agents` instead of the repository

You omitted `--project`. dotagents defaults to global scope. Re-run with `--project`; remove the global entries with `npx @sentry/dotagents remove <name>` if needed.

### `Ambiguous portable matches for subagent ...`

Only affects the CM-AI-Content-Skills repository itself (its subagent source is `path:.`, so a repeated `install` matches its own generated copy under `.agents/agents/`). Use `sync` after editing agents, or clean and reinstall:

```bash
npx --yes @sentry/dotagents@3.0.1 --project sync
# or
rm -rf .agents/agents && npx --yes @sentry/dotagents@3.0.1 --project install
```

Portals consume the GitHub source and never hit this.

### Skills missing or symlinks broken

```bash
npx @sentry/dotagents --project doctor --fix
```

### Wrong version installed

The version is the `@tag` in the `source` string of `agents.toml`. Check the tag exists:

```bash
git ls-remote --tags https://github.com/usulpt/CM-AI-Content-Skills.git v0.4.0
```

then `npx @sentry/dotagents --project install`.

### Node.js missing

dotagents needs Node.js 20+. Add a Node feature to the devcontainer image:

```json
{ "features": { "ghcr.io/devcontainers/features/node:1": { "version": "22" } } }
```

## Wiring script

### `DRIFT: AGENTS.md managed block`

The block in the portal differs from the release you are syncing. A plain run updates it; `--check` only reports. Portal-specific text must live outside the markers — anything inside them is overwritten.

### `MISSING: AGENTS.md has no managed block`

An `AGENTS.md` exists without markers. A plain run prepends the block; existing content is preserved below it.

### `DRIFT (kept): style-guide-full.md`

The portal's copy was edited. Either merge the change back into `skills/style-guide-validator/references/style-guide-full.md` here, or re-run with `--force` to overwrite.

### `curl` or `git` missing

`curl` is needed to fetch the wiring script; add it to the image or vendor the script into `.devcontainer/`.

## `postCreateCommand` failure

Run the command manually inside the devcontainer to see the full output, and check that the container has network access, Node.js 20+, and that `AI_ASSETS_REF` / the `@tag` point to an existing tag.

## Legacy Bash installer

`scripts/install-ai-assets.sh` is deprecated. If you still use it: it requires Git, resolves all asset folders from the repository root (falling back to the pre-0.4.0 `ai/` layout), and writes to `$HOME/.config/cm-ai-content` plus the user-level skill folders. To reset: `rm -rf "$HOME/.config/cm-ai-content" "$HOME/.cache/cm-ai-content-skills"`.
