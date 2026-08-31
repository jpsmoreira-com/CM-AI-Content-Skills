# Publishing and Versioning AI Assets

This repository is the source of truth for reusable public AI assets. Keep assets generic, public-safe, and backward compatible when possible.

## Updating Assets

1. Add or change skills under `skills/` (a directory with a `SKILL.md` that has at least `name` and `description`).
1. Add or change subagents under `agents/`.
1. Add always-on rules to the managed block in `instructions/AGENTS.md`. Keep it short — it is loaded on every turn in every consumer. On-demand workflows belong in a skill, not here.
1. Register new skills/agents in `manifest.json` and in `agents.toml` (with a `path:` source).
1. Update examples under `examples/` if the consumer contract changed.
1. Update `CHANGELOG.md`.
1. Run `scripts/validate-ai-assets.sh` and `npx @sentry/dotagents --project install && npx @sentry/dotagents --project doctor`.

## Versioning

Use semantic versions for the asset library:

- Patch versions for compatible fixes and documentation updates.
- Minor versions for new skills, agents, managed-block rules, or script options.
- Major versions for breaking layout, manifest, managed-block marker, or script behavior changes.

Set the same version in `manifest.json` and `CHANGELOG.md`.

## Stable Releases

Consumers pin to Git tags in two places: the `@tag` in each `agents.toml` source and the `AI_ASSETS_REF` used to fetch `sync-repo-wiring.sh`. Keep them equal.

```bash
git tag v0.4.0
git push origin v0.4.0
```

Do not create tags until the release is reviewed and ready.

## Public-Safe Content

Do not publish:

- secrets or credentials
- internal URLs
- customer data
- proprietary implementation details
- private tokens or keys

Use neutral placeholders such as `usulpt/CM-AI-Content-Skills`, `cm-ai-content`, and `example`.
