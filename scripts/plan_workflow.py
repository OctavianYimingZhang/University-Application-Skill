#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROUTE_ACTIONS: dict[str, list[str]] = {
    "program_research": [
        "profile_intake",
        "official_source_collection",
        "programme_table",
        "shortlist_without_probability",
        "source_log",
    ],
    "requirement_audit": [
        "programme_source_collection",
        "hard_requirement_extraction",
        "applicant_requirement_comparison",
        "gap_and_blocker_review",
        "source_log",
    ],
    "materials_check": [
        "source_backed_document_checklist",
        "simulated_evidence_inventory",
        "document_status_review",
        "writing_gaps_route_if_needed",
        "submission_blockers",
    ],
    "application_writing_studio": [
        "writing_brief_lock",
        "evidence_inventory",
        "narrative_options",
        "programme_fit_plan",
        "critical_review",
        "planning_approval",
        "draft_gate",
    ],
    "submission_readiness": [
        "final_programme_selection_check",
        "deadline_and_fee_review",
        "documents_and_language_review",
        "visa_sensitive_gap_review",
        "final_action_list",
    ],
    "programme_table_cleaning": [
        "source_workbook_inventory",
        "programme_table_cleaning",
        "lineage_preservation",
        "cleaned_workbook_verification",
    ],
    "visa_route": [
        "citizenship_destination_intake_review",
        "official_government_source_collection",
        "funding_and_document_gap_review",
        "visa_readiness_notes",
    ],
}

ROUTE_LABELS = {
    "program_research": "Program Research",
    "requirement_audit": "Requirement Audit",
    "materials_check": "Materials Check",
    "application_writing_studio": "Application Writing Studio",
    "submission_readiness": "Submission Readiness",
    "programme_table_cleaning": "Programme Table Cleaning",
    "visa_route": "Visa Route",
}

ROUTE_OUTPUTS = {
    "program_research": ["source_backed_programme_list", "shortlist_table", "source_log"],
    "requirement_audit": ["requirement_table", "gap_list", "source_log"],
    "materials_check": ["materials_checklist", "document_validation_status", "blockers"],
    "application_writing_studio": ["writing_brief", "evidence_map", "narrative_options", "approved_structure", "draft_if_approved"],
    "submission_readiness": ["final_readiness_checklist", "blockers", "next_actions"],
    "programme_table_cleaning": ["cleaned_programme_workbook", "verification_report"],
    "visa_route": ["visa_readiness_notes", "source_log", "document_gaps"],
}


def prompt_has_any(prompt: str, signals: list[str]) -> bool:
    return any(signal in prompt for signal in signals)


def detect_route(prompt: str, setup: dict[str, Any] | None = None) -> str:
    setup = setup or {}
    workflow_mode = str(setup.get("workflow_mode") or setup.get("task_type") or "").strip()
    workflow_aliases = {
        "shortlist": "program_research",
        "full_shortlist": "program_research",
        "quick_triage": "program_research",
        "exact_program_selection": "program_research",
        "requirement_check": "requirement_audit",
        "requirement_audit": "requirement_audit",
        "essay_plan": "application_writing_studio",
        "essay_sop": "application_writing_studio",
        "materials_check": "materials_check",
        "submission_readiness": "submission_readiness",
        "visa_readiness": "visa_route",
        "visa_route": "visa_route",
        "programme_table_cleaning": "programme_table_cleaning",
    }
    if workflow_mode in workflow_aliases:
        return workflow_aliases[workflow_mode]

    p = (prompt or "").lower()
    if prompt_has_any(p, ["programme table", "program table", "programme workbook", "program workbook", "clean workbook", "clean programme", "clean program", "xlsx", "csv"]):
        return "programme_table_cleaning"
    if prompt_has_any(p, ["visa", "cas", "student route", "immigration", "citizenship"]):
        return "visa_route"
    if prompt_has_any(p, ["submit", "submission", "final checklist", "readiness", "deadline", "before applying"]):
        return "submission_readiness"
    if prompt_has_any(p, ["personal statement", "statement of purpose", "sop", "essay", "supplement", "writing studio", "文书"]):
        return "application_writing_studio"
    if prompt_has_any(p, ["material", "document", "transcript", "reference", "passport", "upload", "checklist"]):
        return "materials_check"
    if prompt_has_any(p, ["requirement", "entry requirement", "language", "ielts", "toefl", "fee", "tuition", "audit"]):
        return "requirement_audit"
    return "program_research"


def profile_gaps(setup: dict[str, Any]) -> list[str]:
    profile = setup.get("profile") if isinstance(setup.get("profile"), dict) else {}
    gaps = []
    for key, label in [
        ("target_degree_level", "target degree level"),
        ("target_countries", "destination country or region"),
        ("target_field", "target field"),
        ("target_intake", "target intake"),
        ("gpa_value", "academic result"),
        ("language_status", "language test status"),
    ]:
        value = profile.get(key, setup.get(key))
        if value in (None, "", [], {}):
            gaps.append(label)
    return gaps


def build_plan(prompt: str, setup: dict[str, Any] | None = None) -> dict[str, Any]:
    setup = setup or {}
    route = detect_route(prompt, setup)
    source_policy = setup.get("source_policy") or "official_only"
    return {
        "status": "preliminary",
        "route": route,
        "route_label": ROUTE_LABELS[route],
        "actions": ROUTE_ACTIONS[route],
        "proposed_outputs": ROUTE_OUTPUTS[route],
        "human_review_required": True,
        "human_review_targets": [
            "application_route",
            "source_policy",
            "profile_gaps",
            "writing_brief_and_evidence" if route == "application_writing_studio" else "route_specific_follow_up",
        ],
        "source_policy": source_policy,
        "profile_gaps": profile_gaps(setup),
        "probability_prediction": "prohibited",
    }


def load_setup(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def self_test() -> None:
    cases = [
        ("find me biosciences programmes", "program_research"),
        ("check IELTS and A-level requirements", "requirement_audit"),
        ("simulate my documents checklist", "materials_check"),
        ("help brainstorm my personal statement", "application_writing_studio"),
        ("final submission readiness before applying", "submission_readiness"),
        ("clean this programme workbook", "programme_table_cleaning"),
        ("student visa route for UK", "visa_route"),
    ]
    for prompt, expected in cases:
        got = detect_route(prompt)
        assert got == expected, (prompt, got, expected)
    setup = {"workflow_mode": "essay_sop", "profile": {"target_degree_level": "masters"}}
    assert build_plan("", setup)["route"] == "application_writing_studio"
    assert build_plan("chance probability safe school")["probability_prediction"] == "prohibited"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a preliminary University Application workflow plan.")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--setup-json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("OK: plan_workflow self-test passed")
        return
    print(json.dumps(build_plan(args.prompt, load_setup(args.setup_json)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
