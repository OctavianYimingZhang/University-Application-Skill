#!/usr/bin/env python3
"""Create a minimal admissions setup template."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WORKFLOW_ALIASES = {
    "shortlist": "full_shortlist",
    "requirement_check": "requirement_audit",
    "visa_readiness": "visa_readiness",
    "visa_route": "visa_readiness",
    "essay_plan": "essay_sop",
}

OUTPUT_ALIASES = {
    "chat_summary": "draft",
    "table": "draft",
    "workbook": "draft",
    "source_backed_table": "source_backed",
    "verified_workbook": "verified",
}


def build_blank_memory() -> dict:
    return {
        "schema_version": "2026-06-26",
        "privacy_mode": "local_only",
        "profile": {},
        "course_memory": [],
        "lecture_delta_memory": [],
        "writing_voice": {
            "samples": [],
            "inferred_rules": [],
            "revision_rules": [],
        },
        "notes_preferences": [],
        "exam_preparation_preferences": [],
        "application_preferences": [],
        "source_log": [],
        "conflicts": [],
    }


def build_template(workflow_mode: str, output_mode: str) -> dict:
    workflow_mode = WORKFLOW_ALIASES.get(workflow_mode, workflow_mode)
    output_mode = OUTPUT_ALIASES.get(output_mode, output_mode)
    data = {
        "user_setup_id": "",
        "workflow_mode": workflow_mode,
        "output_mode": output_mode,
        "recommendation_count": 10,
        "preferred_depth": "standard",
        "ask_style": "compact_batches",
        "source_policy": "official_only",
        "privacy_mode": "public_redacted",
        "export_format": "table",
        "ranking_weight": "",
        "admission_safety_weight": "",
        "budget_weight": "",
        "city_weight": "",
        "career_weight": "",
        "research_fit_weight": "",
        "visa_work_route_weight": "",
        "deadline_feasibility_weight": "",
        "profile": {
            "target_degree_level": "",
            "target_intake": "",
            "target_countries": [],
            "citizenship_countries": [],
            "residence_country": "",
            "education_country": "",
            "passport_country": "",
            "visa_application_country": "",
            "target_field": "",
            "current_institution": "",
            "current_major": "",
            "gpa_value": "",
            "gpa_scale": "",
            "language_status": "",
            "core_courses": [],
            "budget_annual": "",
            "constraints": [],
        },
        "memory": build_blank_memory(),
        "evidence_records": [],
    }
    if workflow_mode == "programme_table_cleaning":
        data["source_workbook_dir_or_files"] = []
        data["cleaned_output_dir"] = ""
        data["copy_back_requested"] = False
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workflow-mode', '--task-type', dest='workflow_mode', default='full_shortlist')
    parser.add_argument('--output-mode', '--output-format', dest='output_mode', default='draft')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = build_template(args.workflow_mode, args.output_mode)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
