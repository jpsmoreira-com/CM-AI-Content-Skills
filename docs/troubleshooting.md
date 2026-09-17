# Troubleshooting

## dotagents

### Skills went to `~/.agents` instead of the repository

`--project` was omitted; dotagents defaults to the global scope. Re-run with `--project`, and remove the global entries with `npx --yes @sentry/dotagents@3.1.0 remove <name>` if needed.

### `Failed to resolve skill ... not found`

The `@tag` in `agents.toml` does not exist, or the tag predates the asset. Check: `git ls-remote --tags https://github.com/jpsmoreira-com/CM-AI-Content-Skills.git`. Release notes list what each tag contains.

### Skills missing or symlinks broken

`install` fetches missing skills; `sync` repairs the symlinks and generated tool files; `doctor` reports what is wrong (`doctor --fix` only repairs `.gitignore` entries and tracked generated files).

```bash
npx --yes @sentry/dotagents@3.1.0 --project install
npx --yes @sentry/dotagents@3.1.0 --project sync
npx --yes @sentry/dotagents@3.1.0 --project doctor
```

### Warnings about `agents.lock` or `.agents/.gitignore` not being ignored

Run the wiring script (it appends the entries) or `npx --yes @sentry/dotagents@3.1.0 --project doctor --fix`.

### Node.js missing

dotagents needs Node.js 20+. In a devcontainer: `"features": { "ghcr.io/devcontainers/features/node:1": {} }`.

## Wiring script

### `no release given`

Running remotely, the script needs a tag: pin `CM-AI-Content-Skills@vX.Y.Z` in `agents.toml`, or pass `--ref vX.Y.Z` / set `AI_ASSETS_REF`.

### `AI_ASSETS_REF is ... but agents.toml pins ...`

The devcontainer's `AI_ASSETS_REF` and the pin in `agents.toml` disagree. Set both to the same tag; rules and skills are released together.

### `could not fetch https://raw.githubusercontent.com/...`

The tag does not exist or the container has no network. Verify the tag, or vendor the script into `.devcontainer/` from the pinned tag.

### `DRIFT: AGENTS.md managed block`

The block in the portal differs from the pinned release. A plain run updates it; `--check` only reports. Portal-specific text must live outside the markers — anything inside them is overwritten.

### `MISSING: AGENTS.md has no managed block`

An `AGENTS.md` exists without markers. A plain run prepends the block and keeps the existing content below it.

## `postCreateCommand` failure

Run the command by hand inside the container to see the full output. The usual causes are no network, no Node.js, or a tag that does not exist.
