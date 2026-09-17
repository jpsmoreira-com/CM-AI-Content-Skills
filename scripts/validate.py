#!/usr/bin/env python3
"""Validate the asset layout of CM-AI-Content-Skills before publishing.

Structural checks only (no network): the primitives under .apm/ follow the Agent Skills
and APM conventions, apm.yml and examples/ describe exactly what is on disk, the shared
guardrails instruction is unconditional and well-formed, internal links resolve, and the
release version is consistent between apm.yml, CHANGELOG.md, and the examples. Prints
one line per problem; exit 1 on any problem.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APM = ROOT / ".apm"
SKILLS = APM / "skills"
AGENTS = APM / "agents"
INSTRUCTIONS = APM / "instructions"
GUARDRAILS = INSTRUCTIONS / "cm-ai-content.instructions.md"
PACKAGE_NAME = "cm-ai-content-skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DEP_RE = re.compile(r"^([\w.-]+/[\w.-]+)#v(\d+\.\d+\.\d+)$")
# Every harness a portal (and this repository's dogfood install) deploys to.
EXPECTED_TARGETS = ["copilot", "claude", "codex"]
SKILL_KEYS = {"name", "description", "argument-hint", "license", "compatibility", "metadata", "allowed-tools"}
# Files whose links are intentionally broken (fixtures and illustrative examples).
LINK_EXCLUDES = (
    "evals/",
    ".apm/skills/tutorial-source-to-mkdocs/references/golden-examples/",
    ".apm/skills/style-guide-validator/references/style-guide-full.md",
)
# The pre-APM layout and tooling; none of it may come back.
LEGACY = (
    "agents.toml", "agents.lock", "manifest.json", "skills", "agents", "instructions",
    "examples/agents.toml", "scripts/sync-repo-wiring.sh", "scripts/test-wiring.sh",
    "scripts/install-ai-assets.sh", "scripts/validate-ai-assets.sh",
)
# The APM CLI version is repeated in CI, the devcontainer, and docs; keep them equal.
APM_VERSION_RES = (
    re.compile(r"APM_VERSION:\s*[\"']?(\d+\.\d+\.\d+)"),
    re.compile(r"apm-unix \| sh -s -- @v(\d+\.\d+\.\d+)"),
    re.compile(r"apm-version:\s*[\"']?(\d+\.\d+\.\d+)"),
)

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


def read_manifest(path: Path) -> dict | None:
    """Read the flat YAML subset apm.yml uses here: top-level scalars, top-level lists
    (block or flow), and the nested `dependencies: apm:` / `mcp:` lists. No PyYAML needed."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        problem(path, f"cannot read: {exc}")
        return None

    def flow_list(value: str) -> list[str]:
        return [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]

    data: dict = {}
    receiving: tuple[dict, str] | None = None  # (mapping, key) that "- item" lines append to
    section: str | None = None  # top-level key whose indented children are being read
    for raw in text.splitlines():
        line = "" if raw.lstrip().startswith("#") else raw.split(" #", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped.startswith("- "):
            if receiving is None:
                problem(path, f"list item outside a list: {raw!r}")
                continue
            mapping, key = receiving
            if not isinstance(mapping.get(key), list):
                mapping[key] = []
            mapping[key].append(stripped[2:].strip().strip("'\""))
            continue
        key, sep, value = stripped.partition(":")
        if not sep:
            problem(path, f"cannot parse line: {raw!r}")
            continue
        key, value = key.strip(), value.strip()
        target = data
        if indent == 0:
            section = key
        else:
            if section is None:
                problem(path, f"indented key without a parent: {raw!r}")
                continue
            if not isinstance(data.get(section), dict):
                data[section] = {}
            target = data[section]
        if value == "":
            target[key] = None
            receiving = (target, key)
        elif value.startswith("[") and value.endswith("]"):
            target[key] = flow_list(value)
            receiving = None
        else:
            target[key] = value.strip("'\"")
            receiving = None
    return data


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
        problem(SKILLS, "missing directory")
        return
    for entry in sorted(SKILLS.iterdir()):
        if entry.is_file():
            problem(entry, "only skill directories belong here")
            continue
        skill = entry / "SKILL.md"
        if not skill.is_file():
            problem(entry, "missing SKILL.md")
            continue
        fields, body = frontmatter(skill)
        name = fields.get("name", "")
        if name != entry.name:
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
        for md in entry.rglob("*.md"):
            check_links(md)


def check_agents() -> set[str]:
    names: set[str] = set()
    if not AGENTS.is_dir():
        problem(AGENTS, "missing directory")
        return names
    for agent in sorted(p for p in AGENTS.iterdir() if p.is_file()):
        if not agent.name.endswith(".agent.md"):
            problem(agent, "APM treats every file here as a subagent; name it <name>.agent.md or move it out")
            continue
        stem = agent.name[: -len(".agent.md")]
        fields, body = frontmatter(agent)
        name = fields.get("name", "")
        if name != stem:
            problem(agent, f"frontmatter name {name!r} must equal the file name {stem!r}")
        if not NAME_RE.match(name):
            problem(agent, "name must be lowercase letters, digits and single hyphens")
        if not fields.get("description"):
            problem(agent, "description is required (Copilot and Claude surface the agent by it)")
        if not body.strip():
            problem(agent, "empty body")
        check_links(agent)
        names.add(stem)
    return names


def check_instructions() -> None:
    if not GUARDRAILS.is_file():
        problem(GUARDRAILS, "missing: the always-on guardrails must ship with every release")
        return
    for path in sorted(INSTRUCTIONS.glob("*.md")):
        if not path.name.endswith(".instructions.md"):
            problem(path, "instructions must be named <name>.instructions.md")
            continue
        text = path.read_text(encoding="utf-8")
        if "\r" in text:
            problem(path, "must use LF line endings")
        if not text.endswith("\n"):
            problem(path, "must end with a newline")
        if "cm-ai-content:managed" in text:
            problem(path, "managed-block markers belong to the retired wiring script")
        fields, body = frontmatter(path)
        if not fields.get("description"):
            problem(path, "description is required")
        if path == GUARDRAILS and "applyTo" in fields:
            problem(path, "must not set applyTo: the guardrails load unconditionally, on every turn, in every harness")
        if not body.strip():
            problem(path, "empty body")
        check_links(path)


def check_manifest() -> str | None:
    path = ROOT / "apm.yml"
    data = read_manifest(path)
    if data is None:
        return None
    if data.get("name") != PACKAGE_NAME:
        problem(path, f"name must be {PACKAGE_NAME!r}")
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        problem(path, f"version must be X.Y.Z, got {version!r}")
        version = None
    if data.get("includes") != "auto":
        problem(path, "includes must be auto so every primitive under .apm/ is published")
    if data.get("targets") != EXPECTED_TARGETS:
        problem(path, f"targets must be {EXPECTED_TARGETS}, got {data.get('targets')!r}")
    deps = data.get("dependencies") if isinstance(data.get("dependencies"), dict) else {}
    if deps.get("apm") != []:
        problem(path, "dependencies.apm must be empty: a published package must not pull transitive context into portals")
    return version


def check_examples(version: str | None) -> None:
    path = ROOT / "examples" / "apm.yml"
    data = read_manifest(path)
    if data is not None:
        for key in ("name", "version"):
            if not data.get(key):
                problem(path, f"{key} is required by apm.yml")
        if data.get("targets") != EXPECTED_TARGETS:
            problem(path, f"targets must be {EXPECTED_TARGETS}, got {data.get('targets')!r}")
        deps = data.get("dependencies") if isinstance(data.get("dependencies"), dict) else {}
        apm_deps = deps.get("apm") or []
        if len(apm_deps) != 1:
            problem(path, f"dependencies.apm must contain exactly this package, got {apm_deps!r}")
        else:
            match = DEP_RE.match(apm_deps[0])
            if not match:
                problem(path, f"dependency must be owner/repo#vX.Y.Z, got {apm_deps[0]!r}")
            elif version and match.group(2) != version:
                problem(path, f"pins v{match.group(2)} but apm.yml is version {version}; the next tag must match both")

    devcontainer = ROOT / "examples" / "devcontainer.json"
    try:
        dc = json.loads(devcontainer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problem(devcontainer, f"cannot parse: {exc}")
        return
    command = dc.get("postCreateCommand", "")
    for needle in ("apm-unix | sh -s -- @v", "apm install --frozen", "apm compile"):
        if needle not in command:
            problem(devcontainer, f"postCreateCommand must contain {needle!r}")


def check_changelog(version: str | None) -> None:
    path = ROOT / "CHANGELOG.md"
    if not path.is_file():
        problem(path, "missing")
        return
    match = re.search(r"^## (\d+\.\d+\.\d+)\b", path.read_text(encoding="utf-8"), re.M)
    if not match:
        problem(path, "no '## X.Y.Z' release heading found")
        return
    if version and match.group(1) != version:
        problem(path, f"top release is {match.group(1)} but apm.yml is version {version}; the next tag must match both")


def check_docs_links() -> None:
    for md in sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md")):
        check_links(md)
    for legacy in LEGACY:
        if (ROOT / legacy).exists():
            problem(legacy, "retired with the move to APM; must not come back")


def check_apm_cli_version() -> None:
    files = sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md"))
    files += [ROOT / "examples" / "devcontainer.json"]
    files += sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    found: dict[str, list[str]] = {}
    for f in files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        versions = {v for regex in APM_VERSION_RES for v in regex.findall(text)}
        for v in versions:
            found.setdefault(v, []).append(str(f.relative_to(ROOT)))
    if len(found) > 1:
        detail = "; ".join(f"{v} in {', '.join(sorted(p))}" for v, p in sorted(found.items()))
        problem("scripts/validate.py", f"APM CLI version disagrees across files: {detail}")


def main() -> int:
    check_skills()
    check_agents()
    check_instructions()
    version = check_manifest()
    check_examples(version)
    check_changelog(version)
    check_docs_links()
    check_apm_cli_version()
    for line in problems:
        print(line)
    if problems:
        print(f"validate: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("validate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
