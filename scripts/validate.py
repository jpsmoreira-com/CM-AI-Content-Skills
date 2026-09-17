#!/usr/bin/env python3
"""Validate the asset layout of CM-AI-Content-Skills before publishing.

Structural checks only (no network): skills and subagents follow the Agent Skills /
dotagents conventions, agents.toml and examples/ describe exactly what is on disk, the
managed AGENTS.md block is well-formed, internal links resolve, and the release pin is
consistent between CHANGELOG.md and the examples. Prints one line per problem; exit 1
on any problem.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"
START_MARK = "<!-- cm-ai-content:managed:start -->"
END_MARK = "<!-- cm-ai-content:managed:end -->"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+)$")
DOTAGENTS_RE = re.compile(r"@sentry/dotagents@(\d+\.\d+\.\d+)")
# Tools configured by both manifests. "copilot" needs dotagents >= 3.1.0; it writes no
# project files (Copilot reads .agents/skills/ natively) but must stay declared so CI
# installs against it. dotagents has no Copilot subagent format, hence SUBAGENT_TARGETS.
EXPECTED_AGENTS = ["claude", "codex", "copilot"]
SUBAGENT_TARGETS = ["claude", "codex"]
SKILL_KEYS = {"name", "description", "argument-hint", "license", "compatibility", "metadata", "allowed-tools"}
# Files whose links are intentionally broken (fixtures and illustrative examples).
LINK_EXCLUDES = ("evals/", "skills/tutorial-source-to-mkdocs/references/golden-examples/", "skills/style-guide-validator/references/style-guide-full.md")

problems: list[str] = []


def problem(path: Path | str, message: str) -> None:
    rel = path.relative_to(ROOT) if isinstance(path, Path) else path
    problems.append(f"{rel}: {message}")


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Parse a flat YAML frontmatter block (scalar values only) and return (fields, body)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        problem(path, "missing frontmatter")
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        problem(path, "unterminated frontmatter")
        return {}, text
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue  # nested value (e.g. metadata:), keep the parent key only
        key, sep, value = line.partition(":")
        if not sep:
            problem(path, f"invalid frontmatter line: {line!r}")
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields, text[end + 5:]


def check_links(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith(LINK_EXCLUDES):
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", text):
        target = match.group(1).split("#", 1)[0]
        if not target or re.match(r"^[a-z]+:", target):
            continue
        if not (path.parent / target).exists():
            problem(path, f"broken link: {match.group(1)}")


def check_skills() -> None:
    if not SKILLS.is_dir():
        problem("skills", "missing directory")
        return
    for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        skill = skill_dir / "SKILL.md"
        if not skill.is_file():
            problem(skill_dir, "missing SKILL.md")
            continue
        fields, body = frontmatter(skill)
        name = fields.get("name", "")
        if name != skill_dir.name:
            problem(skill, f"frontmatter name {name!r} must equal the directory name")
        if not NAME_RE.match(name) or len(name) > 64:
            problem(skill, "name must be lowercase letters, digits and single hyphens, at most 64 characters")
        description = fields.get("description", "")
        if not description:
            problem(skill, "description is required")
        elif len(description) > 1024:
            problem(skill, f"description is {len(description)} characters, limit is 1024")
        for key in fields.keys() - SKILL_KEYS:
            problem(skill, f"unexpected frontmatter key {key!r}")
        if not body.strip():
            problem(skill, "empty body")
        lines = skill.read_text(encoding="utf-8").count("\n")
        if lines > 500:
            problem(skill, f"{lines} lines, keep SKILL.md under 500 lines and move detail to references/")
        for md in skill_dir.rglob("*.md"):
            check_links(md)


def check_agents() -> set[str]:
    names: set[str] = set()
    if not AGENTS.is_dir():
        problem("agents", "missing directory")
        return names
    for agent in sorted(AGENTS.glob("*.md")):
        if agent.name == "README.md":
            check_links(agent)
            continue
        fields, body = frontmatter(agent)
        name = fields.get("name", "")
        if name != agent.stem:
            problem(agent, f"frontmatter name {name!r} must equal the file name")
        if not NAME_RE.match(name):
            problem(agent, "name must be lowercase letters, digits and single hyphens")
        if not fields.get("description"):
            problem(agent, "description is required")
        for key in ("tools", "model"):
            if key in fields:
                problem(agent, f"{key!r} is dropped by dotagents for every target; state the constraint in the body instead")
        if not body.strip():
            problem(agent, "empty body (dotagents rejects subagents without a body)")
        names.add(agent.stem)
    return names


def load_toml(path: Path) -> dict | None:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        problem(path, f"cannot parse: {exc}")
        return None


def check_agent_list(path: Path, data: dict) -> None:
    """Both manifests must configure the same tools, so a portal matches what CI installs."""
    agents = data.get("agents")
    if agents != EXPECTED_AGENTS:
        problem(path, f"agents must be {EXPECTED_AGENTS}, got {agents!r}")


def check_subagent_targets(path: Path, sub: dict) -> None:
    targets = sub.get("targets")
    if targets != SUBAGENT_TARGETS:
        problem(
            path,
            f"subagent {sub.get('name')}: targets must be {SUBAGENT_TARGETS} "
            "(dotagents has no Copilot subagent format)",
        )


def check_dotagents_version() -> None:
    """The dotagents version is repeated in docs, CI and the devcontainer; keep them equal."""
    files = sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md"))
    files += [ROOT / "agents.toml", ROOT / "agents" / "README.md", ROOT / "examples" / "devcontainer.json"]
    files += sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    found: dict[str, list[str]] = {}
    for f in files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        versions = set(DOTAGENTS_RE.findall(text))
        versions |= set(re.findall(r"DOTAGENTS_VERSION:\s*(\d+\.\d+\.\d+)", text))
        for v in versions:
            found.setdefault(v, []).append(str(f.relative_to(ROOT)))
    if len(found) > 1:
        detail = "; ".join(f"{v} in {', '.join(sorted(p))}" for v, p in sorted(found.items()))
        problem("scripts/validate.py", f"dotagents version disagrees across files: {detail}")


def check_agents_toml(agent_names: set[str]) -> None:
    path = ROOT / "agents.toml"
    data = load_toml(path)
    if data is None:
        return
    if data.get("version") != 1:
        problem(path, "version must be 1")
    check_agent_list(path, data)
    skills = data.get("skills", [])
    if not any(s.get("name") == "*" and s.get("source") == "path:." and s.get("path") == "skills" for s in skills):
        problem(path, 'expected a wildcard entry: name = "*", source = "path:.", path = "skills"')
    declared: set[str] = set()
    for sub in data.get("subagents", []):
        name = sub.get("name", "")
        declared.add(name)
        if sub.get("source") != "path:.":
            problem(path, f'subagent {name}: source must be "path:."')
        if sub.get("path") != f"agents/{name}.md":
            problem(path, f'subagent {name}: path must be "agents/{name}.md" (keeps repeated installs unambiguous)')
        check_subagent_targets(path, sub)
    for name in sorted(agent_names - declared):
        problem(path, f"subagent {name} exists under agents/ but is not declared")
    for name in sorted(declared - agent_names):
        problem(path, f"subagent {name} is declared but agents/{name}.md does not exist")


def check_examples(agent_names: set[str]) -> str | None:
    path = ROOT / "examples" / "agents.toml"
    data = load_toml(path)
    if data is None:
        return None
    refs: set[str] = set()
    repo = None
    entries = list(data.get("skills", [])) + list(data.get("subagents", []))
    for entry in entries:
        source = entry.get("source", "")
        match = re.match(r"^([\w.-]+/[\w.-]+)@(\S+)$", source)
        if not match:
            problem(path, f"{entry.get('name')}: source must be owner/repo@tag, got {source!r}")
            continue
        repo = repo or match.group(1)
        if match.group(1) != repo:
            problem(path, f"{entry.get('name')}: source repository differs from {repo}")
        refs.add(match.group(2))
    if len(refs) != 1:
        problem(path, f"all sources must pin the same release, found {sorted(refs)}")
    ref = next(iter(refs), None)
    if ref and not TAG_RE.match(ref):
        problem(path, f"release pin {ref!r} must look like vX.Y.Z")
    check_agent_list(path, data)
    for sub in data.get("subagents", []):
        check_subagent_targets(path, sub)
    if not any(s.get("name") == "*" for s in data.get("skills", [])):
        problem(path, 'expected a wildcard skills entry (name = "*")')
    declared = {s.get("name") for s in data.get("subagents", [])}
    for name in sorted(agent_names ^ declared):
        problem(path, f"subagent set differs from agents/: {name}")
    trust = data.get("trust", {}).get("github_repos", [])
    if repo and repo not in trust:
        problem(path, f"[trust] github_repos should include {repo}")

    devcontainer = ROOT / "examples" / "devcontainer.json"
    try:
        dc = json.loads(devcontainer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problem(devcontainer, f"cannot parse: {exc}")
        return ref
    dc_ref = dc.get("remoteEnv", {}).get("AI_ASSETS_REF")
    if dc_ref != ref:
        problem(devcontainer, f"remoteEnv.AI_ASSETS_REF is {dc_ref!r} but examples/agents.toml pins {ref!r}")
    if "@sentry/dotagents@" not in dc.get("postCreateCommand", ""):
        problem(devcontainer, "postCreateCommand must pin the @sentry/dotagents version")
    return ref


def check_managed_block() -> None:
    path = ROOT / "instructions" / "AGENTS.md"
    if not path.is_file():
        problem(path, "missing")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if "\r" in text:
        problem(path, "must use LF line endings")
    if not text.endswith("\n"):
        problem(path, "must end with a newline")
    if not lines or lines[0] != START_MARK:
        problem(path, "first line must be the managed-block start marker")
    if not lines or lines[-1] != END_MARK:
        problem(path, "last line must be the managed-block end marker")
    if text.count(START_MARK) != 1 or text.count(END_MARK) != 1:
        problem(path, "markers must appear exactly once")
    check_links(path)


def check_changelog(ref: str | None) -> None:
    path = ROOT / "CHANGELOG.md"
    if not path.is_file():
        problem(path, "missing")
        return
    match = re.search(r"^## (\d+\.\d+\.\d+)\b", path.read_text(encoding="utf-8"), re.M)
    if not match:
        problem(path, "no '## X.Y.Z' release heading found")
        return
    if ref and TAG_RE.match(ref) and TAG_RE.match(ref).group(1) != match.group(1):
        problem(path, f"top release is {match.group(1)} but examples pin {ref}; the next tag must match both")


def check_docs_links() -> None:
    for md in sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md")):
        check_links(md)
    for legacy in ("manifest.json", "scripts/install-ai-assets.sh", "scripts/validate-ai-assets.sh"):
        if (ROOT / legacy).exists():
            problem(legacy, "legacy file must not come back")


def main() -> int:
    agent_names = check_agents()
    check_skills()
    check_agents_toml(agent_names)
    ref = check_examples(agent_names)
    check_managed_block()
    check_changelog(ref)
    check_docs_links()
    check_dotagents_version()
    for line in problems:
        print(line)
    if problems:
        print(f"validate: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("validate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
