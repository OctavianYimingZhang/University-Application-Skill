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

    programs = first_nonempty_rows(data.get("programs"), ontology.get("programs"))
    sources = row_list(data.get("sources")) + ontology_rows(ontology, "source_evidence")
    submission_tasks = first_nonempty_rows(data.get("submission_tasks"), ontology.get("tasks"))

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

    sheets.append(("School Shortlist", make_table("School Shortlist", note, SCHOOL_COLUMNS, row_list(data.get("school_shortlist")))))
    sheets.append(("Program Comparison", make_table("Program Comparison", note, PROGRAM_COLUMNS, programs)))
    sheets.append(("Requirements Matrix", make_table("Requirements Matrix", note, REQUIREMENT_COLUMNS, row_list(data.get("requirements")))))
    sheets.append(("Essay Plan", make_table("Essay Plan", note, ESSAY_COLUMNS, row_list(data.get("essay_plan")))))
    sheets.append(("Submission Checklist", make_table("Submission Checklist", note, SUBMISSION_COLUMNS, submission_tasks)))
    sheets.append(("Source Log", make_table("Source Log", note, SOURCE_COLUMNS, sources)))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for program in programs:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a study-abroad admissions workbook from JSON.")
    parser.add_argument("input_json", type=Path, help="Path to structured admissions JSON.")
    parser.add_argument("output_xlsx", type=Path, help="Path for the generated .xlsx workbook.")
    args = parser.parse_args(argv)

    data = load_json(args.input_json)
    sheets = build_sheets(data)
    write_xlsx(sheets, args.output_xlsx)
    print(f"Wrote {args.output_xlsx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
