#!/usr/bin/env python3
"""Validate admissions setup JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ALLOWED_WORKFLOW_MODES = {
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
}

ALLOWED_OUTPUT_MODES = {"brainstorm", "draft", "source_backed", "verified"}

WORKFLOW_ALIASES = {
    "shortlist": "full_shortlist",
    "requirement_check": "requirement_audit",
    "visa_readiness": "visa_route",
    "essay_plan": "essay_sop",
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
        ("gpa_value", "academic_background", "current_qualification", "current_major"),
    ],
    "full_shortlist": [
        ("target_degree_level", "degree_level"),
        ("target_intake", "intake_term"),
        ("target_countries", "target_country_or_region"),
        ("target_field", "subject_area"),
        ("gpa_value", "academic_background", "current_qualification"),
        ("gpa_scale", "academic_background", "current_qualification"),
        ("budget_annual", "budget"),
    ],
    "exact_program_selection": [
        ("target_degree_level", "degree_level"),
        ("target_field", "subject_area"),
        ("target_countries", "target_country_or_region"),
        ("gpa_value", "academic_background", "current_qualification"),
    ],
    "requirement_audit": [
        ("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"),
        ("applicant_qualification", "current_qualification", "academic_background"),
        ("source_policy",),
    ],
    "essay_sop": [
        ("program_name", "target_programs"),
        ("prompt", "essay_prompt"),
        ("word_limit",),
        ("applicant_background", "academic_background", "current_qualification"),
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
        ("citizenship_countries", "citizenship"),
        ("target_countries", "destination_country", "target_country_or_region"),
    ],
    "source_refresh": [
        ("source_urls", "source_url", "program_name_or_url", "program_names_or_urls"),
    ],
    "visa_route": [
        ("citizenship_countries", "citizenship"),
        ("target_countries", "destination_country", "target_country_or_region"),
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
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
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
    print('OK: setup validation passed')


if __name__ == '__main__':
    main()
