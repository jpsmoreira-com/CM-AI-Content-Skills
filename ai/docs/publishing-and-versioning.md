# Publishing and Versioning AI Assets

This repository is the source of truth for reusable public AI assets. Keep assets generic, public-safe, and backward compatible when possible.

## Updating Assets

When adding or changing assets:

1. Add reusable skills under `ai/skills/`.
1. Add reusable agents under `ai/agents/`.
1. Add reusable instructions under `ai/instructions/`.
1. Add examples under `ai/examples/`.
1. Update `ai/manifest.json`.
1. Update `ai/CHANGELOG.md`.
1. Run `scripts/validate-ai-assets.sh`.

Each Codex skill must be a directory with a `SKILL.md` file that includes at least `name` and `description` metadata.

## Versioning

Use semantic versions for the asset library:

- Patch versions for compatible fixes and documentation updates.
- Minor versions for new skills, agents, instructions, or installer options.
- Major versions for breaking layout, manifest, or behavior changes.

Set the same version in `ai/manifest.json` and `ai/CHANGELOG.md`.

## Stable Releases

Use Git tags for stable releases, for example:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Do not create tags until the release is reviewed and ready. Consuming repositories can pin `AI_ASSETS_REF` to a tag for repeatable devcontainer setup.

## Public-Safe Content

Do not publish:

- secrets or credentials
- internal URLs
- customer data
- proprietary implementation details
- private tokens or keys

Use neutral placeholders such as `usulpt/CM-AI-Content-Skills`, `cm-ai-content`, and `example`.

## Future npx Package

The Bash installer is the primary devcontainer path for now. A later npm package can expose:

- `cm-ai-content-skills sync`
- `cm-ai-content-skills list`
- `cm-ai-content-skills doctor`

Keep the Bash installer stable so an npx wrapper can delegate to it later.
