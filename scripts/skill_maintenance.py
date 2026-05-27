#!/usr/bin/env python3
"""Skill self-check and safe update helper."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "skill_manifest.json"
BACKUP_DIR = ROOT / ".skill_backups"
EXCLUDED_BACKUP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".skill_backups"}


def run(cmd: str | list[str], *, check: bool = False, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=isinstance(cmd, str),
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {cmd}\nexit={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def git(args: list[str], *, check: bool = True) -> str:
    return run(["git", *args], check=check).stdout.strip()


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST_PATH}")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    required = ["schema_version", "skill_id", "repo", "branch", "entrypoint", "health_commands"]
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit(f"Manifest missing fields: {', '.join(missing)}")
    entrypoint = ROOT / str(data["entrypoint"])
    if not entrypoint.exists():
        raise SystemExit(f"Missing Skill entrypoint: {entrypoint}")
    return data


def has_git() -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"]).returncode == 0


def dirty_files() -> list[str]:
    proc = run(["git", "status", "--porcelain"])
    return [line for line in proc.stdout.splitlines() if line.strip()]


def sync_status(branch: str, *, fetch: bool = True) -> dict[str, Any]:
    if fetch:
        run(["git", "fetch", "--quiet", "origin", branch], check=True)
    remote_ref = f"origin/{branch}"
    local = git(["rev-parse", "HEAD"])
    remote = git(["rev-parse", remote_ref])
    base = git(["merge-base", "HEAD", remote_ref])

    if local == remote:
        state = "up_to_date"
    elif base == local:
        state = "behind"
    elif base == remote:
        state = "ahead"
    else:
        state = "diverged"

    changes = run(["git", "diff", "--name-status", f"HEAD..{remote_ref}"]).stdout.splitlines()
    commits = run(["git", "log", "--oneline", f"HEAD..{remote_ref}"]).stdout.splitlines()
    return {
        "state": state,
        "local": local,
        "remote": remote,
        "remote_ref": remote_ref,
        "changed_files": [line for line in changes if line.strip()],
        "incoming_commits": [line for line in commits if line.strip()],
    }


def run_health(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for cmd in manifest.get("health_commands", []):
        proc = run(str(cmd))
        results.append(
            {
                "cmd": cmd,
                "ok": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout_tail": proc.stdout[-4000:],
                "stderr_tail": proc.stderr[-4000:],
            }
        )
    return results


def make_backup(skill_id: str, old_sha: str) -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"{skill_id}-{old_sha[:12]}-{stamp}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob("*"):
            if any(part in EXCLUDED_BACKUP_PARTS for part in path.parts):
                continue
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))
    return target


def print_result(data: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print(f"skill: {data.get('skill_id')}")
    print(f"root: {data.get('root', ROOT)}")
    print(f"git: {data.get('git')}")
    sync = data.get("sync") or {}
    print(f"sync: {sync.get('state')}")
    if sync.get("incoming_commits"):
        print("\nincoming commits:")
        for line in sync["incoming_commits"][:20]:
            print(f"  {line}")
    if sync.get("changed_files"):
        print("\nchanged files:")
        for line in sync["changed_files"][:50]:
            print(f"  {line}")
    if data.get("dirty_files"):
        print("\ndirty files:")
        for line in data["dirty_files"]:
            print(f"  {line}")
    if data.get("health"):
        print("\nhealth:")
        for item in data["health"]:
            mark = "PASS" if item["ok"] else "FAIL"
            print(f"  [{mark}] {item['cmd']}")


def command_doctor(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    result: dict[str, Any] = {
        "skill_id": manifest["skill_id"],
        "root": str(ROOT),
        "manifest": str(MANIFEST_PATH),
        "git": "present" if has_git() else "missing",
    }
    if has_git():
        result["dirty_files"] = dirty_files()
        result["sync"] = sync_status(str(manifest["branch"]), fetch=not args.offline)
    else:
        result["sync"] = {
            "state": "no_git_metadata",
            "message": "This Skill directory is not a git checkout. Use git clone for safe self-update.",
        }
    result["health"] = [] if args.skip_health else run_health(manifest)
    print_result(result, args.json)
    return 1 if any(not item["ok"] for item in result["health"]) else 0


def command_update(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    if not has_git():
        raise SystemExit("Cannot update: this Skill directory has no .git metadata.")
    dirty = dirty_files()
    if dirty:
        raise SystemExit("Cannot update: working tree is dirty.\n" + "\n".join(dirty))

    status = sync_status(str(manifest["branch"]), fetch=True)
    if status["state"] == "up_to_date":
        print("Already up to date.")
        return 0
    if status["state"] != "behind":
        raise SystemExit(f"Cannot fast-forward safely: local state is {status['state']}.")

    if args.dry_run:
        print_result({"skill_id": manifest["skill_id"], "git": "present", "sync": status, "dry_run": True}, args.json)
        return 0
    if not args.yes:
        raise SystemExit("Refusing to update without --yes. Run update --dry-run first.")

    old_sha = git(["rev-parse", "HEAD"])
    backup = make_backup(str(manifest["skill_id"]), old_sha)
    try:
        run(["git", "merge", "--ff-only", status["remote_ref"]], check=True)
        for cmd in manifest.get("post_update_commands", []):
            run(str(cmd), check=True)
        health = run_health(manifest)
        if any(not item["ok"] for item in health):
            raise RuntimeError("Health check failed after update.")
        print_result(
            {
                "skill_id": manifest["skill_id"],
                "updated": True,
                "from": old_sha,
                "to": git(["rev-parse", "HEAD"]),
                "backup": str(backup),
                "health": health,
            },
            args.json,
        )
        return 0
    except Exception as exc:
        run(["git", "reset", "--hard", old_sha])
        raise SystemExit(f"Update failed and code was reset to {old_sha}.\nBackup: {backup}\nError: {exc}") from exc


def command_proposal(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    proposal = {
        "skill_id": manifest["skill_id"],
        "allowed_outputs": [
            "patch proposal",
            "GitHub issue draft",
            "PR summary",
            "affected-file checklist",
            "benchmark fixture proposal",
        ],
        "merge_gates": [
            "Relevant validation scripts pass.",
            "No private files, generated outputs, source maps, run manifests, QA logs, or user data are included.",
            "No benchmark-specific names become production triggers.",
            "The change preserves the Skill purpose.",
            "Human review is required before merge.",
        ],
        "trigger": args.trigger,
    }
    print(json.dumps(proposal, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill self-check and safe update helper.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    doctor = subcommands.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--offline", action="store_true")
    doctor.add_argument("--skip-health", action="store_true")
    doctor.set_defaults(func=command_doctor)

    update = subcommands.add_parser("update")
    update.add_argument("--dry-run", action="store_true")
    update.add_argument("--yes", action="store_true")
    update.add_argument("--json", action="store_true")
    update.set_defaults(func=command_update)

    proposal = subcommands.add_parser("proposal")
    proposal.add_argument("--trigger", default="unspecified")
    proposal.set_defaults(func=command_proposal)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
