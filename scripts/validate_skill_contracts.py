#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_manifest() -> dict:
    path = ROOT / "skill_manifest.json"
    if not path.exists():
        fail("skill_manifest.json missing")
    manifest = read_json(path)
    required = ["schema_version", "skill_id", "repo", "branch", "entrypoint", "multi_skill_system", "routes", "focused_skills"]
    missing = [key for key in required if key not in manifest]
    if missing:
        fail("manifest missing fields: " + ", ".join(missing))
    if not (ROOT / manifest["entrypoint"]).exists():
        fail(f"manifest entrypoint missing: {manifest['entrypoint']}")
    router = manifest.get("plugin_router_skill") or {}
    if not router.get("path") or not (ROOT / router["path"]).exists():
        fail("plugin router skill path missing")
    return manifest


def check_focused_skills(manifest: dict) -> None:
    seen = set()
    for item in manifest.get("focused_skills", []):
        name = item.get("name")
        path = item.get("path")
        route = item.get("route")
        if not name or not path or not route:
            fail(f"focused skill entry incomplete: {item}")
        if name in seen:
            fail(f"duplicate focused skill: {name}")
        seen.add(name)
        skill_path = ROOT / path
        if not skill_path.exists():
            fail(f"focused skill file missing: {path}")
        body = text(skill_path)
        if f"name: {name}" not in body:
            fail(f"focused skill frontmatter mismatch: {path}")
    index = manifest.get("index_skill")
    if not index or not (ROOT / index).exists():
        fail("index_skill missing or invalid")


def check_route_scripts(manifest: dict) -> None:
    plan = text(ROOT / "scripts" / "plan_workflow.py")
    questions = text(ROOT / "scripts" / "build_review_questions.py")
    for route in manifest.get("routes", []):
        if route not in plan:
            fail(f"route missing from plan_workflow.py: {route}")
        if route not in questions:
            fail(f"route missing from build_review_questions.py: {route}")
    for target in manifest.get("human_review_targets", []):
        if target not in questions and target not in plan:
            fail(f"human review target missing from route scripts: {target}")
    banned = ["acceptance probability", "chance score", "safe/match/reach"]
    web_dir = ROOT / "web" / "src"
    if web_dir.exists():
        combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in web_dir.rglob("*") if path.is_file())
        for phrase in banned:
            if phrase in combined.lower():
                fail(f"banned probability wording found in web source: {phrase}")


def check_plugin() -> None:
    path = ROOT / ".codex-plugin" / "plugin.json"
    if not path.exists():
        fail(".codex-plugin/plugin.json missing")
    plugin = read_json(path)
    if plugin.get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json must point skills to ./skills/")


def run_self_tests() -> None:
    for script in ["scripts/plan_workflow.py", "scripts/build_review_questions.py"]:
        proc = subprocess.run([sys.executable, str(ROOT / script), "--self-test"], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode != 0:
            fail(f"{script} --self-test failed\n{proc.stdout}\n{proc.stderr}")


def main() -> None:
    manifest = check_manifest()
    check_focused_skills(manifest)
    check_route_scripts(manifest)
    check_plugin()
    run_self_tests()
    print("OK: skill contract checks passed")


if __name__ == "__main__":
    main()
