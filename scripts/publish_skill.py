#!/usr/bin/env python3
"""Synchronise, compare, or push the simplified University Application Plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "skill_manifest.json"
LOCAL_SKILL_ROOT = Path.home() / ".codex" / "skills"
ROUTER_ID = "university-application"
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "outputs",
    "tmp",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".docx", ".pdf", ".pptx", ".xlsx", ".zip", ".jsonl"}
SHARED_DIRS = ("references", "scripts", "catalogues")
SHARED_FILES = ("LICENSE", "skill_manifest.json")


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def ignored(_: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in SKIP_DIRS or name == ".DS_Store" or Path(name).suffix in SKIP_SUFFIXES
    }


def skill_name(skill_md: Path) -> str:
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", skill_md.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise RuntimeError(f"Cannot read Skill name from {skill_md}")
    return match.group(1)


def public_skills() -> list[dict[str, Any]]:
    entries = []
    for item in load_manifest().get("public_skills", []):
        source = ROOT / str(item.get("path", ""))
        name = str(item.get("name", ""))
        if not source.is_file() or source.name != "SKILL.md" or skill_name(source) != name:
            raise RuntimeError(f"Invalid public Skill declaration: {item!r}")
        entries.append({"name": name, "source": source.parent})
    if [item["name"] for item in entries] != [
        "university-application",
        "application-research",
        "application-writing",
        "application-readiness",
    ]:
        raise RuntimeError("Expected the router followed by Research, Writing, and Readiness")
    return entries


def replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=ignored)


def install_focused(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "SKILL.md", destination / "SKILL.md")
    for item in source.iterdir():
        if item.name == "SKILL.md" or item.name in SKIP_DIRS or item.name == ".DS_Store":
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=ignored)
        elif item.suffix not in SKIP_SUFFIXES:
            shutil.copy2(item, target)
    for dirname in SHARED_DIRS:
        shared = ROOT / dirname
        if shared.exists():
            shutil.copytree(shared, destination / dirname, ignore=ignored)
    for filename in SHARED_FILES:
        shared = ROOT / filename
        if shared.exists():
            shutil.copy2(shared, destination / filename)


def removed_ids() -> list[str]:
    return [str(item) for item in load_manifest().get("removed_focused_skills", []) if item]


def cleanup_removed(install_root: Path) -> list[dict[str, str]]:
    results = []
    for name in removed_ids():
        destination = install_root / name
        if destination.exists():
            shutil.rmtree(destination)
            status = "removed"
        else:
            status = "absent"
        results.append({"name": name, "destination": str(destination), "status": status})
    return results


def synchronise(install_root: Path) -> dict[str, Any]:
    entries = public_skills()
    router_destination = install_root / ROUTER_ID
    replace_tree(ROOT, router_destination)
    focused = []
    for entry in entries[1:]:
        destination = install_root / entry["name"]
        install_focused(entry["source"], destination)
        focused.append({"name": entry["name"], "destination": str(destination), "status": "synchronised"})
    return {
        "status": "ok",
        "router": str(router_destination),
        "focused_skills": focused,
        "removed_focused_skills": cleanup_removed(install_root),
    }


def tree_manifest(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS or part == ".DS_Store" for part in relative.parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def compare(expected: Path, actual: Path, name: str) -> dict[str, Any]:
    left = tree_manifest(expected)
    right = tree_manifest(actual)
    missing = sorted(left.keys() - right.keys())
    unexpected = sorted(right.keys() - left.keys())
    changed = sorted(key for key in left.keys() & right.keys() if left[key] != right[key])
    return {
        "name": name,
        "status": "ok" if not missing and not unexpected and not changed else "drift",
        "missing": missing,
        "unexpected": unexpected,
        "changed": changed,
    }


def check_installed(install_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        expected_root = Path(temporary) / "skills"
        synchronise(expected_root)
        checks = [
            compare(expected_root / entry["name"], install_root / entry["name"], entry["name"])
            for entry in public_skills()
        ]
    retired_present = [name for name in removed_ids() if (install_root / name).exists()]
    return {
        "status": "ok" if all(item["status"] == "ok" for item in checks) and not retired_present else "drift",
        "checks": checks,
        "retired_present": retired_present,
    }


def run_push() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def self_test() -> None:
    manifest = load_manifest()
    assert manifest["plugin_version"] == "3.0.0"
    assert len(public_skills()) == 4
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "skills"
        for name in removed_ids()[:2]:
            (root / name).mkdir(parents=True)
        result = synchronise(root)
        assert result["status"] == "ok"
        assert all((root / entry["name"] / "SKILL.md").exists() for entry in public_skills())
        assert not any((root / name).exists() for name in removed_ids())
        assert check_installed(root)["status"] == "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-local-skill", action="store_true")
    parser.add_argument("--check-installed", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--install-root", type=Path, default=LOCAL_SKILL_ROOT)
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("OK: publish_skill self-test passed")
        return 0

    result: dict[str, Any] = {"steps": []}
    install_root = args.install_root.expanduser().resolve()
    if args.sync_local_skill:
        result["steps"].append({"sync": synchronise(install_root)})
    if args.check_installed:
        result["steps"].append({"installed_check": check_installed(install_root)})
    if args.push:
        result["steps"].append({"push": run_push()})
    if not result["steps"]:
        result["steps"].append({"status": "nothing_requested"})
    print(json.dumps(result, indent=2))
    failed = any(
        isinstance(value, dict) and value.get("status") in {"error", "drift"}
        for step in result["steps"]
        for value in step.values()
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
