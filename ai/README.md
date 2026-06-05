# CM AI Content Skills

This directory contains reusable AI assets that can be installed into devcontainers and development environments from a public GitHub repository.

The library includes:

- Shared skills in `skills/` for Codex, GitHub Copilot, and Claude Code
- A shared style guide bundled with the `style-guide-validator` skill
- Shared agent definitions in `agents/`
- Reusable instruction and prompt files in `instructions/`
- Consumer examples in `examples/`
- A machine-readable inventory in `manifest.json`

Consuming repositories should keep repository-specific guidance in their own `AGENTS.md` files and use this library only for shared, public-safe behavior.

## Install

Use the Bash installer from a devcontainer `postCreateCommand`:

```json
{
  "postCreateCommand": "curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | bash"
}
```

By default, assets are installed to `$HOME/.config/cm-ai-content`, and shared skills are also installed to the supported tool-specific user skill folders.

## Configuration

The installer supports these environment variables:

- `AI_ASSETS_REPO_URL`
- `AI_ASSETS_REF`
- `AI_ASSETS_PATH`
- `AI_INSTALL_DIR`
- `AI_CACHE_DIR`
- `AI_INSTALL_TARGETS`

See `docs/consuming-from-devcontainers.md` in this asset library for usage examples.
