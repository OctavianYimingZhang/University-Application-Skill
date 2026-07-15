#!/usr/bin/env python3
"""Validate admissions setup JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_evidence import effective_fact_class, evidence_passes, validate_evidence_record

ALLOWED_WORKFLOW_MODES = {
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
}

ALLOWED_OUTPUT_MODES = {"brainstorm", "draft", "source_backed", "verified"}

WORKFLOW_ALIASES = {
    "shortlist": "full_shortlist",
    "requirement_check": "requirement_audit",
    "visa_readiness": "visa_readiness",
    "visa_route": "visa_readiness",
    "essay_plan": "essay_sop",
    "application_writing_studio": "essay_sop",
    "materials_check": "materials_check",
}

OUTPUT_ALIASES = {
    "chat_summary": "draft",
    "table": "draft",
    "workbook": "draft",
    "source_backed_table": "source_backed",
    "verified_workbook": "verified",
}

REQUIRED_BY_WORKFLOW = {
    "quick_triage": [
        ("target_degree_level", "degree_level"),
        ("target_countries", "target_country_or_region"),
        ("target_field", "subject_area"),
    ],
    "full_shortlist": [
        ("target_degree_level", "degree_level"),
        ("target_intake", "intake_term"),
        ("target_countries", "target_country_or_region"),
        ("target_field", "subject_area"),
    ],
    "exact_program_selection": [
        ("target_degree_level", "degree_level"),
        ("target_field", "subject_area"),
        ("target_countries", "target_country_or_region"),
    ],
    "requirement_audit": [
        ("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"),
        ("target_intake", "intake_term", "application_cycle"),
    ],
    "essay_sop": [
        ("program_name", "program_name_or_url", "program_names_or_urls", "target_programs"),
        ("prompt", "essay_prompt"),
        ("word_limit", "character_limit"),
        ("audience",),
        ("intended_use", "submission_use"),
        ("applicant_background", "academic_background", "current_qualification"),
        ("output_location", "output_path"),
        ("overwrite_existing", "overwrite_decision"),
    ],
    "materials_check": [
        ("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"),
        ("target_intake", "intake_term", "application_cycle"),
        ("document_inventory", "application_materials", "documents"),
    ],
    "workbook_build": [
        ("export_format",),
    ],
    "programme_table_cleaning": [
        ("source_workbook_dir_or_files", "source_workbook_dir", "source_workbook_files"),
        ("cleaned_output_dir",),
    ],
    "submission_readiness": [
        ("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"),
        ("target_intake", "intake_term", "application_cycle"),
        ("document_inventory", "application_materials", "documents"),
    ],
    "source_refresh": [
        ("source_urls", "source_url", "program_name_or_url", "program_names_or_urls"),
    ],
    "visa_readiness": [
        ("citizenship_countries", "citizenship"),
        ("target_countries", "destination_country", "target_country_or_region"),
        ("visa_application_country",),
        ("target_intake", "intake_term", "intended_intake"),
        ("budget_annual", "funding_plan", "budget"),
    ],
}


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def is_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {
            "-", "n/a", "none", "not confirmed", "not provided", "placeholder",
            "source required", "tbc", "tbd", "todo", "unknown",
        }
    if isinstance(value, (list, tuple, set)):
        return any(is_present(item) for item in value)
    if isinstance(value, dict):
        return any(is_present(item) for item in value.values())
    return True


def values_for(data: dict, aliases: tuple[str, ...]) -> list[object]:
    profile = data.get("profile") if isinstance(data.get("profile"), dict) else {}
    values = []
    for alias in aliases:
        if alias in profile:
            values.append(profile.get(alias))
        if alias in data:
            values.append(data.get(alias))
    return values


def has_any(data: dict, aliases: tuple[str, ...]) -> bool:
    return any(is_present(value) for value in values_for(data, aliases))


def display_group(aliases: tuple[str, ...]) -> str:
    if len(aliases) == 1:
        return aliases[0]
    return "one of " + ", ".join(aliases)


def normalize_workflow_mode(value: object) -> str:
    mode = str(value or "")
    return WORKFLOW_ALIASES.get(mode, mode)


def normalize_output_mode(data: dict) -> str:
    if data.get("output_mode"):
        return str(data["output_mode"])
    output_format = str(data.get("output_format") or "")
    return OUTPUT_ALIASES.get(output_format, output_format)


def first_present(data: dict, aliases: tuple[str, ...]) -> object | None:
    for value in values_for(data, aliases):
        if is_present(value):
            return value
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('setup_json', type=Path)
    args = parser.parse_args()
    data = json.loads(args.setup_json.read_text(encoding='utf-8'))

    workflow_mode = normalize_workflow_mode(data.get("workflow_mode") or data.get("task_type"))
    output_mode = normalize_output_mode(data)
    if not workflow_mode:
        fail("missing workflow_mode")
    if not output_mode:
        fail("missing output_mode")
    if workflow_mode not in ALLOWED_WORKFLOW_MODES:
        fail(f"unsupported workflow_mode: {workflow_mode}")
    if output_mode not in ALLOWED_OUTPUT_MODES:
        fail(f"unsupported output_mode: {output_mode}")

    missing = [
        display_group(group)
        for group in REQUIRED_BY_WORKFLOW.get(workflow_mode, [])
        if not has_any(data, group)
    ]
    if missing:
        fail('missing required fields for task: ' + ', '.join(missing))

    evidence_records = data.get("evidence_records", [])
    if not isinstance(evidence_records, list):
        fail("evidence_records must be an array")
    for index, record in enumerate(evidence_records):
        errors = validate_evidence_record(record)
        if errors:
            fail(f"invalid evidence_records[{index}]: " + "; ".join(errors))
        fact_class = effective_fact_class(
            record,
            "official_requirement" if workflow_mode == "requirement_audit" else "writing",
        )
        if fact_class == "mutable_official_fact":
            purpose = "official_requirement"
        elif workflow_mode == "materials_check":
            purpose = "material_document"
        elif workflow_mode == "submission_readiness":
            purpose = "submission"
        elif workflow_mode == "requirement_audit":
            purpose = "applicant_comparison"
        else:
            purpose = str(record.get("evidence_use") or "writing")
        current_cycle = first_present(data, ("application_cycle", "target_intake", "intake_term"))
        if output_mode == "verified" and not evidence_passes(
            record,
            purpose=purpose,
            current_cycle=str(current_cycle) if current_cycle is not None else None,
        ):
            fail(f"evidence_records[{index}] does not satisfy the evidence passing invariant")
    print('OK: setup validation passed')


if __name__ == '__main__':
    main()
