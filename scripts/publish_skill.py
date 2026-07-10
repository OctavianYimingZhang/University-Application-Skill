#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "skill_manifest.json"
DEFAULT_LOCAL_SKILL_ROOT = Path.home() / ".codex" / "skills"
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".skill_backups",
    ".npm-cache",
    "node_modules",
    "dist",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".docx", ".pdf", ".pptx", ".xlsx", ".zip", ".jsonl"}
SHARED_RESOURCE_DIRS = ("references", "scripts", "contracts", "schemas")
SHARED_RESOURCE_FILES = ("LICENSE", "skill_manifest.json", "plugin-capability-manifest.v2.json")
CANONICAL_SKILL_NAME = "university-application-index"
CATALOGUE_SKILLS = {"program-research", "programme-table-cleaning"}


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def run(cmd: list[str], dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"cmd": cmd, "status": "planned"}
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def ignore(_: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        suffix = Path(name).suffix
        if name in SKIP_DIRS or suffix in SKIP_SUFFIXES or name == ".DS_Store":
            ignored.add(name)
    return ignored


def read_skill_name(skill_md: Path) -> str:
    body = skill_md.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", body, flags=re.MULTILINE)
    return match.group(1) if match else skill_md.parent.name


def discover_focused_skills() -> list[dict[str, Any]]:
    skills_dir = ROOT / "skills"
    out = []
    for path in sorted(item for item in skills_dir.iterdir() if item.is_dir()):
        skill_md = path / "SKILL.md"
        if skill_md.exists() and path.name != CANONICAL_SKILL_NAME:
            out.append({"name": read_skill_name(skill_md), "source": path})
    return out


def copy_child_resources(source_dir: Path, destination: Path) -> None:
    for item in source_dir.iterdir():
        if item.name == "SKILL.md" or item.name in SKIP_DIRS or item.suffix in SKIP_SUFFIXES or item.name == ".DS_Store":
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=ignore)
        else:
            shutil.copy2(item, target)


def sync_focused_skill(skill: dict[str, Any], local_skill_root: Path, dry_run: bool) -> dict[str, Any]:
    destination = local_skill_root / skill["name"]
    if dry_run:
        return {"name": skill["name"], "destination": str(destination), "status": "planned"}
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    skill_text = (skill["source"] / "SKILL.md").read_text(encoding="utf-8")
    skill_text = skill_text.replace("../../references/", "references/")
    skill_text = skill_text.replace("../../scripts/", "scripts/")
    skill_text = skill_text.replace("../../contracts/", "contracts/")
    skill_text = skill_text.replace("../../catalogues/", "catalogues/")
    (destination / "SKILL.md").write_text(skill_text, encoding="utf-8")
    copy_child_resources(skill["source"], destination)
    for dirname in SHARED_RESOURCE_DIRS:
        source = ROOT / dirname
        if source.exists():
            shutil.copytree(source, destination / dirname, ignore=ignore)
    if skill["name"] in CATALOGUE_SKILLS:
        shutil.copytree(ROOT / "catalogues", destination / "catalogues", ignore=ignore)
    for filename in SHARED_RESOURCE_FILES:
        source = ROOT / filename
        if source.exists():
            shutil.copy2(source, destination / filename)
    return {"name": skill["name"], "destination": str(destination), "status": "ok"}


def sync_local_skill(destination: Path, dry_run: bool) -> dict[str, Any]:
    canonical_destination = destination if destination.name == CANONICAL_SKILL_NAME else destination.parent / CANONICAL_SKILL_NAME
    if dry_run:
        return {
            "canonical_destination": str(canonical_destination),
            "focused_skills": [
                {"name": item["name"], "destination": str(canonical_destination.parent / item["name"]), "status": "planned"}
                for item in discover_focused_skills()
            ],
            "status": "planned",
        }
    if canonical_destination.exists():
        shutil.rmtree(canonical_destination)
    canonical_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT, canonical_destination, ignore=ignore)
    focused = [sync_focused_skill(item, canonical_destination.parent, dry_run=False) for item in discover_focused_skills()]
    return {"canonical_destination": str(canonical_destination), "focused_skills": focused, "status": "ok"}


def basic_status() -> dict[str, Any]:
    manifest = load_manifest()
    return {
        "repo": manifest.get("repo"),
        "entrypoint_exists": (ROOT / manifest.get("entrypoint", "")).exists(),
        "focused_skill_count": len(discover_focused_skills()),
        "web_exists": (ROOT / "web" / "package.json").exists(),
    }


def publish(push: bool, sync_local: bool, destination: Path, dry_run: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"status": basic_status(), "steps": []}
    if push:
        result["steps"].append(run(["git", "push"], dry_run))
    if sync_local:
        result["steps"].append(sync_local_skill(destination, dry_run))
    if not push and not sync_local:
        result["steps"].append({"status": "nothing_requested", "hint": "Use --push and/or --sync-local-skill."})
    return result


def has_error(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("status") == "error":
            return True
        return any(has_error(item) for item in value.values())
    if isinstance(value, list):
        return any(has_error(item) for item in value)
    return False


def self_test() -> None:
    manifest = load_manifest()
    assert manifest.get("multi_skill_system") is True
    assert discover_focused_skills()
    assert {item["name"] for item in discover_focused_skills()} >= {"study-abroad-advisor", "visa-readiness"}
    assert manifest.get("skill_id") == CANONICAL_SKILL_NAME
    dry = sync_local_skill(DEFAULT_LOCAL_SKILL_ROOT / manifest["skill_id"], dry_run=True)
    assert dry["status"] == "planned"
    legacy_dry = sync_local_skill(DEFAULT_LOCAL_SKILL_ROOT / "study-abroad-advisor", dry_run=True)
    assert Path(legacy_dry["canonical_destination"]).name == CANONICAL_SKILL_NAME
    with tempfile.TemporaryDirectory() as tmp:
        local_root = Path(tmp)
        canonical = local_root / CANONICAL_SKILL_NAME
        result = sync_local_skill(canonical, dry_run=False)
        assert result["status"] == "ok"
        assert (canonical / "SKILL.md").exists()
        for name in ("study-abroad-advisor", "program-research", "visa-readiness"):
            installed = local_root / name
            body = (installed / "SKILL.md").read_text(encoding="utf-8")
            assert "../../references/" not in body
            assert "../../scripts/" not in body
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
                if target.startswith(("http://", "https://", "#")):
                    continue
                assert (installed / target.split("#", 1)[0]).resolve().exists(), (name, target)
        assert (local_root / "program-research" / "catalogues" / "index.json").exists()
        assert not (local_root / "visa-readiness" / "catalogues").exists()


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish or sync University Application Skill.")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--sync-local-skill", action="store_true")
    parser.add_argument("--local-skill-dir", default=str(DEFAULT_LOCAL_SKILL_ROOT / CANONICAL_SKILL_NAME))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("OK: publish_skill self-test passed")
        return
    result = publish(args.push, args.sync_local_skill, Path(args.local_skill_dir), args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if has_error(result):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
