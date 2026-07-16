#!/usr/bin/env python3
"""Validate the simplified University Application Plugin."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = [
    ("university-application", "skills/university-application/SKILL.md"),
    ("application-research", "skills/application-research/SKILL.md"),
    ("application-writing", "skills/application-writing/SKILL.md"),
    ("application-readiness", "skills/application-readiness/SKILL.md"),
]
EXPECTED_REFERENCES = {
    "references/evidence-contract.md",
    "references/research.md",
    "references/essay-sop.md",
    "references/submission.md",
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
RETIRED_SKILLS = {
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
    name = re.search(r"^name:\s*([^\n]+)$", match.group(1), re.MULTILINE)
    description = re.search(r"^description:\s*([^\n]+)$", match.group(1), re.MULTILINE)
    extra = [
        line.split(":", 1)[0]
        for line in match.group(1).splitlines()
        if ":" in line and not line.startswith(("name:", "description:"))
    ]
    if not name or not description or extra:
        raise ValidationError(f"Skill frontmatter must contain only name and description: {relative}")
    return name.group(1).strip(), description.group(1).strip()


def check_manifest() -> dict[str, Any]:
    manifest = read_json("skill_manifest.json")
    if manifest.get("schema_version") != 3 or manifest.get("plugin_version") != "3.0.0":
        raise ValidationError("skill_manifest.json must declare schema 3 and Plugin 3.0.0")
    if manifest.get("skill_id") != "university-application" or manifest.get("multi_skill_system") is not True:
        raise ValidationError("skill_manifest.json has the wrong router identity")
    entries = manifest.get("public_skills")
    pairs = [(item.get("name"), item.get("path")) for item in entries or [] if isinstance(item, dict)]
    if pairs != EXPECTED_SKILLS:
        raise ValidationError("skill_manifest.json must declare exactly the four public Skills in order")
    if set(manifest.get("references", [])) != EXPECTED_REFERENCES:
        raise ValidationError("skill_manifest.json reference set drifted")
    if set(manifest.get("removed_focused_skills", [])) != RETIRED_SKILLS:
        raise ValidationError("skill_manifest.json retired Skill set drifted")
    for relative in manifest.get("references", []):
        read_text(relative)
    for relative in manifest.get("tools", {}).values():
        read_text(str(relative))
    return manifest


def check_skills() -> None:
    root_name, _ = skill_frontmatter("SKILL.md")
    if root_name != "university-application":
        raise ValidationError("Root SKILL.md must be university-application")
    for expected_name, relative in EXPECTED_SKILLS:
        actual_name, description = skill_frontmatter(relative)
        if actual_name != expected_name or len(description) < 40:
            raise ValidationError(f"Invalid Skill metadata: {relative}")


def check_plugin_metadata() -> None:
    plugin = read_json(".codex-plugin/plugin.json")
    if plugin.get("name") != "university-application-skill" or plugin.get("version") != "3.0.0":
        raise ValidationError("Plugin metadata identity or version drifted")
    if plugin.get("skills") != "./skills/":
        raise ValidationError("Plugin metadata must expose ./skills/")
    interface = plugin.get("interface", {})
    if interface.get("displayName") != "University Application Skill":
        raise ValidationError("Plugin display name drifted")
    agents = read_text("agents/openai.yaml")
    for token in ("university-application", "application-research", "application-writing", "application-readiness"):
        if token not in agents:
            raise ValidationError(f"agents/openai.yaml is missing {token}")


def check_retirement() -> None:
    present = sorted(path for path in RETIRED_PATHS if (ROOT / path).exists())
    if present:
        raise ValidationError("Retired paths remain: " + ", ".join(present))
    public_files = [
        "SKILL.md",
        "README.md",
        "agents/openai.yaml",
        ".codex-plugin/plugin.json",
        *(relative for _, relative in EXPECTED_SKILLS),
        *EXPECTED_REFERENCES,
    ]
    combined = "\n".join(read_text(path) for path in public_files)
    found = sorted(term for term in RETIRED_TERMS if term.lower() in combined.lower())
    if found:
        raise ValidationError("Retired workflow terms remain: " + ", ".join(found))
    live_skill_dirs = {
        path.name
        for path in (ROOT / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    if live_skill_dirs != {name for name, _ in EXPECTED_SKILLS}:
        raise ValidationError(f"Unexpected public Skill directories: {sorted(live_skill_dirs)}")


def run_check(command: list[str]) -> None:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise ValidationError(f"Command failed: {' '.join(command)}\n{detail}")


def main() -> int:
    try:
        check_manifest()
        check_skills()
        check_plugin_metadata()
        check_retirement()
        run_check([sys.executable, "scripts/validate_catalogues.py"])
        run_check([sys.executable, "scripts/validate_evidence.py", "--self-test"])
        run_check([sys.executable, "scripts/publish_skill.py", "--self-test"])
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: simplified University Application Plugin validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
