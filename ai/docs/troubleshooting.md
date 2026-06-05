# Troubleshooting AI Asset Installation

Use this guide when a devcontainer cannot install shared AI assets from the public repository.

## Git Missing

The installer requires Git. Add a Git feature or package to the devcontainer image.

Example devcontainer feature:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  }
}
```

## curl Missing

`curl` is needed only when downloading the installer with `curl | bash` or a wrapper script. Install `curl` in the image or replace the wrapper with another download method available in the container.

## Wrong GitHub URL

Set `AI_ASSETS_REPO_URL` to the public Git repository URL:

```bash
export AI_ASSETS_REPO_URL="https://github.com/usulpt/CM-AI-Content-Skills.git"
```

If using a raw GitHub URL to download the installer, make sure the `OWNER`, `REPO`, and branch or tag are correct.

## Missing Tag or Ref

If installation fails for a pinned version, confirm that the tag exists:

```bash
git ls-remote --tags https://github.com/usulpt/CM-AI-Content-Skills.git v0.1.0
```

Then retry with:

```bash
AI_ASSETS_REF=v0.1.0 bash .devcontainer/sync-ai-assets.sh
```

## Missing Asset Path

The default asset path is `ai`. If the public repository stores assets elsewhere, set:

```bash
export AI_ASSETS_PATH="path/to/ai"
```

The path must contain `agents/`, `skills/`, `instructions/`, `examples/`, and `manifest.json`.

## Stale Installed Assets

The installer uses delete-aware sync so removed source files are removed from the install directory. To force a completely fresh install, remove the install and cache directories:

```bash
rm -rf "$HOME/.config/cm-ai-content" "$HOME/.cache/cm-ai-content-skills"
```

Then rebuild the devcontainer or rerun the installer.

## `postCreateCommand` Failure

Run the command manually inside the devcontainer to see the full output:

```bash
curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | bash
```

Check that:

- the container has network access
- Git is installed
- the GitHub URL is public and reachable
- `AI_ASSETS_REF` points to an existing branch, tag, or commit
- `$HOME` is writable for the devcontainer user

## Target-Specific Checks

The installer uses `AI_INSTALL_TARGETS=all` by default. To narrow the install, set a comma-separated list:

```bash
curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | AI_INSTALL_TARGETS=codex,copilot,claude bash
```

Check the target folders after installation:

- Codex-compatible skills: `$HOME/.agents/skills`
- GitHub Copilot skills: `$HOME/.copilot/skills`
- Claude Code skills: `$HOME/.claude/skills`

If a target folder is missing, confirm that `AI_INSTALL_TARGETS` includes that target or is set to `all`.

## Future npx Migration

The repository can later add an npm package that wraps the same installer behavior. Until then, keep consuming repositories on the Bash installer and pin `AI_ASSETS_REF` to a release tag when stable setup is required.
