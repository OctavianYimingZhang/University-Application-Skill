#!/usr/bin/env python3
"""Check setup schema, gates, fixtures, and template drift."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_MODES = [
    "quick_triage",
    "full_shortlist",
    "exact_program_selection",
    "requirement_audit",
    "essay_sop",
    "workbook_build",
    "programme_table_cleaning",
    "submission_readiness",
    "source_refresh",
    "visa_route",
]
ROOT_FIELDS = [
    "workflow_mode",
    "output_mode",
    "source_policy",
    "privacy_mode",
    "export_format",
    "ranking_weight",
    "admission_safety_weight",
    "budget_weight",
    "city_weight",
    "career_weight",
    "research_fit_weight",
    "visa_work_route_weight",
    "deadline_feasibility_weight",
    "source_workbook_dir_or_files",
    "cleaned_output_dir",
    "copy_back_requested",
]
PROFILE_FIELDS = [
    "target_degree_level",
    "target_intake",
    "target_countries",
    "citizenship_countries",
    "residence_country",
    "education_country",
    "passport_country",
    "visa_application_country",
    "target_field",
    "current_institution",
    "current_major",
    "gpa_value",
    "gpa_scale",
    "language_status",
    "core_courses",
    "budget_annual",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(args: list[str], *, input_text: str | None = None, expect_ok: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=ROOT, input=input_text, text=True, capture_output=True)
    if expect_ok and proc.returncode != 0:
        fail(f"command failed: {' '.join(args)}\n{proc.stderr or proc.stdout}")
    if not expect_ok and proc.returncode == 0:
        fail(f"command unexpectedly passed: {' '.join(args)}")
    return proc


def check_schema() -> None:
    schema = json.loads((ROOT / "references/setup/user-setup.schema.json").read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    profile_props = props.get("profile", {}).get("properties", {})
    if "anyOf" not in schema:
        fail("schema must accept current and legacy setup identifiers through anyOf")
    for field in ROOT_FIELDS:
        if field not in props:
            fail(f"schema missing root field: {field}")
    for field in PROFILE_FIELDS:
        if field not in profile_props:
            fail(f"schema missing profile field: {field}")


def check_setup_references() -> None:
    flow = (ROOT / "references/setup/onboarding-flow.yaml").read_text(encoding="utf-8")
    gates = (ROOT / "references/setup/task-gates.yaml").read_text(encoding="utf-8")
    for mode in WORKFLOW_MODES:
        if f"      gate: {mode}" not in flow:
            fail(f"onboarding flow missing normalized gate: {mode}")
        if f"  {mode}:" not in gates:
            fail(f"task gates missing workflow mode: {mode}")
    if "source_workbook_dir_or_files" not in flow:
        fail("onboarding flow missing canonical programme workbook source field")
    if "output_only: true" not in flow:
        fail("status diagnostics card must be marked output_only")


def check_fixtures_and_template() -> None:
    run(["python3", "scripts/validate_setup.py", "tests/fixtures/user_setup_full_shortlist.json"])
    run(["python3", "scripts/validate_setup.py", "tests/fixtures/user_setup_programme_table_cleaning.json"])
    run(["python3", "scripts/validate_setup.py", "tests/fixtures/user_setup_missing_fields.json"], expect_ok=False)
    template = run(
        ["python3", "scripts/onboard_admissions.py", "--workflow-mode", "programme_table_cleaning", "--output-mode", "source_backed"]
    ).stdout
    data = json.loads(template)
    if "source_workbook_dir_or_files" not in data:
        fail("programme table template missing source_workbook_dir_or_files")
    if "source_workbook_dir" in data:
        fail("programme table template should not emit deprecated source_workbook_dir")
    legacy = json.dumps(
        {
            "task_type": "shortlist",
            "output_format": "chat_summary",
            "degree_level": "masters",
            "subject_area": "Data Science",
            "target_country_or_region": "UK",
            "academic_background": "BSc quantitative",
            "intake_term": "2026",
            "budget": "30000 GBP",
        }
    )
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=legacy)


def main() -> None:
    check_schema()
    check_setup_references()
    check_fixtures_and_template()
    print("OK: setup contract checks passed")


if __name__ == "__main__":
    main()
