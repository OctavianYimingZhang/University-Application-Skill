#!/usr/bin/env python3
"""Validate the manifest-driven University Application Plugin."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RETIRED_SKILLS = {
    "university-application-index",
    "study-abroad-advisor",
    "program-research",
    "requirement-audit",
    "materials-check",
    "application-writing-studio",
    "submission-readiness",
    "visa-readiness",
    "programme-table-cleaning",
}
RETIRED_PATHS = {
    "plugin-capability-manifest.v2.json",
    "contracts",
    "schemas",
    "memory",
    "references/setup",
    "COPY_PACKAGE.md",
    "scripts/build_review_questions.py",
    "scripts/check_setup_contract.py",
    "scripts/onboard_admissions.py",
    "scripts/plan_workflow.py",
    "scripts/skill_maintenance.py",
    "scripts/validate_setup.py",
}
RETIRED_TERMS = {
    "Auto-diagnosis",
    "TaskRunState",
    "LocalBridgeProtocol",
    "PluginCapabilityManifest",
    "Soleil",
    "direct invocation gate",
    "route_status",
    "AcademicTaskContext",
    "ApplicationCase",
}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
FIXED_COUNT_PATTERN = re.compile(
    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|\d+)\s+"
    r"(?:(?:public|focused|local)\s+)?Skills?\b",
    re.IGNORECASE,
)


class ValidationError(RuntimeError):
    pass


def read_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Invalid JSON: {relative}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"Expected a JSON object: {relative}")
    return value


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise ValidationError(f"Missing file: {relative}")
    return path.read_text(encoding="utf-8")


def skill_frontmatter(relative: str) -> tuple[str, str]:
    text = read_text(relative)
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValidationError(f"Missing Skill frontmatter: {relative}")
    block = match.group(1)
    name = re.search(r"^name:\s*([^\n]+)$", block, re.MULTILINE)
    description = re.search(r"^description:\s*([^\n]+)$", block, re.MULTILINE)
    extra = [
        line.split(":", 1)[0]
        for line in block.splitlines()
        if ":" in line and not line.startswith(("name:", "description:"))
    ]
    if not name or not description or extra:
        raise ValidationError(f"Skill frontmatter must contain only name and description: {relative}")
    return name.group(1).strip(), description.group(1).strip()


def manifest_skills(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    entries = manifest.get("public_skills")
    if not isinstance(entries, list) or len(entries) < 2:
        raise ValidationError("A Multi-Skill System requires a Router and at least one focused Skill")
    pairs: list[tuple[str, str]] = []
    purposes: list[str] = []
    for item in entries:
        if not isinstance(item, dict):
            raise ValidationError("Each public Skill declaration must be an object")
        name = str(item.get("name", ""))
        relative = str(item.get("path", ""))
        purpose = str(item.get("purpose", ""))
        if not NAME_PATTERN.fullmatch(name) or relative != f"skills/{name}/SKILL.md" or not purpose:
            raise ValidationError(f"Invalid public Skill declaration: {item!r}")
        pairs.append((name, relative))
        purposes.append(purpose)
    if len({name for name, _ in pairs}) != len(pairs):
        raise ValidationError("Public Skill names must be unique")
    router = str(manifest.get("skill_id", ""))
    architecture = manifest.get("architecture", {})
    if pairs[0][0] != router or purposes[0] != "intent_router":
        raise ValidationError("The first public Skill must be the declared Router")
    if architecture.get("router") != router or architecture.get("focused_skill_policy") != "manifest_driven":
        raise ValidationError("Architecture must declare a manifest-driven focused Skill policy")
    return pairs


def check_manifest() -> tuple[dict[str, Any], list[tuple[str, str]], set[str]]:
    manifest = read_json("skill_manifest.json")
    version = str(manifest.get("plugin_version", ""))
    if manifest.get("schema_version") != 3 or not VERSION_PATTERN.fullmatch(version):
        raise ValidationError("skill_manifest.json must declare schema 3 and a semantic Plugin version")
    if manifest.get("skill_id") != "university-application" or manifest.get("multi_skill_system") is not True:
        raise ValidationError("skill_manifest.json has the wrong Router identity")
    skills = manifest_skills(manifest)
    references = {str(item) for item in manifest.get("references", [])}
    actual_references = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "references").glob("*.md")
    }
    if not references or references != actual_references:
        raise ValidationError("Manifest references must match the live reference files")
    removed = {str(item) for item in manifest.get("removed_focused_skills", [])}
    if not REQUIRED_RETIRED_SKILLS.issubset(removed):
        raise ValidationError("skill_manifest.json is missing Plugin-owned retired Skills")
    if removed & {name for name, _ in skills}:
        raise ValidationError("A public Skill cannot also be retired")
    for relative in references:
        read_text(relative)
    tools = manifest.get("tools", {})
    if not isinstance(tools, dict) or not tools:
        raise ValidationError("skill_manifest.json must declare the retained tools")
    for relative in tools.values():
        read_text(str(relative))
    return manifest, skills, references


def check_skills(skills: list[tuple[str, str]]) -> None:
    root_name, _ = skill_frontmatter("SKILL.md")
    if root_name != skills[0][0]:
        raise ValidationError("Root SKILL.md must match the Router")
    for expected_name, relative in skills:
        actual_name, description = skill_frontmatter(relative)
        if actual_name != expected_name or len(description) < 40:
            raise ValidationError(f"Invalid Skill metadata: {relative}")


def check_plugin_metadata(manifest: dict[str, Any], skills: list[tuple[str, str]]) -> None:
    plugin = read_json(".codex-plugin/plugin.json")
    plugin_version = str(plugin.get("version", "")).split("+", 1)[0]
    if plugin.get("name") != "university-application-skill" or plugin_version != manifest["plugin_version"]:
        raise ValidationError("Plugin metadata identity or version drifted")
    if plugin.get("skills") != "./skills/":
        raise ValidationError("Plugin metadata must expose ./skills/")
    if plugin.get("interface", {}).get("displayName") != "University Application Skill":
        raise ValidationError("Plugin display name drifted")
    agents = read_text("agents/openai.yaml")
    if (
        'manifest: "skill_manifest.json"' not in agents
        or 'focused_skill_policy: "manifest_driven"' not in agents
        or "focused_skills:" in agents
    ):
        raise ValidationError("agents/openai.yaml must use the manifest as the Skill source")


def check_retirement(skills: list[tuple[str, str]], references: set[str]) -> None:
    present = sorted(path for path in RETIRED_PATHS if (ROOT / path).exists())
    if present:
        raise ValidationError("Retired paths remain: " + ", ".join(present))
    public_files = [
        "SKILL.md",
        "README.md",
        "agents/openai.yaml",
        ".codex-plugin/plugin.json",
        *(relative for _, relative in skills),
        *references,
    ]
    combined = "\n".join(read_text(path) for path in public_files)
    found = sorted(term for term in RETIRED_TERMS if term.lower() in combined.lower())
    if found:
        raise ValidationError("Retired workflow terms remain: " + ", ".join(found))
    if FIXED_COUNT_PATTERN.search(combined):
        raise ValidationError("Public guidance must not encode a fixed Skill count")
    live = {
        path.name
        for path in (ROOT / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    if live != {name for name, _ in skills}:
        raise ValidationError(f"Skill directories differ from the manifest: {sorted(live)}")


def run_check(command: list[str]) -> None:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise ValidationError(f"Command failed: {' '.join(command)}\n{detail}")


def main() -> int:
    try:
        manifest, skills, references = check_manifest()
        check_skills(skills)
        check_plugin_metadata(manifest, skills)
        check_retirement(skills, references)
        run_check([sys.executable, "scripts/validate_catalogues.py"])
        run_check([sys.executable, "scripts/validate_evidence.py", "--self-test"])
        run_check([sys.executable, "scripts/publish_skill.py", "--self-test"])
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: manifest-driven University Application Plugin {manifest['plugin_version']} validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
