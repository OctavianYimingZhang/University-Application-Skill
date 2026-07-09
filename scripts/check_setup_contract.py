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
    "visa_readiness",
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
    "requested_output_language",
    "evidence_records",
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
    evidence = schema.get("$defs", {}).get("evidenceRecord", {})
    required_evidence_fields = {
        "evidence_id", "value", "source", "evidence_date", "confirmation_status", "confirmed_at",
        "source_availability", "fact_verification", "completeness", "application_cycle", "accessed_at", "staleness",
    }
    if set(evidence.get("required", [])) != required_evidence_fields:
        fail("schema evidenceRecord required fields drifted")


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
    run(["python3", "scripts/validate_setup.py", "tests/fixtures/user_setup_full_shortlist.json"], expect_ok=False)
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
    if data.get("evidence_records") != []:
        fail("setup template must ship with empty evidence_records")
    full_template = json.loads(run(["python3", "scripts/onboard_admissions.py"]).stdout)
    if any(value not in ("", [], {}) for value in full_template.get("profile", {}).values()):
        fail("setup template contains seeded applicant profile values")
    legacy = json.dumps(
        {
            "task_type": "shortlist",
            "output_format": "chat_summary",
        }
    )
    proc = run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=legacy, expect_ok=False)
    if "missing required fields for task" not in proc.stderr:
        fail("legacy setup aliases were not normalized before gap validation")
    placeholder = json.dumps({
        "workflow_mode": "full_shortlist",
        "output_mode": "verified",
        "profile": {
            "target_degree_level": "TBD",
            "target_intake": "TBD",
            "target_countries": ["TBD"],
            "target_field": "TBD",
            "gpa_value": "TBD",
            "gpa_scale": "TBD",
            "budget_annual": "TBD",
        },
    })
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=placeholder, expect_ok=False)

    for path in (ROOT / "tests" / "fixtures").glob("*.json"):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        if any(value not in ("", [], {}) for value in fixture.get("profile", {}).values()):
            fail(f"fixture contains seeded applicant profile data: {path.relative_to(ROOT)}")
        if fixture.get("applicant") not in (None, {}):
            fail(f"fixture contains seeded applicant data: {path.relative_to(ROOT)}")
        if fixture.get("applicant_evidence") not in (None, []):
            fail(f"fixture contains seeded applicant evidence: {path.relative_to(ROOT)}")
        if fixture.get("evidence_records") not in (None, []):
            fail(f"fixture contains seeded evidence records: {path.relative_to(ROOT)}")


def main() -> None:
    check_schema()
    check_setup_references()
    check_fixtures_and_template()
    print("OK: setup contract checks passed")


if __name__ == "__main__":
    main()
