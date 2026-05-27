#!/usr/bin/env python3
"""Build an admissions planning workbook from structured JSON.

This script intentionally uses only the Python standard library so the skill can
run in constrained Codex environments without package installation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from xml.sax.saxutils import escape

from validate_ontology import build_indexes, check_lineage_refs, check_quality, check_refs, summarize


PROFILE_KEYS = [
    "applicant_id",
    "student_name",
    "degree_level",
    "target_intake",
    "citizenship_countries",
    "residence_country",
    "education_country",
    "passport_country",
    "visa_application_country",
    "document_language",
    "funding_source_country",
    "prior_residence_history",
    "current_country",
    "current_institution",
    "current_major",
    "gpa",
    "gpa_scale",
    "budget",
    "target_countries",
    "target_field",
    "ranking_constraints",
    "career_or_research_goal",
    "risk_tolerance",
    "language_scores",
    "tests",
    "fixed_constraints",
    "flexible_preferences",
    "missing_facts",
]

APPLICANT_COLUMNS = [
    ("applicant_id", "Applicant ID"),
    ("legal_name_passport", "Legal Name on Passport"),
    ("preferred_name", "Preferred Name"),
    ("date_of_birth", "Date of Birth"),
    ("citizenship_countries", "Citizenship Countries"),
    ("residence_country", "Residence Country"),
    ("education_country", "Education Country"),
    ("passport_country", "Passport Country"),
    ("dual_citizenship", "Dual Citizenship"),
    ("visa_application_country", "Visa Application Country"),
    ("document_language", "Document Language"),
    ("funding_source_country", "Funding Source Country"),
    ("prior_residence_history", "Prior Residence History"),
    ("target_degree_level", "Target Degree Level"),
    ("target_intake", "Target Intake"),
    ("target_countries", "Target Countries"),
    ("budget_total", "Budget Total"),
    ("budget_annual", "Budget Annual"),
    ("career_or_research_goal", "Career / Research Goal"),
    ("risk_tolerance", "Risk Tolerance"),
    ("data_completeness_status", "Data Completeness Status"),
    ("notes", "Notes"),
]

CREDENTIAL_COLUMNS = [
    ("credential_id", "Credential ID"),
    ("applicant_id", "Applicant ID"),
    ("country", "Country"),
    ("institution", "Institution"),
    ("qualification_type", "Qualification Type"),
    ("major", "Major"),
    ("start_date", "Start Date"),
    ("end_date", "End Date"),
    ("expected_graduation_date", "Expected Graduation Date"),
    ("gpa_value", "GPA Value"),
    ("gpa_scale", "GPA Scale"),
    ("class_rank", "Class Rank"),
    ("grading_evidence_document_id", "Grading Evidence Document ID"),
    ("language_of_instruction", "Language of Instruction"),
    ("status", "Status"),
    ("notes", "Notes"),
]

INSTITUTION_COLUMNS = [
    ("institution_id", "Institution ID"),
    ("name_official", "Official Name"),
    ("country", "Country"),
    ("city", "City"),
    ("campus_list", "Campus List"),
    ("institution_type", "Institution Type"),
    ("application_systems", "Application Systems"),
    ("visa_sponsor_status", "Visa Sponsor Status"),
    ("dli_number", "DLI Number"),
    ("recognised_sponsor_status", "Recognised Sponsor Status"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("notes", "Notes"),
]

PROGRAM_OBJECT_COLUMNS = [
    ("program_id", "Program ID"),
    ("institution_id", "Institution ID"),
    ("official_name", "Official Program Name"),
    ("award", "Award"),
    ("degree_level", "Degree Level"),
    ("subject_area", "Subject Area"),
    ("campus", "Campus"),
    ("duration", "Duration"),
    ("mode", "Mode"),
    ("intake_terms", "Intake Terms"),
    ("application_route", "Application Route"),
    ("tuition_fee", "Tuition Fee"),
    ("deadline_set_id", "Deadline Set ID"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("verification_status", "Verification Status"),
    ("notes", "Notes"),
]

APPLICATION_CASE_COLUMNS = [
    ("application_case_id", "Application Case ID"),
    ("applicant_id", "Applicant ID"),
    ("program_id", "Program ID"),
    ("institution_id", "Institution ID"),
    ("school", "School"),
    ("program", "Program"),
    ("cycle", "Cycle"),
    ("intake", "Intake"),
    ("route", "Route"),
    ("status", "Status"),
    ("fit_category", "Fit Category"),
    ("academic_fit", "Academic Fit"),
    ("budget_fit", "Budget Fit"),
    ("timing_fit", "Timing Fit"),
    ("visa_work_fit", "Visa / Work Fit"),
    ("risk_summary", "Risk Summary"),
    ("last_verified_at", "Last Verified At"),
    ("blocking_tasks", "Blocking Tasks"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("notes", "Notes"),
]

SCHOOL_COLUMNS = [
    ("application_case_id", "Application Case ID"),
    ("institution_id", "Institution ID"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("country", "Country"),
    ("region", "Region"),
    ("school", "School"),
    ("city", "City"),
    ("campus", "Campus"),
    ("ranking_range", "Ranking / Range"),
    ("school_rank", "School Rank"),
    ("subject_rank", "Subject Rank"),
    ("degree_level", "Degree Level"),
    ("fit_category", "Fit Category"),
    ("fit_score", "Fit Score"),
    ("academic_fit", "Academic Fit"),
    ("budget_fit", "Budget Fit"),
    ("location_fit", "Location Fit"),
    ("career_research_fit", "Career / Research Fit"),
    ("visa_work_notes", "Visa / Work Notes"),
    ("scholarship_notes", "Scholarship Notes"),
    ("rationale", "Rationale"),
    ("official_source", "Official Source"),
    ("check_date", "Check Date"),
    ("notes", "Notes / Needs Check"),
]

PROGRAM_COLUMNS = [
    ("program_id", "Program ID"),
    ("institution_id", "Institution ID"),
    ("application_case_id", "Application Case ID"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("region", "Region"),
    ("country", "Country"),
    ("school", "School"),
    ("ranking_range", "Ranking / School Range"),
    ("program", "Program"),
    ("award", "Award"),
    ("program_type", "Program Type"),
    ("direction_group", "Direction Group"),
    ("relevance", "Direction / Relevance"),
    ("application_status", "Application Status / Feasibility"),
    ("fit_risk", "Fit / Risk"),
    ("zero_background_risk", "Zero-Background / Switch Risk"),
    ("coursework_training", "Program Introduction + Curriculum / Training"),
    ("entry_requirements", "Entry Requirements"),
    ("language_requirements", "Language Requirements"),
    ("duration_mode", "Duration / Mode"),
    ("application_time_status", "Application Time / Status"),
    ("fees_funding", "Fees / Funding / Important Info"),
    ("applicant_judgement", "Applicant Judgement Points"),
    ("same_school_program_count", "Same-School Program Count"),
    ("cross_table_direction_reference", "Cross-Table Direction Reference"),
    ("application_system", "Application System"),
    ("official_source", "Official Source"),
    ("check_date", "Check Date"),
    ("notes", "Notes / Needs Check"),
]

REQUIREMENT_RULE_COLUMNS = [
    ("requirement_rule_id", "Requirement Rule ID"),
    ("application_case_id", "Application Case ID"),
    ("program_id", "Program ID"),
    ("jurisdiction", "Jurisdiction"),
    ("rule_category", "Rule Category"),
    ("applies_when", "Applies When"),
    ("requirement_text", "Requirement Text"),
    ("required_document_type", "Required Document Type"),
    ("source_evidence_id", "Source Evidence ID"),
    ("checked_at", "Checked At"),
    ("valid_from", "Valid From"),
    ("valid_until", "Valid Until"),
    ("stale_after_days", "Stale After Days"),
    ("verification_status", "Verification Status"),
    ("notes", "Notes"),
]

REQUIREMENT_COLUMNS = [
    ("requirement_rule_id", "Requirement Rule ID"),
    ("application_case_id", "Application Case ID"),
    ("source_evidence_id", "Source Evidence ID"),
    ("program_id", "Program ID"),
    ("school", "School"),
    ("program", "Program"),
    ("transcript", "Transcript"),
    ("degree_certificate", "Degree / Enrollment Certificate"),
    ("gpa_requirement", "GPA / Class Requirement"),
    ("language_test", "Language Test"),
    ("language_minimum", "Language Minimum"),
    ("references", "References"),
    ("cv_resume", "CV / Resume"),
    ("essay_sop", "Essay / SOP"),
    ("portfolio", "Portfolio / Sample Work"),
    ("test_scores", "Other Tests"),
    ("application_fee", "Application Fee"),
    ("deadline", "Deadline"),
    ("application_system", "Application System"),
    ("source", "Source"),
    ("check_date", "Check Date"),
    ("notes", "Notes / Needs Check"),
]

DOCUMENT_COLUMNS = [
    ("document_id", "Document ID"),
    ("applicant_id", "Applicant ID"),
    ("application_case_id", "Application Case ID"),
    ("document_type", "Document Type"),
    ("issuing_country", "Issuing Country"),
    ("language", "Language"),
    ("translation_required", "Translation Required"),
    ("legalisation_required", "Legalisation Required"),
    ("version", "Version"),
    ("status", "Status"),
    ("expiry_date", "Expiry Date"),
    ("linked_requirement_ids", "Linked Requirement IDs"),
    ("file_name", "File Name"),
    ("notes", "Notes"),
]

ESSAY_COLUMNS = [
    ("school", "School"),
    ("program", "Program"),
    ("essay_type", "Essay Type"),
    ("prompt", "Prompt"),
    ("word_limit", "Word Limit"),
    ("evidence_needed", "Evidence Needed"),
    ("program_specific_angle", "Program-Specific Angle"),
    ("academic_depth_notes", "Academic Depth Notes"),
    ("status", "Status"),
    ("source", "Source"),
    ("notes", "Notes"),
]

SUBMISSION_COLUMNS = [
    ("task_id", "Task ID"),
    ("application_case_id", "Application Case ID"),
    ("blocking_requirement_ids", "Blocking Requirement IDs"),
    ("school", "School"),
    ("program", "Program"),
    ("system", "System / Portal"),
    ("account", "Account"),
    ("task", "Task"),
    ("owner", "Owner"),
    ("deadline", "Deadline"),
    ("status", "Status"),
    ("source", "Source"),
    ("notes", "Notes"),
]

TASK_COLUMNS = [
    ("task_id", "Task ID"),
    ("application_case_id", "Application Case ID"),
    ("task_type", "Task Type"),
    ("owner", "Owner"),
    ("due_at", "Due At"),
    ("timezone", "Timezone"),
    ("status", "Status"),
    ("blocking_requirement_ids", "Blocking Requirement IDs"),
    ("evidence_required", "Evidence Required"),
    ("source_evidence_id", "Source Evidence ID"),
    ("notes", "Notes"),
]

RISK_COLUMNS = [
    ("risk_id", "Risk ID"),
    ("application_case_id", "Application Case ID"),
    ("category", "Category"),
    ("severity", "Severity"),
    ("rationale", "Rationale"),
    ("evidence_id", "Evidence ID"),
    ("status", "Status"),
    ("notes", "Notes"),
]

DEADLINE_COLUMNS = [
    ("deadline_id", "Deadline ID"),
    ("application_case_id", "Application Case ID"),
    ("deadline_type", "Deadline Type"),
    ("due_at", "Due At"),
    ("timezone", "Timezone"),
    ("source_evidence_id", "Source Evidence ID"),
    ("verification_status", "Verification Status"),
    ("notes", "Notes"),
]

OFFER_COLUMNS = [
    ("offer_id", "Offer ID"),
    ("application_case_id", "Application Case ID"),
    ("decision", "Decision"),
    ("conditions", "Conditions"),
    ("deposit_due_at", "Deposit Due At"),
    ("post_offer_document_type", "Post-Offer Document Type"),
    ("source_evidence_id", "Source Evidence ID"),
    ("notes", "Notes"),
]

VISA_COLUMNS = [
    ("visa_case_id", "Visa Case ID"),
    ("application_case_id", "Application Case ID"),
    ("destination_country", "Destination Country"),
    ("visa_or_permit_type", "Visa / Permit Type"),
    ("route_status", "Route Status"),
    ("post_offer_document_id", "Post-Offer Document ID"),
    ("required_document_ids", "Required Document IDs"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("notes", "Notes"),
]

SOURCE_COLUMNS = [
    ("source_evidence_id", "Source Evidence ID"),
    ("source_id", "Source ID"),
    ("entity", "Entity"),
    ("title", "Title"),
    ("url", "URL"),
    ("source_type", "Source Type"),
    ("facts_supported", "Facts Supported"),
    ("checked_date", "Checked Date"),
    ("checked_at", "Checked At"),
    ("retrieved_at", "Retrieved At"),
    ("reliability", "Reliability"),
    ("stale_after_days", "Stale After Days"),
    ("verification_status", "Verification Status"),
    ("quote_or_excerpt", "Quote / Excerpt"),
    ("notes", "Notes"),
]

SOURCE_SNAPSHOT_COLUMNS = [
    ("source_snapshot_id", "Source Snapshot ID"),
    ("source_evidence_id", "Source Evidence ID"),
    ("url", "URL"),
    ("retrieved_at", "Retrieved At"),
    ("content_hash", "Content Hash"),
    ("raw_title", "Raw Title"),
    ("raw_excerpt", "Raw Excerpt"),
    ("http_status", "HTTP Status"),
    ("cycle_hint", "Cycle Hint"),
    ("snapshot_status", "Snapshot Status"),
    ("notes", "Notes"),
]

EXTRACTED_FACT_COLUMNS = [
    ("extracted_fact_id", "Extracted Fact ID"),
    ("source_snapshot_id", "Source Snapshot ID"),
    ("entity_type", "Entity Type"),
    ("entity_id", "Entity ID"),
    ("fact_text", "Fact Text"),
    ("normalized_key", "Normalized Key"),
    ("extraction_confidence", "Extraction Confidence"),
    ("extraction_method", "Extraction Method"),
    ("verification_status", "Verification Status"),
    ("notes", "Notes"),
]

FACT_VERSION_COLUMNS = [
    ("fact_version_id", "Fact Version ID"),
    ("extracted_fact_id", "Extracted Fact ID"),
    ("previous_value", "Previous Value"),
    ("current_value", "Current Value"),
    ("changed_at", "Changed At"),
    ("change_type", "Change Type"),
    ("impact_scope", "Impact Scope"),
    ("notes", "Notes"),
]

LINEAGE_EDGE_COLUMNS = [
    ("lineage_edge_id", "Lineage Edge ID"),
    ("from_object_id", "From Object ID"),
    ("from_object_type", "From Object Type"),
    ("to_object_id", "To Object ID"),
    ("to_object_type", "To Object Type"),
    ("transformation", "Transformation"),
    ("evidence_required", "Evidence Required"),
    ("notes", "Notes"),
]

QUALITY_CHECK_COLUMNS = [
    ("quality_check_id", "Quality Check ID"),
    ("check_name", "Check Name"),
    ("target_object_type", "Target Object Type"),
    ("severity", "Severity"),
    ("logic", "Logic"),
    ("on_fail", "On Fail"),
    ("status", "Status"),
    ("notes", "Notes"),
]

PIPELINE_RUN_COLUMNS = [
    ("pipeline_run_id", "Pipeline Run ID"),
    ("workflow_name", "Workflow Name"),
    ("started_at", "Started At"),
    ("finished_at", "Finished At"),
    ("input_object_ids", "Input Object IDs"),
    ("output_object_ids", "Output Object IDs"),
    ("quality_check_ids", "Quality Check IDs"),
    ("status", "Status"),
    ("notes", "Notes"),
]

ACTION_EVENT_COLUMNS = [
    ("action_event_id", "Action Event ID"),
    ("action_type", "Action Type"),
    ("actor", "Actor"),
    ("target_object_id", "Target Object ID"),
    ("before_state", "Before State"),
    ("after_state", "After State"),
    ("validation_results", "Validation Results"),
    ("source_evidence_ids", "Source Evidence IDs"),
    ("created_at", "Created At"),
    ("notes", "Notes"),
]

USER_SETUP_COLUMNS = [
    ("user_setup_id", "User Setup ID"),
    ("applicant_id", "Applicant ID"),
    ("workflow_mode", "Workflow Mode"),
    ("output_mode", "Output Mode"),
    ("recommendation_count", "Recommendation Count"),
    ("preferred_depth", "Preferred Depth"),
    ("ask_style", "Ask Style"),
    ("source_policy", "Source Policy"),
    ("privacy_mode", "Privacy Mode"),
    ("export_format", "Export Format"),
    ("created_at", "Created At"),
    ("updated_at", "Updated At"),
    ("notes", "Notes"),
]

PREFERENCE_WEIGHT_COLUMNS = [
    ("preference_weight_id", "Preference Weight ID"),
    ("user_setup_id", "User Setup ID"),
    ("ranking_weight", "Ranking Weight"),
    ("admission_safety_weight", "Admission Safety Weight"),
    ("budget_weight", "Budget Weight"),
    ("city_weight", "City Weight"),
    ("career_weight", "Career Weight"),
    ("research_fit_weight", "Research Fit Weight"),
    ("visa_work_route_weight", "Visa / Work Route Weight"),
    ("deadline_feasibility_weight", "Deadline Feasibility Weight"),
    ("notes", "Notes"),
]

INTERACTION_STATE_COLUMNS = [
    ("interaction_state_id", "Interaction State ID"),
    ("user_setup_id", "User Setup ID"),
    ("current_step", "Current Step"),
    ("completed_cards", "Completed Cards"),
    ("missing_fields", "Missing Fields"),
    ("blocker_count", "Blocker Count"),
    ("warning_count", "Warning Count"),
    ("next_recommended_action", "Next Recommended Action"),
    ("notes", "Notes"),
]

STUDENT_EVIDENCE_COLUMNS = [
    ("student_evidence_id", "Student Evidence ID"),
    ("applicant_id", "Applicant ID"),
    ("evidence_type", "Evidence Type"),
    ("description", "Description"),
    ("document_id", "Document ID"),
    ("verification_status", "Verification Status"),
    ("notes", "Notes"),
]

PROGRAM_FIT_FACT_COLUMNS = [
    ("program_fit_fact_id", "Program Fit Fact ID"),
    ("program_id", "Program ID"),
    ("fact_type", "Fact Type"),
    ("fact_text", "Fact Text"),
    ("source_evidence_id", "Source Evidence ID"),
    ("verification_status", "Verification Status"),
    ("notes", "Notes"),
]

ESSAY_CLAIM_COLUMNS = [
    ("essay_claim_id", "Essay Claim ID"),
    ("application_case_id", "Application Case ID"),
    ("claim_type", "Claim Type"),
    ("claim_text", "Claim Text"),
    ("student_evidence_ids", "Student Evidence IDs"),
    ("program_fit_fact_ids", "Program Fit Fact IDs"),
    ("status", "Status"),
    ("notes", "Notes"),
]


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(as_text(item) for item in value if as_text(item))
    if isinstance(value, dict):
        return "; ".join(f"{key}: {as_text(val)}" for key, val in value.items() if as_text(val))
    return str(value)


def value_for(row: dict[str, Any], key: str) -> str:
    if key in row:
        return as_text(row.get(key, ""))
    aliases = {
        "program": "official_name",
        "school": "name_official",
        "check_date": "checked_at",
        "checked_date": "checked_at",
        "source_id": "source_evidence_id",
        "source_evidence_id": "source_id",
    }
    alias = aliases.get(key)
    if alias:
        return as_text(row.get(alias, ""))
    return ""


def make_table(title: str, note: str, columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[list[str]]:
    table: list[list[str]] = [[title], [note], [header for _, header in columns]]
    for row in rows:
        table.append([value_for(row, key) for key, _ in columns])
    return table


def row_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def ontology_rows(ontology: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return row_list(ontology.get(key))


def first_nonempty_rows(*values: Any) -> list[dict[str, Any]]:
    for value in values:
        rows = row_list(value)
        if rows:
            return rows
    return []


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if row.get(key)}


def first_source(
    source_ids: Any,
    sources_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(source_ids, str):
        return sources_by_id.get(source_ids, {})
    if isinstance(source_ids, list):
        for source_id in source_ids:
            source = sources_by_id.get(str(source_id), {})
            if source:
                return source
    return {}


def source_text(source: dict[str, Any]) -> str:
    return as_text(source.get("url") or source.get("title") or source.get("source_evidence_id"))


def checked_text(source: dict[str, Any]) -> str:
    return as_text(source.get("checked_at") or source.get("checked_date"))


def derive_school_shortlist(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    institutions = index_by(ontology_rows(ontology, "institutions"), "institution_id")
    programs = index_by(ontology_rows(ontology, "programs"), "program_id")
    sources = index_by(ontology_rows(ontology, "source_evidence"), "source_evidence_id")
    rows_out: list[dict[str, Any]] = []
    for case in ontology_rows(ontology, "application_cases"):
        program = programs.get(str(case.get("program_id", "")), {})
        institution_id = as_text(case.get("institution_id") or program.get("institution_id"))
        institution = institutions.get(institution_id, {})
        source = first_source(
            case.get("source_evidence_ids") or program.get("source_evidence_ids") or institution.get("source_evidence_ids"),
            sources,
        )
        rows_out.append(
            {
                "application_case_id": case.get("application_case_id"),
                "institution_id": institution_id,
                "source_evidence_ids": case.get("source_evidence_ids") or program.get("source_evidence_ids") or institution.get("source_evidence_ids"),
                "country": institution.get("country"),
                "region": institution.get("country"),
                "school": case.get("school") or institution.get("name_official"),
                "city": institution.get("city"),
                "campus": program.get("campus"),
                "degree_level": program.get("degree_level"),
                "fit_category": case.get("fit_category"),
                "academic_fit": case.get("academic_fit"),
                "budget_fit": case.get("budget_fit"),
                "location_fit": case.get("location_fit"),
                "career_research_fit": case.get("career_research_fit"),
                "visa_work_notes": case.get("visa_work_fit"),
                "rationale": case.get("risk_summary"),
                "official_source": source_text(source),
                "check_date": checked_text(source),
                "notes": case.get("notes"),
            }
        )
    return rows_out


def matching_requirement_texts(requirements: list[dict[str, Any]], program_id: str, categories: set[str]) -> str:
    return as_text(
        [
            rule.get("requirement_text")
            for rule in requirements
            if str(rule.get("program_id", "")) == program_id and rule.get("rule_category") in categories
        ]
    )


def derive_program_comparison(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    institutions = index_by(ontology_rows(ontology, "institutions"), "institution_id")
    cases_by_program: dict[str, dict[str, Any]] = {}
    for case in ontology_rows(ontology, "application_cases"):
        if case.get("program_id"):
            cases_by_program[str(case["program_id"])] = case
    sources = index_by(ontology_rows(ontology, "source_evidence"), "source_evidence_id")
    requirements = ontology_rows(ontology, "requirement_rules")
    rows_out: list[dict[str, Any]] = []
    for program in ontology_rows(ontology, "programs"):
        program_id = str(program.get("program_id", ""))
        institution = institutions.get(str(program.get("institution_id", "")), {})
        case = cases_by_program.get(program_id, {})
        source = first_source(program.get("source_evidence_ids") or institution.get("source_evidence_ids"), sources)
        rows_out.append(
            {
                "program_id": program.get("program_id"),
                "institution_id": program.get("institution_id"),
                "application_case_id": case.get("application_case_id"),
                "source_evidence_ids": program.get("source_evidence_ids") or institution.get("source_evidence_ids"),
                "region": institution.get("country"),
                "country": institution.get("country"),
                "school": institution.get("name_official"),
                "program": program.get("official_name"),
                "award": program.get("award"),
                "program_type": program.get("degree_level"),
                "direction_group": program.get("subject_area"),
                "application_status": case.get("status"),
                "fit_risk": case.get("risk_summary"),
                "coursework_training": program.get("coursework_training") or program.get("notes"),
                "entry_requirements": matching_requirement_texts(requirements, program_id, {"academic", "document", "credential_evaluation"}),
                "language_requirements": matching_requirement_texts(requirements, program_id, {"language"}),
                "duration_mode": as_text([program.get("duration"), program.get("mode")]),
                "application_time_status": case.get("timing_fit"),
                "fees_funding": program.get("tuition_fee"),
                "applicant_judgement": case.get("academic_fit"),
                "application_system": case.get("route") or program.get("application_route"),
                "official_source": source_text(source),
                "check_date": checked_text(source),
                "notes": program.get("notes"),
            }
        )
    return rows_out


def derive_requirements_matrix(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    institutions = index_by(ontology_rows(ontology, "institutions"), "institution_id")
    programs = index_by(ontology_rows(ontology, "programs"), "program_id")
    cases = index_by(ontology_rows(ontology, "application_cases"), "application_case_id")
    sources = index_by(ontology_rows(ontology, "source_evidence"), "source_evidence_id")
    rows_out: list[dict[str, Any]] = []
    for rule in ontology_rows(ontology, "requirement_rules"):
        program = programs.get(str(rule.get("program_id", "")), {})
        case = cases.get(str(rule.get("application_case_id", "")), {})
        institution = institutions.get(str(case.get("institution_id") or program.get("institution_id") or ""), {})
        source = first_source(rule.get("source_evidence_id"), sources)
        text = rule.get("requirement_text")
        row = {
            "requirement_rule_id": rule.get("requirement_rule_id"),
            "application_case_id": rule.get("application_case_id"),
            "source_evidence_id": rule.get("source_evidence_id"),
            "program_id": rule.get("program_id"),
            "school": case.get("school") or institution.get("name_official"),
            "program": case.get("program") or program.get("official_name"),
            "deadline": text if rule.get("rule_category") == "deadline" else "",
            "application_system": text if rule.get("rule_category") == "application_route" else case.get("route") or program.get("application_route"),
            "source": source_text(source),
            "check_date": checked_text(source),
            "notes": rule.get("notes") or rule.get("verification_status"),
        }
        document_type = as_text(rule.get("required_document_type")).lower()
        category = as_text(rule.get("rule_category")).lower()
        if "transcript" in document_type:
            row["transcript"] = text
        elif "degree" in document_type or "enrollment" in document_type:
            row["degree_certificate"] = text
        elif "reference" in document_type or "recommendation" in document_type:
            row["references"] = text
        elif document_type in {"cv", "resume"}:
            row["cv_resume"] = text
        elif "sop" in document_type or "essay" in document_type:
            row["essay_sop"] = text
        elif "portfolio" in document_type:
            row["portfolio"] = text
        elif "test" in document_type:
            row["test_scores"] = text
        elif category == "language":
            row["language_test"] = rule.get("required_document_type")
            row["language_minimum"] = text
        elif category in {"academic", "credential_evaluation"}:
            row["gpa_requirement"] = text
        elif category == "fee":
            row["application_fee"] = text
        else:
            row["notes"] = as_text([row.get("notes"), text])
        rows_out.append(row)
    return rows_out


def derive_essay_plan(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    cases = index_by(ontology_rows(ontology, "application_cases"), "application_case_id")
    programs = index_by(ontology_rows(ontology, "programs"), "program_id")
    institutions = index_by(ontology_rows(ontology, "institutions"), "institution_id")
    evidence = index_by(ontology_rows(ontology, "student_evidence"), "student_evidence_id")
    fit_facts = index_by(ontology_rows(ontology, "program_fit_facts"), "program_fit_fact_id")
    sources = index_by(ontology_rows(ontology, "source_evidence"), "source_evidence_id")
    rows_out: list[dict[str, Any]] = []
    for claim in ontology_rows(ontology, "essay_claims"):
        case = cases.get(str(claim.get("application_case_id", "")), {})
        program = programs.get(str(case.get("program_id", "")), {})
        institution = institutions.get(str(case.get("institution_id") or program.get("institution_id") or ""), {})
        linked_evidence = [evidence.get(str(item), {}) for item in claim.get("student_evidence_ids", []) if evidence.get(str(item))]
        linked_fits = [fit_facts.get(str(item), {}) for item in claim.get("program_fit_fact_ids", []) if fit_facts.get(str(item))]
        first_fit_source = first_source([fit.get("source_evidence_id") for fit in linked_fits], sources)
        rows_out.append(
            {
                "school": case.get("school") or institution.get("name_official"),
                "program": case.get("program") or program.get("official_name"),
                "essay_type": claim.get("claim_type"),
                "evidence_needed": [item.get("description") for item in linked_evidence],
                "program_specific_angle": [item.get("fact_text") for item in linked_fits],
                "academic_depth_notes": claim.get("claim_text"),
                "status": claim.get("status"),
                "source": source_text(first_fit_source),
                "notes": claim.get("notes"),
            }
        )
    return rows_out


def derive_submission_checklist(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    cases = index_by(ontology_rows(ontology, "application_cases"), "application_case_id")
    programs = index_by(ontology_rows(ontology, "programs"), "program_id")
    institutions = index_by(ontology_rows(ontology, "institutions"), "institution_id")
    sources = index_by(ontology_rows(ontology, "source_evidence"), "source_evidence_id")
    rows_out: list[dict[str, Any]] = []
    for task in ontology_rows(ontology, "tasks"):
        case = cases.get(str(task.get("application_case_id", "")), {})
        program = programs.get(str(case.get("program_id", "")), {})
        institution = institutions.get(str(case.get("institution_id") or program.get("institution_id") or ""), {})
        source = first_source(task.get("source_evidence_id"), sources)
        rows_out.append(
            {
                "task_id": task.get("task_id"),
                "application_case_id": task.get("application_case_id"),
                "blocking_requirement_ids": task.get("blocking_requirement_ids"),
                "school": case.get("school") or institution.get("name_official"),
                "program": case.get("program") or program.get("official_name"),
                "system": case.get("route") or program.get("application_route"),
                "task": task.get("task_type"),
                "owner": task.get("owner"),
                "deadline": task.get("due_at"),
                "status": task.get("status"),
                "source": source_text(source),
                "notes": task.get("notes"),
            }
        )
    return rows_out


def profile_table(profile: dict[str, Any], title: str, note: str) -> list[list[str]]:
    rows = [[title], [note], ["Field", "Value"]]
    seen = set()
    for key in PROFILE_KEYS:
        if key in profile:
            rows.append([key.replace("_", " ").title(), as_text(profile.get(key))])
            seen.add(key)
    for key in sorted(k for k in profile if k not in seen):
        rows.append([key.replace("_", " ").title(), as_text(profile.get(key))])
    return rows


def slug_sheet_name(value: str) -> str:
    cleaned = re.sub(r"[\[\]\:\*\?\/\\]", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned) or "Sheet"
    return cleaned[:31]


def unique_sheet_name(base: str, used: set[str]) -> str:
    name = slug_sheet_name(base)
    if name not in used:
        used.add(name)
        return name
    for index in range(2, 1000):
        suffix = f" {index}"
        candidate = f"{name[:31 - len(suffix)]}{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise ValueError(f"Could not create unique sheet name for {base!r}")


def col_name(index: int) -> str:
    result = ""
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def xml_text(value: str) -> str:
    return escape(value, {"\n": "&#10;", "\r": "&#13;", "\t": "&#9;"})


def estimate_width(values: Iterable[str], header: str) -> float:
    max_len = len(header)
    for value in values:
        for part in as_text(value).splitlines() or [""]:
            max_len = max(max_len, len(part))
    return float(min(max(max_len + 2, 10), 48))


def worksheet_xml(rows: list[list[str]], freeze_header: bool = True) -> str:
    max_cols = max((len(row) for row in rows), default=1)
    col_widths: list[str] = []
    headers = rows[2] if len(rows) > 2 else []
    for col_idx in range(1, max_cols + 1):
        header = headers[col_idx - 1] if col_idx <= len(headers) else ""
        values = [row[col_idx - 1] for row in rows[3:] if col_idx <= len(row)]
        width = estimate_width(values, header)
        col_widths.append(f'<col min="{col_idx}" max="{col_idx}" width="{width:.1f}" customWidth="1"/>')

    sheet_views = ""
    if freeze_header and len(rows) >= 3:
        sheet_views = (
            "<sheetViews><sheetView workbookViewId=\"0\">"
            "<pane ySplit=\"3\" topLeftCell=\"A4\" activePane=\"bottomLeft\" state=\"frozen\"/>"
            "<selection pane=\"bottomLeft\" activeCell=\"A4\" sqref=\"A4\"/>"
            "</sheetView></sheetViews>"
        )
    else:
        sheet_views = "<sheetViews><sheetView workbookViewId=\"0\"/></sheetViews>"

    row_xml: list[str] = []
    for row_idx, row in enumerate(rows, start=1):
        height = " ht=\"34\" customHeight=\"1\"" if row_idx in (1, 2) else ""
        cells: list[str] = []
        for col_idx, value in enumerate(row, start=1):
            ref = f"{col_name(col_idx)}{row_idx}"
            style = "1" if row_idx == 1 else "2" if row_idx == 2 else "3" if row_idx == 3 else "4"
            cells.append(
                f'<c r="{ref}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{xml_text(as_text(value))}</t></is></c>'
            )
        row_xml.append(f'<row r="{row_idx}"{height}>{"".join(cells)}</row>')

    dimension = f"A1:{col_name(max_cols)}{max(len(rows), 1)}"
    auto_filter = ""
    if len(rows) >= 3 and max_cols > 1:
        auto_filter = f'<autoFilter ref="A3:{col_name(max_cols)}{max(len(rows), 3)}"/>'
    merged = ""
    if max_cols > 1:
        merged = (
            f'<mergeCells count="2"><mergeCell ref="A1:{col_name(max_cols)}1"/>'
            f'<mergeCell ref="A2:{col_name(max_cols)}2"/></mergeCells>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<dimension ref="{dimension}"/>'
        f"{sheet_views}"
        f"<cols>{''.join(col_widths)}</cols>"
        f"<sheetData>{''.join(row_xml)}</sheetData>"
        f"{auto_filter}{merged}"
        '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
        "</worksheet>"
    )


def workbook_xml(sheet_names: list[str]) -> str:
    sheets = []
    for idx, name in enumerate(sheet_names, start=1):
        sheets.append(f'<sheet name="{xml_text(name)}" sheetId="{idx}" r:id="rId{idx}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<workbookPr date1904=\"false\"/>"
        "<bookViews><workbookView xWindow=\"0\" yWindow=\"0\" windowWidth=\"22000\" windowHeight=\"12000\"/></bookViews>"
        f"<sheets>{''.join(sheets)}</sheets>"
        "</workbook>"
    )


def workbook_rels_xml(count: int) -> str:
    rels = []
    for idx in range(1, count + 1):
        rels.append(
            f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels)}</Relationships>"
    )


def content_types_xml(count: int) -> str:
    sheets = []
    for idx in range(1, count + 1):
        sheets.append(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{''.join(sheets)}</Types>"
    )


def root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="4">'
        '<font><sz val="10"/><name val="Arial"/></font>'
        '<font><b/><sz val="14"/><name val="Arial"/><color rgb="FFFFFFFF"/></font>'
        '<font><i/><sz val="10"/><name val="Arial"/><color rgb="FF374151"/></font>'
        '<font><b/><sz val="10"/><name val="Arial"/><color rgb="FFFFFFFF"/></font>'
        '</fonts>'
        '<fills count="5">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFEAF2F8"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF4F81BD"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="2">'
        '<border><left/><right/><top/><bottom/><diagonal/></border>'
        '<border><left style="thin"><color rgb="FFD9E2F3"/></left><right style="thin"><color rgb="FFD9E2F3"/></right><top style="thin"><color rgb="FFD9E2F3"/></top><bottom style="thin"><color rgb="FFD9E2F3"/></bottom><diagonal/></border>'
        '</borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="5">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="3" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )


def build_sheets(data: dict[str, Any]) -> list[tuple[str, list[list[str]]]]:
    title = as_text(data.get("workbook_title")) or "Study Abroad Application Plan"
    generated_on = as_text(data.get("generated_on")) or date.today().isoformat()
    note = (
        f"Generated on {generated_on}. Ontology objects are the source of truth; "
        "admissions facts must link to SourceEvidence; blanks mean unavailable, not assumed."
    )
    ontology = data.get("ontology") if isinstance(data.get("ontology"), dict) else {}

    applicants = ontology_rows(ontology, "applicants")
    profile = data.get("student_profile") if isinstance(data.get("student_profile"), dict) else {}
    if not profile and applicants:
        profile = applicants[0]

    school_shortlist_rows = derive_school_shortlist(ontology) or row_list(data.get("school_shortlist"))
    program_view_rows = derive_program_comparison(ontology) or row_list(data.get("programs"))
    requirements_view_rows = derive_requirements_matrix(ontology) or row_list(data.get("requirements"))
    essay_view_rows = derive_essay_plan(ontology) or row_list(data.get("essay_plan"))
    submission_view_rows = derive_submission_checklist(ontology) or row_list(data.get("submission_tasks"))
    source_evidence = ontology_rows(ontology, "source_evidence")
    sources = row_list(data.get("sources")) + source_evidence

    sheets: list[tuple[str, list[list[str]]]] = []
    sheets.append(("Profile", profile_table(profile, title, note)))

    if applicants:
        sheets.append(("Applicant Objects", make_table("Applicant Objects", note, APPLICANT_COLUMNS, applicants)))
    credentials = ontology_rows(ontology, "education_credentials")
    if credentials:
        sheets.append(("Credentials", make_table("Education Credentials", note, CREDENTIAL_COLUMNS, credentials)))
    institutions = ontology_rows(ontology, "institutions")
    if institutions:
        sheets.append(("Institution Objects", make_table("Institution Objects", note, INSTITUTION_COLUMNS, institutions)))
    if ontology_rows(ontology, "programs"):
        sheets.append(("Program Objects", make_table("Program Objects", note, PROGRAM_OBJECT_COLUMNS, ontology_rows(ontology, "programs"))))
    application_cases = ontology_rows(ontology, "application_cases")
    if application_cases:
        sheets.append(("Application Cases", make_table("Application Cases", note, APPLICATION_CASE_COLUMNS, application_cases)))
    requirement_rules = ontology_rows(ontology, "requirement_rules")
    if requirement_rules:
        sheets.append(("Requirement Rules", make_table("Requirement Rules", note, REQUIREMENT_RULE_COLUMNS, requirement_rules)))
    documents = ontology_rows(ontology, "document_artifacts")
    if documents:
        sheets.append(("Document Artifacts", make_table("Document Artifacts", note, DOCUMENT_COLUMNS, documents)))
    tasks = ontology_rows(ontology, "tasks")
    if tasks:
        sheets.append(("Tasks", make_table("Tasks", note, TASK_COLUMNS, tasks)))
    risks = ontology_rows(ontology, "risk_flags")
    if risks:
        sheets.append(("Risk Flags", make_table("Risk Flags", note, RISK_COLUMNS, risks)))
    deadlines = ontology_rows(ontology, "deadlines")
    if deadlines:
        sheets.append(("Deadlines", make_table("Deadlines", note, DEADLINE_COLUMNS, deadlines)))
    offers = ontology_rows(ontology, "offer_decisions")
    if offers:
        sheets.append(("Offer Decisions", make_table("Offer Decisions", note, OFFER_COLUMNS, offers)))
    visa_cases = ontology_rows(ontology, "visa_immigration_cases")
    if visa_cases:
        sheets.append(("Visa Cases", make_table("Visa Cases", note, VISA_COLUMNS, visa_cases)))
    if source_evidence:
        sheets.append(("Source Evidence", make_table("Source Evidence", note, SOURCE_COLUMNS, source_evidence)))
    source_snapshots = ontology_rows(ontology, "source_snapshots")
    if source_snapshots:
        sheets.append(("Source Snapshots", make_table("Source Snapshots", note, SOURCE_SNAPSHOT_COLUMNS, source_snapshots)))
    extracted_facts = ontology_rows(ontology, "extracted_facts")
    if extracted_facts:
        sheets.append(("Extracted Facts", make_table("Extracted Facts", note, EXTRACTED_FACT_COLUMNS, extracted_facts)))
    fact_versions = ontology_rows(ontology, "fact_versions")
    if fact_versions:
        sheets.append(("Fact Versions", make_table("Fact Versions", note, FACT_VERSION_COLUMNS, fact_versions)))
    lineage_edges = ontology_rows(ontology, "lineage_edges")
    if lineage_edges:
        sheets.append(("Lineage Edges", make_table("Lineage Edges", note, LINEAGE_EDGE_COLUMNS, lineage_edges)))
    quality_checks = ontology_rows(ontology, "quality_checks")
    if quality_checks:
        sheets.append(("Quality Checks", make_table("Quality Checks", note, QUALITY_CHECK_COLUMNS, quality_checks)))
    pipeline_runs = ontology_rows(ontology, "pipeline_runs")
    if pipeline_runs:
        sheets.append(("Pipeline Runs", make_table("Pipeline Runs", note, PIPELINE_RUN_COLUMNS, pipeline_runs)))
    action_events = ontology_rows(ontology, "action_events")
    if action_events:
        sheets.append(("Action Events", make_table("Action Events", note, ACTION_EVENT_COLUMNS, action_events)))
    user_setups = ontology_rows(ontology, "user_setups")
    if user_setups:
        sheets.append(("User Setup", make_table("User Setup", note, USER_SETUP_COLUMNS, user_setups)))
    preference_weights = ontology_rows(ontology, "preference_weights")
    if preference_weights:
        sheets.append(("Preference Weights", make_table("Preference Weights", note, PREFERENCE_WEIGHT_COLUMNS, preference_weights)))
    interaction_states = ontology_rows(ontology, "interaction_states")
    if interaction_states:
        sheets.append(("Interaction State", make_table("Interaction State", note, INTERACTION_STATE_COLUMNS, interaction_states)))
    student_evidence = ontology_rows(ontology, "student_evidence")
    if student_evidence:
        sheets.append(("Student Evidence", make_table("Student Evidence", note, STUDENT_EVIDENCE_COLUMNS, student_evidence)))
    program_fit_facts = ontology_rows(ontology, "program_fit_facts")
    if program_fit_facts:
        sheets.append(("Program Fit Facts", make_table("Program Fit Facts", note, PROGRAM_FIT_FACT_COLUMNS, program_fit_facts)))
    essay_claims = ontology_rows(ontology, "essay_claims")
    if essay_claims:
        sheets.append(("Essay Claims", make_table("Essay Claims", note, ESSAY_CLAIM_COLUMNS, essay_claims)))

    sheets.append(("School Shortlist", make_table("School Shortlist", note, SCHOOL_COLUMNS, school_shortlist_rows)))
    sheets.append(("Program Comparison", make_table("Program Comparison", note, PROGRAM_COLUMNS, program_view_rows)))
    sheets.append(("Requirements Matrix", make_table("Requirements Matrix", note, REQUIREMENT_COLUMNS, requirements_view_rows)))
    sheets.append(("Essay Plan", make_table("Essay Plan", note, ESSAY_COLUMNS, essay_view_rows)))
    sheets.append(("Submission Checklist", make_table("Submission Checklist", note, SUBMISSION_COLUMNS, submission_view_rows)))
    sheets.append(("Source Log", make_table("Source Log", note, SOURCE_COLUMNS, sources)))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for program in program_view_rows:
        if not isinstance(program, dict):
            continue
        key = as_text(program.get("region")) or as_text(program.get("country")) or "Programs"
        grouped.setdefault(key, []).append(program)
    for group, rows in sorted(grouped.items()):
        sheet_title = group if group.lower().endswith("programs") else f"{group} Programs"
        sheets.append((sheet_title, make_table(sheet_title, note, PROGRAM_COLUMNS, rows)))
    return sheets


def write_xlsx(sheets: list[tuple[str, list[list[str]]]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    final_sheets = [(unique_sheet_name(name, used), rows) for name, rows in sheets]
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml(len(final_sheets)))
        archive.writestr("_rels/.rels", root_rels_xml())
        archive.writestr("xl/workbook.xml", workbook_xml([name for name, _ in final_sheets]))
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(len(final_sheets)))
        archive.writestr("xl/styles.xml", styles_xml())
        for idx, (_, rows) in enumerate(final_sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{idx}.xml", worksheet_xml(rows))


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Input JSON must be an object.")
    return data


def validate_before_render(data: dict[str, Any]) -> None:
    ontology = data.get("ontology") if isinstance(data.get("ontology"), dict) else {}
    if not ontology:
        return
    report: list[dict[str, Any]] = []
    indexes = build_indexes(ontology, report)
    check_refs(ontology, indexes, report)
    check_lineage_refs(ontology, indexes, report)
    check_quality(ontology, indexes, report)
    result = summarize(report)
    if result["status"] == "failed":
        print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit("Ontology validation failed; workbook was not rendered.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a study-abroad admissions workbook from JSON.")
    parser.add_argument("input_json", type=Path, help="Path to structured admissions JSON.")
    parser.add_argument("output_xlsx", type=Path, help="Path for the generated .xlsx workbook.")
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Render a draft workbook without ontology quality gates. Do not use for final or verified outputs.",
    )
    args = parser.parse_args(argv)

    data = load_json(args.input_json)
    if not args.skip_validation:
        validate_before_render(data)
    sheets = build_sheets(data)
    write_xlsx(sheets, args.output_xlsx)
    print(f"Wrote {args.output_xlsx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
