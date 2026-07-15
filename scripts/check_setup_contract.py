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
    "materials_check",
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
    "program_name",
    "program_name_or_url",
    "application_cycle",
    "prompt",
    "word_limit",
    "character_limit",
    "audience",
    "intended_use",
    "output_location",
    "overwrite_existing",
    "document_inventory",
    "revision_decision_ledger",
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
    source = evidence.get("properties", {}).get("source", {})
    source_text = json.dumps(source)
    for source_type in ("public_url", "local_document", "user_confirmation"):
        if source_type not in source_text:
            fail(f"schema evidence source type missing: {source_type}")
    local_with_url = {
        "type": "local_document",
        "url": "https://www.example.edu/local-copy",
        "title": "Applicant CV",
        "publisher": "Applicant",
    }

    def branch_matches(instance: dict, branch: dict) -> bool:
        if any(field not in instance for field in branch.get("required", [])):
            return False
        for field, field_schema in branch.get("properties", {}).items():
            if field in instance and "const" in field_schema and instance[field] != field_schema["const"]:
                return False
        return True

    if any(branch_matches(local_with_url, branch) for branch in source.get("anyOf", [])):
        fail("user-setup schema lets local_document URL bypass opaque_local_ref")


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
    if "application_location: [profile.visa_application_country, visa_application_country]" not in gates:
        fail("visa setup gate is missing visa_application_country")


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

    requirement_only = json.dumps({
        "workflow_mode": "requirement_audit",
        "output_mode": "source_backed",
        "program_name_or_url": "https://www.example.edu/programme",
        "application_cycle": "2026-27",
    })
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=requirement_only)
    materials_only = json.dumps({
        "workflow_mode": "materials_check",
        "output_mode": "draft",
        "program_name_or_url": "https://www.example.edu/programme",
        "application_cycle": "2026-27",
        "document_inventory": [{"document": "CV", "status": "available"}],
    })
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=materials_only)
    materials_without_cycle = json.dumps({
        "workflow_mode": "materials_check",
        "output_mode": "draft",
        "program_name_or_url": "https://www.example.edu/programme",
        "document_inventory": [{"document": "CV", "status": "available"}],
    })
    missing_cycle = run(
        ["python3", "scripts/validate_setup.py", "/dev/stdin"],
        input_text=materials_without_cycle,
        expect_ok=False,
    )
    if "application_cycle" not in missing_cycle.stderr:
        fail("materials_check without an application cycle did not fail the route-specific gate")

    character_limit_writing = json.dumps({
        "workflow_mode": "essay_sop",
        "output_mode": "draft",
        "program_name": "Example MRes",
        "prompt": "Explain your preparation.",
        "character_limit": 4000,
        "audience": "Admissions committee",
        "intended_use": "Programme application",
        "applicant_background": "Supplied in the current task",
        "output_location": "chat",
        "overwrite_existing": False,
    })
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=character_limit_writing)
    writing_with_programme_url = json.dumps({
        **json.loads(character_limit_writing),
        "program_name": "",
        "program_name_or_url": "https://www.example.edu/programme",
    })
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=writing_with_programme_url)

    local_with_url_but_no_ref = json.dumps({
        "workflow_mode": "requirement_audit",
        "output_mode": "verified",
        "program_name": "Example MRes",
        "application_cycle": "2026-27",
        "evidence_records": [{
            "evidence_id": "local-no-ref",
            "value": "Applicant fact from a local CV.",
            "fact_class": "applicant_personal_fact",
            "evidence_use": "applicant_comparison",
            "source": {
                "type": "local_document",
                "url": "https://www.example.edu/cv-copy",
                "title": "Applicant CV",
                "publisher": "Applicant"
            },
            "evidence_date": "2026-07-15",
            "confirmation_status": "explicitly_confirmed",
            "confirmed_at": "2026-07-15T00:00:00+00:00",
            "source_availability": "available",
            "fact_verification": "verified",
            "completeness": "complete",
            "application_cycle": "2026-27",
            "accessed_at": "2026-07-15T00:00:00+00:00",
            "staleness": "fresh"
        }],
    })
    invalid_local = run(
        ["python3", "scripts/validate_setup.py", "/dev/stdin"],
        input_text=local_with_url_but_no_ref,
        expect_ok=False,
    )
    if "opaque_local_ref" not in invalid_local.stderr:
        fail("local_document with a URL bypassed the required opaque_local_ref")

    research_profile = {
        "target_degree_level": "masters",
        "target_countries": ["UK"],
        "target_field": "neuroscience",
    }
    for workflow_mode in ("quick_triage", "exact_program_selection"):
        setup = {
            "workflow_mode": workflow_mode,
            "output_mode": "source_backed",
            "profile": research_profile,
        }
        run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=json.dumps(setup))
        plan = json.loads(run(
            ["python3", "scripts/plan_workflow.py", "--setup-json", "/dev/stdin"],
            input_text=json.dumps(setup),
        ).stdout)
        if plan.get("profile_gaps"):
            fail(f"{workflow_mode} planner drifts from its setup gate: {plan['profile_gaps']}")

    visa_setup = {
        "workflow_mode": "visa_readiness",
        "output_mode": "source_backed",
        "profile": {
            "citizenship_countries": ["China"],
            "target_countries": ["UK"],
            "target_intake": "2026-27",
            "budget_annual": "confirmed funding plan",
        },
    }
    missing_visa_location = run(
        ["python3", "scripts/validate_setup.py", "/dev/stdin"],
        input_text=json.dumps(visa_setup),
        expect_ok=False,
    )
    if "visa_application_country" not in missing_visa_location.stderr:
        fail("visa setup without visa_application_country did not fail")
    visa_setup["profile"]["visa_application_country"] = "Taiwan"
    run(["python3", "scripts/validate_setup.py", "/dev/stdin"], input_text=json.dumps(visa_setup))
    visa_plan = json.loads(run(
        ["python3", "scripts/plan_workflow.py", "--setup-json", "/dev/stdin"],
        input_text=json.dumps(visa_setup),
    ).stdout)
    if visa_plan.get("profile_gaps"):
        fail(f"visa planner drifts from its setup gate: {visa_plan['profile_gaps']}")

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
