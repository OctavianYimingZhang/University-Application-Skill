#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

from validate_evidence import is_placeholder

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
    "visa_readiness": [
        "citizenship_destination_intake_review",
        "official_government_source_collection",
        "provenance_cycle_access_and_staleness_review",
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
    "visa_readiness": "Visa Readiness",
}

ROUTE_OUTPUTS = {
    "program_research": ["source_backed_programme_list", "shortlist_table", "source_log"],
    "requirement_audit": ["requirement_table", "gap_list", "source_log"],
    "materials_check": ["materials_checklist", "document_validation_status", "blockers"],
    "application_writing_studio": ["writing_brief", "evidence_map", "narrative_options", "approved_structure", "draft_if_approved"],
    "submission_readiness": ["final_readiness_checklist", "blockers", "next_actions"],
    "programme_table_cleaning": ["cleaned_programme_workbook", "verification_report"],
    "visa_readiness": ["visa_readiness_notes", "source_log", "document_gaps"],
}


def normalize_prompt(prompt: str) -> str:
    decomposed = unicodedata.normalize("NFKD", prompt or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def prompt_has_any(prompt: str, signals: list[str]) -> bool:
    return any(signal in prompt for signal in signals)


def profile_value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return not is_placeholder(value)
    if isinstance(value, (list, tuple, set)):
        return any(profile_value_present(item) for item in value)
    if isinstance(value, dict):
        return any(profile_value_present(item) for item in value.values())
    return True


def output_language(prompt: str, setup: dict[str, Any]) -> str:
    configured = str(setup.get("requested_output_language") or "").strip()
    if configured:
        return configured
    normalized = normalize_prompt(prompt)
    explicit_requests = {
        "Chinese": ["respond in chinese", "answer in chinese", "output in chinese", "请用中文", "用中文回答", "中文输出"],
        "Spanish": ["respond in spanish", "answer in spanish", "responde en espanol", "respuesta en espanol"],
        "French": ["respond in french", "answer in french", "reponds en francais", "reponse en francais"],
    }
    for language, signals in explicit_requests.items():
        if prompt_has_any(normalized, signals):
            return language
    return "English"


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
        "visa_readiness": "visa_readiness",
        "visa_route": "visa_readiness",
        "programme_table_cleaning": "programme_table_cleaning",
    }
    if workflow_mode in workflow_aliases:
        return workflow_aliases[workflow_mode]

    p = normalize_prompt(prompt)
    if prompt_has_any(p, [
        "programme table", "program table", "programme workbook", "program workbook", "clean workbook",
        "clean programme", "clean program", "catalogue maintenance", "catalog maintenance",
        "清理项目表", "清理项目目录", "维护项目目录", "课程表格维护", "limpiar tabla de programas",
        "mantenimiento del catalogo", "nettoyer le catalogue",
    ]):
        return "programme_table_cleaning"
    if prompt_has_any(p, [
        "visa", "visado", "student route", "immigration", "citizenship", "cas readiness",
        "签证", "学生签", "移民材料", "居留许可", "permis de sejour",
    ]):
        return "visa_readiness"
    if prompt_has_any(p, [
        "submit", "submission", "final checklist", "application readiness", "before applying",
        "提交前", "递交前", "最终检查", "申请是否就绪", "antes de enviar", "avant de soumettre",
    ]):
        return "submission_readiness"
    if prompt_has_any(p, [
        "personal statement", "statement of purpose", "sop", "essay", "supplement", "writing studio",
        "文书", "个人陈述", "动机信", "目的陈述", "carta de motivacion", "lettre de motivation",
    ]):
        return "application_writing_studio"
    if prompt_has_any(p, [
        "material", "document", "transcript", "reference", "passport", "upload", "document checklist",
        "申请材料", "成绩单", "推荐信", "护照材料", "材料是否齐全", "documentos de solicitud", "dossier de candidature",
    ]):
        return "materials_check"
    if prompt_has_any(p, [
        "requirement", "entry requirement", "language requirement", "ielts", "toefl", "fee", "tuition", "audit",
        "入学要求", "申请要求", "语言要求", "学费要求", "requisitos de admision", "conditions d'admission",
    ]):
        return "requirement_audit"
    return "program_research"


def profile_gaps(setup: dict[str, Any], route: str | None = None) -> list[str]:
    profile = setup.get("profile") if isinstance(setup.get("profile"), dict) else {}
    if route == "programme_table_cleaning":
        return []
    fields = [
        ("target_degree_level", "target degree level"),
        ("target_countries", "destination country or region"),
        ("target_field", "target field"),
        ("target_intake", "target intake"),
        ("gpa_value", "academic result"),
        ("language_status", "language test status"),
    ]
    if route == "visa_readiness":
        fields = [
            ("citizenship_countries", "citizenship"),
            ("target_countries", "destination country or region"),
            ("visa_application_country", "visa application location"),
            ("target_intake", "target intake"),
            ("budget_annual", "funding basis"),
        ]
    gaps = []
    for key, label in fields:
        value = profile.get(key, setup.get(key))
        if not profile_value_present(value):
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
        "profile_gaps": profile_gaps(setup, route),
        "output_language": output_language(prompt, setup),
        "default_output_language": "English",
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
        ("student visa route for UK", "visa_readiness"),
        ("检查学生签证准备情况", "visa_readiness"),
        ("帮我规划个人陈述", "application_writing_studio"),
        ("核对这个项目的入学要求", "requirement_audit"),
        ("检查我的申请材料是否齐全", "materials_check"),
        ("提交前做最终检查", "submission_readiness"),
        ("维护并清理项目目录表", "programme_table_cleaning"),
        ("Buscar programas universitarios oficiales", "program_research"),
    ]
    for prompt, expected in cases:
        got = detect_route(prompt)
        assert got == expected, (prompt, got, expected)
    setup = {"workflow_mode": "essay_sop", "profile": {"target_degree_level": "masters"}}
    assert build_plan("", setup)["route"] == "application_writing_studio"
    assert build_plan("chance probability safe school")["probability_prediction"] == "prohibited"
    assert build_plan("帮我规划个人陈述")["output_language"] == "English"
    assert build_plan("帮我规划个人陈述，请用中文回答")["output_language"] == "Chinese"
    assert build_plan("", {"requested_output_language": "Chinese"})["output_language"] == "Chinese"
    assert "target degree level" in build_plan("", {"profile": {"target_degree_level": "TBD"}})["profile_gaps"]
    visa_gaps = build_plan("student visa route for UK")["profile_gaps"]
    assert "citizenship" in visa_gaps and "academic result" not in visa_gaps


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
