#!/usr/bin/env bash
# Consumer smoke test: install this package into a portal directory that already holds an
# apm.yml, then assert every primitive reached every harness the contract promises.
# Used by CI (dependency = the checkout) and by the release workflow (dependency = the tag).
#
#   scripts/smoke-portal.sh <portal-dir>
set -euo pipefail

portal="${1:?usage: smoke-portal.sh <portal-dir>}"
cd "$portal"
test -f apm.yml
git init -q .

# The portal's own rule must compile alongside the shared guardrails, portal rule first.
mkdir -p .apm/instructions
printf -- '---\ndescription: Portal-specific rules\n---\n- PORTAL-RULE: never edit files under generated/.\n' \
  > .apm/instructions/portal-rules.instructions.md

apm install
apm compile

# Skills: the shared .agents/skills/ path is what Codex and Copilot read natively.
for skill in style-guide-validator tutorial-source-to-mkdocs docs-change-summary; do
  test -f ".agents/skills/$skill/SKILL.md"
  test -f ".claude/skills/$skill/SKILL.md"
done
# Subagents reach all three harnesses, including GitHub Copilot.
for agent in docs-style-reviewer docs-link-auditor; do
  test -f ".github/agents/$agent.agent.md"
  test -f ".claude/agents/$agent.md"
  test -f ".codex/agents/$agent.toml"
done
# Guardrails: native per harness, and folded into AGENTS.md for Codex.
test -f .github/instructions/cm-ai-content.instructions.md
test -f .claude/rules/cm-ai-content.md
grep -q "Content AI Shared Rules" .github/copilot-instructions.md
grep -q "Content AI Shared Rules" AGENTS.md
grep -q "PORTAL-RULE" AGENTS.md
# The guardrails must stay unconditional: no applyTo may have crept in.
! grep -q "^applyTo:" .github/instructions/cm-ai-content.instructions.md

# What a portal commits must reproduce exactly and audit clean.
apm install --frozen
apm audit --ci
echo "OK: consumer smoke test passed in $portal"
