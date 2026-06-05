# CM AI Content Skills

Reusable public AI assets for devcontainers and development environments.

This repository is the source of truth for shared skills, agents, instructions, examples, and installer scripts that can be reused across projects without copying repository-specific guidance into each consumer.

## Contents

- `ai/` contains the canonical asset library.
- `ai/skills/` contains shared skills for Codex, GitHub Copilot, and Claude Code.
- `ai/agents/` contains reusable agent definitions.
- `ai/instructions/` contains shared instruction and prompt files.
- `ai/examples/` contains generic consumer examples.
- `ai/manifest.json` provides the machine-readable asset inventory.
- `scripts/install-ai-assets.sh` installs assets into a devcontainer or local development environment.
- `scripts/validate-ai-assets.sh` validates the asset layout before publishing.

See `ai/README.md` for the asset-library overview.

## Install From a Devcontainer

Use the Bash installer from a devcontainer `postCreateCommand`:

```json
{
  "postCreateCommand": "curl -fsSL https://raw.githubusercontent.com/usulpt/CM-AI-Content-Skills/main/scripts/install-ai-assets.sh | bash"
}
```

By default, the installer writes the canonical asset copy to `$HOME/.config/cm-ai-content` and installs supported skills into user-level folders for Codex, GitHub Copilot, and Claude Code.

For pinned versions, targeted installs, and wrapper-script examples, see `ai/docs/consuming-from-devcontainers.md`.

## Work on Assets

When adding, removing, renaming, or changing shared assets:

1. Put reusable skills under `ai/skills/`.
1. Put reusable agents under `ai/agents/`.
1. Put reusable instructions under `ai/instructions/`.
1. Put generic examples under `ai/examples/`.
1. Update `ai/manifest.json`.
1. Update `ai/CHANGELOG.md`.
1. Run validation before publishing.

```bash
bash scripts/validate-ai-assets.sh
```

Run `shellcheck` on shell scripts when it is available:

```bash
shellcheck scripts/*.sh
```

## Public Content Rules

Keep all shared content safe to publish. Do not include secrets, internal URLs, customer data, private credentials, proprietary information, or environment-specific tokens.

Use neutral placeholders such as `usulpt/CM-AI-Content-Skills`, `cm-ai-content`, and `example`.

## Documentation

- `ai/docs/consuming-from-devcontainers.md` explains consumer installation patterns.
- `ai/docs/publishing-and-versioning.md` explains release and versioning expectations.
- `ai/docs/troubleshooting.md` covers common installation issues.

Do not publish to npm, push to GitHub, or create Git tags unless that release action has been explicitly requested.
