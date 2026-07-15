#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from validate_evidence import is_placeholder

ROUTE_ACTIONS: dict[str, list[str]] = {
    "program_research": [
        "profile_intake",
        "research_degree_type_verification",
        "official_source_collection",
        "supervisor_contact_status",
        "supervisor_research_and_publication_fit",
        "programme_structure_and_module_fit",
        "programme_table",
        "shortlist_without_probability",
        "source_log",
    ],
    "requirement_audit": [
        "programme_source_collection",
        "hard_requirement_extraction",
        "writing_prompt_word_limit_and_ai_policy",
        "deadline_fee_and_pre_application_action_review",
        "applicant_requirement_comparison",
        "gap_and_blocker_review",
        "source_log",
    ],
    "materials_check": [
        "source_backed_document_requirements",
        "applicant_document_inventory",
        "document_status_review",
        "writing_gaps_route_if_needed",
        "submission_blockers",
    ],
    "application_writing_studio": [
        "writing_brief_lock",
        "evidence_inventory",
        "revision_decision_ledger",
        "narrative_options",
        "programme_fit_plan",
        "shared_narrative_and_programme_adaptation",
        "critical_review",
        "planning_approval",
        "draft_gate",
        "revision_coverage_gate",
    ],
    "submission_readiness": [
        "application_case_cycle_check",
        "deadline_and_fee_review",
        "portal_and_document_status_review",
        "visa_sensitive_gap_review",
        "submission_blockers_and_next_actions",
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
    "requirement_audit": ["requirement_explanation", "requirement_table", "gap_list", "source_log"],
    "materials_check": ["materials_checklist", "document_validation_status", "blockers"],
    "application_writing_studio": [
        "writing_brief",
        "evidence_map",
        "revision_decision_ledger",
        "narrative_options",
        "approved_structure",
        "draft_if_approved",
        "revision_coverage",
    ],
    "submission_readiness": ["final_readiness_checklist", "blockers", "next_actions"],
    "programme_table_cleaning": ["cleaned_programme_workbook", "verification_report"],
    "visa_readiness": ["visa_readiness_notes", "source_log", "document_gaps"],
}


def normalize_prompt(prompt: str) -> str:
    decomposed = unicodedata.normalize("NFKD", prompt or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def prompt_has_any(prompt: str, signals: list[str]) -> bool:
    return any(signal in prompt for signal in signals)


def explicit_writing_request(prompt: str) -> bool:
    """Recognize an explicit drafting/revision act even when requirements or submission are mentioned."""
    normalized = normalize_prompt(prompt)
    if prompt_has_any(normalized, [
        "write my personal statement", "revise my personal statement", "polish my personal statement",
        "write my sop", "draft my sop", "revise my sop", "polish my sop", "brainstorm my essay",
        "brainstorm my personal statement", "plan my personal statement", "writing studio",
        "programme-fit paragraph", "program-fit paragraph",
        "写个人陈述", "修改个人陈述", "润色个人陈述", "规划个人陈述", "写文书", "改文书",
        "修改文书", "润色文书", "文书修改", "文书润色", "写动机信", "修改动机信",
        "帮我写sop", "帮我写 sop", "写sop", "写 sop",
        "carta de motivacion", "lettre de motivation",
    ]):
        return True
    return bool(re.search(
        r"(?:^|[.!?]\s+)(?:please\s+|(?:can|could|would) you\s+|i (?:need|want) you to\s+)?"
        r"(?:draft|write|revise|rewrite|edit|polish|plan|outline|improve)\b.{0,90}"
        r"\b(?:statement of purpose|personal statement|sop|admissions? essay|motivation letter|"
        r"programme-fit paragraph|program-fit paragraph|application paragraph)\b",
        normalized,
    ))


def explicit_materials_readiness_request(prompt: str) -> bool:
    """Recognize comparison of the applicant's current materials, not a requirements-only audit."""
    normalized = normalize_prompt(prompt)
    if prompt_has_any(normalized, [
        "are my materials complete", "are my documents complete", "check my application materials",
        "simulate my documents", "document checklist", "document readiness", "materials readiness",
        "validate my transcript", "check my references", "我的材料是否齐全", "材料是否齐全",
        "检查我的申请材料", "核对我的申请材料", "检查成绩单", "检查推荐信",
        "护照材料是否齐全", "documentos de solicitud", "dossier de candidature",
    ]):
        return True
    return bool(re.search(
        r"\b(?:check|assess|review|verify|tell me whether)\b.{0,100}"
        r"\b(?:my|our)\b.{0,30}\b(?:application )?(?:materials?|documents?)\b.{0,80}"
        r"\b(?:ready|complete|missing|submit|submission)\b",
        normalized,
    ))


def supervisor_fit_requested(prompt: str, setup: dict[str, Any] | None = None) -> bool:
    normalized = normalize_prompt(prompt)
    if prompt_has_any(normalized, [
        "find supervisors", "identify potential supervisors", "potential supervisors", "research supervisors",
        "compare supervisors", "supervisor publications", "representative publications",
        "which supervisor", "supervisor fit", "supervisor research fit", "faculty research fit",
        "programme fit", "program fit", "programme fit research", "program fit research",
        "查找导师", "筛选导师", "导师筛选", "导师匹配", "导师研究方向", "导师论文",
        "课程匹配", "项目匹配", "研究方向匹配",
    ]) or re.search(
        r"(?:find|identify|compare|match|shortlist).{0,60}supervisors?"
        r"|supervisors?.{0,100}(?:current research|representative publications?|research fit|programme fit|program fit)"
        r"|(?:查找|寻找|筛选|匹配|比较).{0,20}导师"
        r"|导师.{0,12}(?:筛选|匹配|比较)",
        normalized,
    ):
        return True
    setup = setup or {}
    return profile_value_present(
        setup.get("supervisor_fit_scope")
        or setup.get("research_fit_scope")
        or setup.get("fit_scope")
    )


def supervisor_contact_requirement_requested(prompt: str, setup: dict[str, Any] | None = None) -> bool:
    normalized = normalize_prompt(prompt)
    if prompt_has_any(normalized, [
        "supervisor contact", "contact a supervisor", "contact the supervisor", "contact supervisors",
        "need to contact", "must i contact", "should i contact", "contact is required",
        "contact requirement", "find a supervisor before applying", "提前联系导师", "联系导师要求",
        "申请前联系导师", "需要联系导师", "是否联系导师",
    ]):
        return True
    setup = setup or {}
    if setup.get("verify_supervisor_contact") is True:
        return True
    scope = normalize_prompt(str(
        setup.get("supervisor_fit_scope")
        or setup.get("research_fit_scope")
        or setup.get("fit_scope")
        or ""
    ))
    return scope in {
        "fit + evidence", "fit and evidence", "fit_evidence", "fit_and_evidence",
        "contact requirement only", "contact_requirement", "contact_requirement_only",
    }


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


def detect_route(prompt: str, setup: dict[str, Any] | None = None) -> str | None:
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
        "application_writing_studio": "application_writing_studio",
        "materials_check": "materials_check",
        "submission_readiness": "submission_readiness",
        "visa_readiness": "visa_readiness",
        "visa_route": "visa_readiness",
        "programme_table_cleaning": "programme_table_cleaning",
    }
    if workflow_mode in ROUTE_ACTIONS:
        return workflow_mode
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
    generic_word_format = prompt_has_any(p, [
        "format this word document", "beautify word", "word formatting", "backup and format",
        "back up my word document", "backup my word document", "improve the typography", "fix the spacing",
        "备份并美化", "美化word", "word排版", "word 排版", "通用排版",
    ])
    admissions_writing_anchor = prompt_has_any(p, [
        "personal statement", "statement of purpose", "sop", "admissions essay",
        "个人陈述", "动机信", "目的陈述", "申请文书",
    ])
    # Explicit task acts take precedence over incidental requirement or portal wording.
    if explicit_materials_readiness_request(prompt):
        return "materials_check"
    if explicit_writing_request(prompt):
        return "application_writing_studio"
    combined_supervisor_fit = prompt_has_any(p, [
        "current research", "representative publications", "supervisor publications",
        "supervisor fit", "research fit", "programme fit", "program fit",
    ])
    if supervisor_fit_requested(prompt, setup) and (
        not supervisor_contact_requirement_requested(prompt, setup) or combined_supervisor_fit
    ):
        return "program_research"

    # Requirements take precedence over generic essay or document wording.
    if prompt_has_any(p, [
        "requirement", "entry requirement", "language requirement", "ielts", "toefl", "fee", "tuition", "audit",
        "documents required", "required documents", "what documents", "which documents", "full requirements",
        "essay requirement", "writing requirement", "word limit", "character limit", "application prompt",
        "ai policy", "ai use policy", "application deadline", "pre-application",
        "入学要求", "申请要求", "项目要求", "专业要求", "课程要求", "语言要求", "学费要求",
        "需要什么文书", "需要哪些文书",
        "文书完整要求", "文书的完整要求", "申请文书要求", "文书字数", "文书题目",
        "supervisor contact", "contact a supervisor", "contact the supervisor", "contact supervisors",
        "need to contact a supervisor", "must i contact", "should i contact", "find a supervisor before applying",
        "申请字段", "ai使用", "ai 使用", "截止日期", "申请截止", "提前联系导师", "联系导师要求",
        "申请前联系导师", "需要联系导师", "是否联系导师", "这个项目需要哪些申请材料",
        "该项目需要哪些申请材料", "需要哪些申请材料", "申请材料要求", "要求哪些文书",
        "requisitos de admision", "conditions d'admission",
    ]):
        return "requirement_audit"

    if prompt_has_any(p, [
        "submit", "submission", "final checklist", "application readiness", "before applying",
        "提交前", "递交前", "最终检查", "申请是否就绪", "antes de enviar", "avant de soumettre",
    ]):
        return "submission_readiness"

    if supervisor_fit_requested(prompt, setup) or prompt_has_any(p, [
        "find programmes", "find programs", "find me", "list programmes", "list programs", "programme search",
        "masters programmes", "master programmes", "master's programmes", "masters programs", "master's programs",
        "program search", "shortlist", "research master", "research masters", "research degree",
        "mres", "mphil", "msc by research", "buscar programas universitarios",
        "find supervisors", "research supervisors", "compare supervisors", "supervisor publications",
        "which supervisor", "supervisor fit", "supervisor research fit", "faculty research fit",
        "programme fit", "program fit", "programme fit research", "program fit research",
        "列出项目", "查找项目", "项目筛选", "项目推荐", "研究型硕士", "研究型生物科学硕士",
        "查找导师", "筛选导师", "导师筛选", "导师匹配", "导师研究方向", "导师论文",
        "课程匹配", "项目匹配", "研究方向匹配",
    ]):
        return "program_research"
    if generic_word_format and not admissions_writing_anchor:
        return None
    return None


def route_status(prompt: str, route: str | None) -> str:
    if route is not None:
        return "matched"
    p = normalize_prompt(prompt)
    if prompt_has_any(p, [
        "format this word document", "beautify word", "word formatting", "backup and format",
        "back up my word document", "backup my word document", "improve the typography", "fix the spacing",
        "备份并美化", "美化word", "word排版", "word 排版", "通用排版",
    ]) or prompt_has_any(p, ["not an admissions document", "not an admission document", "非申请文档", "不是申请文档"]):
        return "out_of_scope"
    return "needs_confirmation"


def setup_value(setup: dict[str, Any], *keys: str) -> Any:
    profile = setup.get("profile") if isinstance(setup.get("profile"), dict) else {}
    for key in keys:
        for value in (profile.get(key), setup.get(key)):
            if profile_value_present(value):
                return value
    return None


def prompt_supplies_input(prompt: str, keys: tuple[str, ...]) -> bool:
    """Return whether the prompt explicitly supplies a dimension, without extracting a value."""
    p = normalize_prompt(prompt)
    key_set = set(keys)
    if key_set & {"target_degree_level", "degree_level"}:
        return prompt_has_any(p, [
            "bachelor", "undergraduate", "masters", "master's", "master ", "postgraduate",
            "mphil", "mres", "msc by research", "phd", "doctorate", "本科", "硕士", "博士",
        ])
    if key_set & {"target_countries", "target_country_or_region", "destination_country"}:
        return prompt_has_any(p, [
            " uk ", "united kingdom", "england", "scotland", "wales", "united states", " usa ",
            "singapore", "canada", "australia", "hong kong", "europe", "英国", "美国", "新加坡",
            "加拿大", "澳大利亚", "澳洲", "香港", "欧洲",
        ]) or p.startswith(("uk ", "usa ")) or p.endswith((" uk", " usa")) or bool(re.search(
            r"\b(?:cambridge|oxford|imperial|ucl|ntu|nus)\b.{0,140}"
            r"\b(?:cambridge|oxford|imperial|ucl|ntu|nus)\b",
            p,
        ))
    if key_set & {
        "research_interests", "research_interest", "research_topic", "proposed_research_topic",
    }:
        return bool(
            re.search(
                r"\b(?:research interests?|research topics?|proposed (?:research )?topic|research focus)"
                r"\s*(?::|is|are|include|includes)?\s+[a-z0-9]",
                p,
            )
            or re.search(
                r"\b(?:supervisors?|faculty).{0,50}\b(?:in|working on|focused on|speciali[sz](?:e|ing) in)\s+"
                r"[a-z0-9]",
                p,
            )
            or re.search(
                r"\b(?:supervisor (?:fit|match)|research fit).{0,20}\b(?:for|in|on)\s+"
                r"(?!(?:my research|this (?:programme|program)|the (?:programme|program))\b)[a-z0-9]",
                p,
            )
            or re.search(r"(?:研究兴趣|研究方向|研究主题|拟研究课题)\s*(?:是|为|：|:)?\s*[\u4e00-\u9fffA-Za-z0-9]", p)
            or re.search(r"\b(?:my )?(?:confirmed|stated) (?:research )?interests?\s+in\s+[a-z0-9]", p)
            or re.search(r"(?:筛选|匹配|查找|寻找).{0,30}(?:方向|领域)(?:的)?导师", p)
            or re.search(r"(?:方向|领域).{0,6}(?:筛选|匹配|查找|寻找)?.{0,4}导师", p)
        )
    if key_set & {"target_field", "subject_area"}:
        candidates = re.findall(
            r"\b([a-z][a-z0-9&-]{2,})\s+(?:programmes?|programs?|mres|mphil|masters?)\b"
            r"|\b(?:programmes?|programs?)\s+(?:in|for)\s+([a-z][a-z0-9&-]{2,})\b"
            r"|\b(?:fit|supervisors?)\s+(?:in|for)\s+([a-z][a-z0-9&-]{2,})\b",
            p,
        )
        generic = {
            "a", "an", "and", "or", "the", "my", "find", "list", "master", "masters",
            "research", "official", "suitable", "university", "graduate",
        }
        named_field = any(
            candidate.casefold() not in generic
            for pair in candidates
            for candidate in pair
            if candidate
        )
        return bool(
            named_field
            or re.search(
                r"\b(?:biological sciences?|life sciences?|biomedical sciences?|computer sciences?|"
                r"cognitive neuroscience|neuroscience|biochemistry|biology|engineering|medicine|law)\b",
                p,
            )
            or re.search(r"(?:项目|专业|方向).{0,6}(?:生物|神经|工程|计算机|医学|法律|商科)", p)
            or re.search(r"(?:生物|神经|工程|计算机|医学|法律|商科).{0,8}(?:项目|专业|硕士)", p)
        )
    if key_set & {"target_intake", "intake_term", "application_cycle", "intended_intake"}:
        return bool(re.search(r"\b20\d{2}(?:[-/]\d{2,4})?\b", p)) or prompt_has_any(p, [
            "current cycle", "current application cycle", "fall entry", "spring entry", "autumn entry",
            "september entry", "january entry", "本申请季", "当前申请季", "今年入学", "秋季入学", "春季入学",
        ])
    if key_set & {
        "program_name", "program_name_or_url", "program_names_or_urls", "target_programs",
        "institution", "institution_name", "target_institution", "target_university",
    }:
        named_programme = bool(re.search(
            r"\b(?:university\s+of|[a-z][a-z&.'-]*\s+university|[a-z][a-z&.'-]*\s+college|"
            r"[a-z][a-z&.'-]*\s+institute)\s+[a-z0-9&.' -]{1,80}"
            r"\b(?:msc|mres|mphil|ma|meng|bsc|ba|phd|doctorate|masters?|bachelors?)\b",
            p,
        ))
        named_institution = bool(
            re.search(
                r"\b(?:university\s+of\s+[a-z][a-z&.' -]{1,60}|"
                r"[a-z][a-z&.' -]{1,60}\s+(?:university|college|institute))\b",
                p,
            )
            or re.search(r"[\u4e00-\u9fff]{2,20}(?:大学|学院|研究所)", p)
        )
        chinese_named_programme = bool(
            named_institution
            and (
                re.search(r"(?:本科|学士|硕士|研究生|博士).{0,10}(?:项目|专业|课程)", p)
                or re.search(r"(?:项目|专业|课程).{0,10}(?:本科|学士|硕士|研究生|博士)", p)
            )
        )
        named_award = bool(re.search(
            r"\b(?:msc(?:\s+by\s+research)?|mres|mphil|ma|meng|bsc|ba|phd|doctorate|masters?|bachelors?)\b",
            p,
        ))
        named_alias = bool(re.search(
            r"\b(?:cambridge|oxford|imperial|ucl|ntu|nus)(?:'s)?\b",
            p,
        ))
        return bool(re.search(r"https://\S+", p)) or named_programme or chinese_named_programme or (
            named_award and (named_institution or named_alias)
        ) or (
            named_institution
            and bool(key_set & {"institution", "institution_name", "target_institution", "target_university"})
        ) or prompt_has_any(p, [
            "this programme", "this program", "the named programme", "the named program",
            "programme:", "program:", "course:", "institution:", "university:",
            "这个项目", "该项目", "上述项目", "这个专业", "该专业",
            "项目是", "项目名称", "专业是", "专业名称", "学校是", "学校名称", "院校是", "院校名称",
        ])
    if key_set & {"prompt", "essay_prompt"}:
        return prompt_has_any(p, ["prompt:", "essay question", "the prompt is", "题目是", "文书题目为", "问题是"])
    if key_set & {"word_limit", "character_limit"}:
        return bool(re.search(
            r"\b\d{1,3}(?:,\d{3})*\s*[-–—]?\s*(?:words?|characters?|字|词)\b"
            r"|\b\d{2,5}\s*[-–—]?\s*(?:words?|characters?|字|词)\b",
            p,
        ))
    if key_set & {"audience"}:
        return prompt_has_any(p, ["admissions committee", "selection committee", "scholarship panel", "招生委员会", "评审委员会"])
    if key_set & {"intended_use", "submission_use"}:
        return prompt_has_any(p, ["for submission", "for my application", "scholarship application", "用于申请", "用于提交", "奖学金申请"]) or bool(
            re.search(r"\bfor my\b.{0,120}\bapplication\b|\bapplication\b.{0,80}\b(?:paragraph|statement|essay)\b", p)
        )
    if key_set & {"output_location", "output_path"}:
        return bool(re.search(r"(?:^|\s)(?:/[^\s]+|[^\s]+\.docx)\b", p)) or prompt_has_any(p, [
            "in chat", "in the chat", "对话框里", "保存到", "输出到",
        ])
    if key_set & {"overwrite_existing", "overwrite_decision"}:
        return prompt_has_any(p, ["overwrite", "do not overwrite", "new file", "覆盖原文件", "不要覆盖", "另存为", "新文件"])
    if key_set & {"applicant_background", "academic_background", "current_qualification"}:
        return prompt_has_any(p, [
            "my cv", "my background", "attached cv", "attached resume", "explicitly confirm",
            "confirmed applicant fact", "我的简历", "我的背景", "已上传简历", "我明确确认",
        ]) or bool(re.search(r"\bmy(?:\s+[a-z-]+){0,2}\s+(?:cv|resume)\b", p))
    if key_set & {"document_inventory", "application_materials", "documents"}:
        return prompt_has_any(p, ["attached documents", "attached files", "i currently have", "my current documents", "已上传材料", "我现有的材料", "已有材料包括"])
    return False


def profile_gaps(setup: dict[str, Any], route: str | None = None, prompt: str = "") -> list[str]:
    if route is None or route == "programme_table_cleaning":
        return []
    fields_by_route: dict[str, list[tuple[tuple[str, ...], str]]] = {
        "program_research": [
            (("target_degree_level", "degree_level"), "target degree level"),
            (("target_countries", "target_country_or_region"), "destination country or region"),
            (("target_field", "subject_area"), "target field"),
            (("target_intake", "intake_term"), "target intake"),
        ],
        "requirement_audit": [
            (("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"), "named programme or official URL"),
            (("target_intake", "intake_term", "application_cycle"), "application cycle or target intake"),
        ],
        "materials_check": [
            (("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"), "named programme or official URL"),
            (("target_intake", "intake_term", "application_cycle"), "application cycle or target intake"),
            (("document_inventory", "application_materials", "documents"), "current application-material inventory"),
        ],
        "application_writing_studio": [
            (("program_name", "program_name_or_url", "target_programs"), "target programme"),
            (("prompt", "essay_prompt"), "application writing prompt"),
            (("word_limit", "character_limit"), "word or character limit"),
            (("audience",), "intended audience"),
            (("intended_use", "submission_use"), "intended use"),
            (("applicant_background", "academic_background", "current_qualification"), "applicant evidence or background"),
            (("output_location", "output_path"), "output location"),
            (("overwrite_existing", "overwrite_decision"), "overwrite decision"),
        ],
        "submission_readiness": [
            (("program_name_or_url", "program_names_or_urls", "target_programs", "program_name"), "named programme or official URL"),
            (("target_intake", "intake_term", "application_cycle"), "application cycle or target intake"),
            (("document_inventory", "application_materials", "documents"), "current document and portal status"),
        ],
        "visa_readiness": [
            (("citizenship_countries", "citizenship"), "citizenship"),
            (("target_countries", "destination_country", "target_country_or_region"), "destination country or region"),
            (("visa_application_country",), "visa application location"),
            (("target_intake", "intake_term", "intended_intake"), "target intake"),
            (("budget_annual", "funding_plan", "budget"), "funding basis"),
        ],
    }
    fields = fields_by_route.get(route, [])
    workflow_mode = str(setup.get("workflow_mode") or setup.get("task_type") or "").strip()
    if route == "program_research" and workflow_mode in {"quick_triage", "exact_program_selection"}:
        fields = [item for item in fields if item[1] != "target intake"]
    if route == "program_research" and supervisor_fit_requested(prompt, setup):
        fields = [
            (
                (
                    "program_name_or_url", "program_names_or_urls", "target_programs", "program_name",
                    "institution", "institution_name", "target_institution", "target_university",
                ),
                "named programme or institution",
            ),
            (
                (
                    "research_interests", "research_interest", "research_topic", "proposed_research_topic",
                    "target_field", "subject_area",
                ),
                "confirmed research interests or proposed topic",
            ),
        ]
        if supervisor_contact_requirement_requested(prompt, setup):
            fields.append(
                (("target_intake", "intake_term", "application_cycle"), "application cycle or target intake")
            )
    p = normalize_prompt(prompt)
    if route in {"program_research", "requirement_audit"} and prompt_has_any(p, [
        "am i eligible", "compare my profile", "eligibility", "我是否符合", "比较我的背景", "录取资格",
    ]):
        fields = [
            *fields,
            (("gpa_value", "academic_background", "current_qualification"), "academic result or qualification"),
            (("language_status",), "language-test status"),
        ]
    return [
        label
        for keys, label in fields
        if not setup_value(setup, *keys) and not prompt_supplies_input(prompt, keys)
    ]


def build_plan(prompt: str, setup: dict[str, Any] | None = None) -> dict[str, Any]:
    setup = setup or {}
    route = detect_route(prompt, setup)
    disposition = route_status(prompt, route)
    source_policy = setup.get("source_policy") or "official_only"
    review_targets = ["application_route"] if route is None else ["profile_gaps"]
    if route == "application_writing_studio":
        review_targets.append("writing_brief_and_evidence")
    elif route is not None:
        review_targets.append("route_specific_follow_up")
    return {
        "status": "preliminary",
        "route_status": disposition,
        "route": route,
        "route_label": ROUTE_LABELS.get(route) if route else None,
        "actions": ROUTE_ACTIONS.get(route, []),
        "proposed_outputs": ROUTE_OUTPUTS.get(route, []),
        "human_review_required": True,
        "human_review_targets": review_targets,
        "source_policy": source_policy,
        "profile_gaps": profile_gaps(setup, route, prompt),
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
        ("检查这个项目都需要什么文书", "requirement_audit"),
        ("这个项目需要哪些申请材料", "requirement_audit"),
        ("这个项目要求哪些文书", "requirement_audit"),
        ("Do I need to contact a supervisor before applying?", "requirement_audit"),
        ("文书的完整要求", "requirement_audit"),
        ("修改个人陈述", "application_writing_studio"),
        ("Write my SOP", "application_writing_studio"),
        ("帮我写SOP", "application_writing_studio"),
        ("核对这个项目的入学要求", "requirement_audit"),
        ("检查我的申请材料是否齐全", "materials_check"),
        ("提交前做最终检查", "submission_readiness"),
        ("维护并清理项目目录表", "programme_table_cleaning"),
        ("Buscar programas universitarios oficiales", "program_research"),
        ("Find supervisors and research programme fit", "program_research"),
        ("Which supervisor best fits my research?", "program_research"),
        ("帮我筛选导师", "program_research"),
    ]
    for prompt, expected in cases:
        got = detect_route(prompt)
        assert got == expected, (prompt, got, expected)
        assert build_plan(prompt)["route_status"] == "matched"
    out_of_scope = build_plan("备份并美化Word排版")
    assert out_of_scope["route_status"] == "out_of_scope" and out_of_scope["route"] is None
    unresolved = build_plan("帮我处理一下这个任务")
    assert unresolved["route_status"] == "needs_confirmation" and unresolved["route"] is None
    setup = {"workflow_mode": "essay_sop", "profile": {"target_degree_level": "masters"}}
    assert build_plan("", setup)["route"] == "application_writing_studio"
    assert build_plan("chance probability safe school")["probability_prediction"] == "prohibited"
    assert build_plan("帮我规划个人陈述")["output_language"] == "English"
    assert build_plan("帮我规划个人陈述，请用中文回答")["output_language"] == "Chinese"
    assert build_plan("", {"requested_output_language": "Chinese"})["output_language"] == "Chinese"
    research = build_plan("find me biosciences programmes", {"profile": {"target_degree_level": "TBD"}})
    assert "target degree level" in research["profile_gaps"]
    requirement_gaps = build_plan("check this programme's requirements", {"program_name": "Example MSc"})["profile_gaps"]
    assert "academic result" not in " ".join(requirement_gaps)
    assert "language-test status" not in requirement_gaps
    visa_gaps = build_plan("student visa route for UK")["profile_gaps"]
    assert "citizenship" in visa_gaps and "academic result" not in visa_gaps
    explicit_research = build_plan("Find 2027 MRes neuroscience programmes in the UK")
    for gap in ("target degree level", "destination country or region", "target field", "target intake"):
        assert gap not in explicit_research["profile_gaps"], explicit_research
    generic_research = build_plan("Find masters programmes in the UK")
    assert "target field" in generic_research["profile_gaps"]
    complete_research_profile = {
        "profile": {
            "target_degree_level": "masters",
            "target_countries": ["UK"],
            "target_field": "neuroscience",
        }
    }
    assert build_plan("", {**complete_research_profile, "workflow_mode": "quick_triage"})["profile_gaps"] == []
    assert build_plan("", {**complete_research_profile, "workflow_mode": "exact_program_selection"})["profile_gaps"] == []
    named_requirement = build_plan("Check the University of Oxford MSc Neuroscience requirements for 2026-27")
    assert "named programme or official URL" not in named_requirement["profile_gaps"]
    chinese_named_requirement = build_plan("检查牛津大学神经科学硕士项目要求")
    assert chinese_named_requirement["route"] == "requirement_audit"
    assert chinese_named_requirement["profile_gaps"] == ["application cycle or target intake"]
    supervisor_gaps = build_plan("帮我筛选导师")
    assert supervisor_gaps["profile_gaps"] == [
        "named programme or institution",
        "confirmed research interests or proposed topic",
    ]
    named_topic_supervisor = build_plan("帮我筛选牛津大学计算神经科学方向的导师")
    assert named_topic_supervisor["profile_gaps"] == []
    supplied_supervisor = build_plan(
        "帮我筛选牛津大学导师，我的研究方向是计算神经科学",
        {"supervisor_fit_scope": "fit + evidence", "application_cycle": "2026-27"},
    )
    assert supplied_supervisor["profile_gaps"] == []
    contact_supervisor = build_plan(
        "帮我筛选牛津大学导师，我的研究方向是计算神经科学",
        {"supervisor_fit_scope": "contact requirement only"},
    )
    assert contact_supervisor["profile_gaps"] == ["application cycle or target intake"]
    writing_gaps = build_plan("Write my SOP") ["profile_gaps"]
    for gap in ("intended audience", "intended use", "output location", "overwrite decision"):
        assert gap in writing_gaps

    sop_portal_prompt = (
        "Draft a 1,000-word statement of purpose for my 2027-28 application to the University of "
        "Cambridge MPhil in Biological Science (Biochemistry) by thesis. It will be submitted in the "
        "admissions portal. I have not yet given you my academic experiences or the exact official prompt."
    )
    sop_portal = build_plan(sop_portal_prompt)
    assert sop_portal["route"] == "application_writing_studio"
    assert "target programme" not in sop_portal["profile_gaps"]
    assert "word or character limit" not in sop_portal["profile_gaps"]
    assert "intended use" not in sop_portal["profile_gaps"]
    assert "application writing prompt" in sop_portal["profile_gaps"]
    assert "applicant evidence or background" in sop_portal["profile_gaps"]

    materials_prompt = (
        "I am applying to UCL's Cognitive Neuroscience MRes for 2027 entry. I currently have a transcript "
        "and CV, my referee has agreed to write, but I do not yet have an IELTS result or personal statement. "
        "Check whether my application materials are ready to submit."
    )
    materials_plan = build_plan(materials_prompt)
    assert materials_plan["route"] == "materials_check"
    assert materials_plan["profile_gaps"] == []

    institution_list_prompt = (
        "请用中文列出 Cambridge、Oxford、Imperial、UCL、NTU 和 NUS 在 2027-28 入学周期中与 Biological "
        "Sciences 相关的 Research 类型 Master 项目。只包括 MPhil、MRes、MSc by Research 或明确以 thesis "
        "为主的同等学位，使用当前官方来源。"
    )
    institution_list = build_plan(institution_list_prompt)
    assert institution_list["route"] == "program_research"
    assert institution_list["profile_gaps"] == []
    assert institution_list["output_language"] == "Chinese"

    supervisor_prompt = (
        "For the University of Cambridge MPhil in Biological Science (Biochemistry) by thesis for 2027-28, "
        "identify potential supervisors and compare their current research and representative publications "
        "with my confirmed interest in enhancer regulation and single-cell genomics. Also verify whether "
        "supervisor contact is required before applying."
    )
    supervisor_plan = build_plan(supervisor_prompt)
    assert supervisor_plan["route"] == "program_research"
    assert supervisor_plan["profile_gaps"] == []
    assert "supervisor_contact_status" in supervisor_plan["actions"]
    assert "supervisor_research_and_publication_fit" in supervisor_plan["actions"]
    assert detect_route("Find a supervisor before applying: is this required?") == "requirement_audit"

    confirmed_fact_prompt = (
        "Draft a programme-fit paragraph for my 2027-28 Cambridge MPhil in Biological Science (Biochemistry) "
        "application. My local CV says I completed an eight-week CRISPR screen placement, and I explicitly "
        "confirm that this is accurate. Use only that confirmed applicant fact plus verified official programme facts."
    )
    confirmed_fact_plan = build_plan(confirmed_fact_prompt)
    assert confirmed_fact_plan["route"] == "application_writing_studio"
    for supplied_gap in ("target programme", "intended use", "applicant evidence or background"):
        assert supplied_gap not in confirmed_fact_plan["profile_gaps"]

    direct_requirement_prompt = (
        "For the University of Oxford MSc by Research in Biochemistry, 2027-28 entry, tell me exactly which "
        "application documents I must submit, the statement prompt and word limit, reference requirements, "
        "application fee, deadline, and whether I must contact a supervisor before applying. Use current "
        "official sources. Explain it directly, not as a checklist."
    )
    direct_requirement = build_plan(direct_requirement_prompt)
    assert direct_requirement["route"] == "requirement_audit"
    assert direct_requirement["profile_gaps"] == []

    natural_word_prompt = (
        "Please back up my Word document, improve the typography, fix the spacing, and make it look more "
        "polished. It is not an admissions document."
    )
    natural_word = build_plan(natural_word_prompt)
    assert natural_word["route_status"] == "out_of_scope" and natural_word["route"] is None


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
