#!/usr/bin/env python3
"""Validate study-abroad-advisor ontology JSON.

The validator is intentionally dependency-free. It checks the highest-risk
quality gates needed before a verified workbook, final shortlist, final
checklist, or state transition is treated as reliable.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from validate_setup import validate_setup_data


OBJECT_ARRAYS = {
    "Applicant": ("applicants", "applicant_id"),
    "EducationCredential": ("education_credentials", "credential_id"),
    "Institution": ("institutions", "institution_id"),
    "Program": ("programs", "program_id"),
    "ApplicationCase": ("application_cases", "application_case_id"),
    "RequirementRule": ("requirement_rules", "requirement_rule_id"),
    "DocumentArtifact": ("document_artifacts", "document_id"),
    "SourceEvidence": ("source_evidence", "source_evidence_id"),
    "SourceSnapshot": ("source_snapshots", "source_snapshot_id"),
    "ExtractedFact": ("extracted_facts", "extracted_fact_id"),
    "FactVersion": ("fact_versions", "fact_version_id"),
    "LineageEdge": ("lineage_edges", "lineage_edge_id"),
    "QualityCheck": ("quality_checks", "quality_check_id"),
    "PipelineRun": ("pipeline_runs", "pipeline_run_id"),
    "ActionEvent": ("action_events", "action_event_id"),
    "UserSetup": ("user_setups", "user_setup_id"),
    "PreferenceWeight": ("preference_weights", "preference_weight_id"),
    "InteractionState": ("interaction_states", "interaction_state_id"),
    "Task": ("tasks", "task_id"),
    "RiskFlag": ("risk_flags", "risk_id"),
    "Deadline": ("deadlines", "deadline_id"),
    "OfferDecision": ("offer_decisions", "offer_id"),
    "VisaImmigrationCase": ("visa_immigration_cases", "visa_case_id"),
    "StudentEvidence": ("student_evidence", "student_evidence_id"),
    "ProgramFitFact": ("program_fit_facts", "program_fit_fact_id"),
    "EssayClaim": ("essay_claims", "essay_claim_id"),
}

REF_FIELDS = [
    ("EducationCredential", "applicant_id", "Applicant"),
    ("Program", "institution_id", "Institution"),
    ("ApplicationCase", "applicant_id", "Applicant"),
    ("ApplicationCase", "program_id", "Program"),
    ("RequirementRule", "application_case_id", "ApplicationCase"),
    ("RequirementRule", "program_id", "Program"),
    ("RequirementRule", "source_evidence_id", "SourceEvidence"),
    ("DocumentArtifact", "applicant_id", "Applicant"),
    ("SourceSnapshot", "source_evidence_id", "SourceEvidence"),
    ("ExtractedFact", "source_snapshot_id", "SourceSnapshot"),
    ("FactVersion", "extracted_fact_id", "ExtractedFact"),
    ("Task", "application_case_id", "ApplicationCase"),
    ("RiskFlag", "application_case_id", "ApplicationCase"),
    ("RiskFlag", "evidence_id", "SourceEvidence"),
    ("Deadline", "application_case_id", "ApplicationCase"),
    ("Deadline", "source_evidence_id", "SourceEvidence"),
    ("OfferDecision", "application_case_id", "ApplicationCase"),
    ("OfferDecision", "source_evidence_id", "SourceEvidence"),
    ("VisaImmigrationCase", "application_case_id", "ApplicationCase"),
    ("UserSetup", "applicant_id", "Applicant"),
    ("PreferenceWeight", "user_setup_id", "UserSetup"),
    ("InteractionState", "user_setup_id", "UserSetup"),
    ("StudentEvidence", "applicant_id", "Applicant"),
    ("StudentEvidence", "document_id", "DocumentArtifact"),
    ("ProgramFitFact", "program_id", "Program"),
    ("ProgramFitFact", "source_evidence_id", "SourceEvidence"),
    ("EssayClaim", "application_case_id", "ApplicationCase"),
]

LIST_REF_FIELDS = [
    ("Institution", "source_evidence_ids", "SourceEvidence"),
    ("Program", "source_evidence_ids", "SourceEvidence"),
    ("ApplicationCase", "blocking_tasks", "Task"),
    ("DocumentArtifact", "linked_requirement_ids", "RequirementRule"),
    ("Task", "blocking_requirement_ids", "RequirementRule"),
    ("FactVersion", "impact_scope", "ApplicationCase"),
    ("VisaImmigrationCase", "required_document_ids", "DocumentArtifact"),
    ("VisaImmigrationCase", "source_evidence_ids", "SourceEvidence"),
    ("EssayClaim", "student_evidence_ids", "StudentEvidence"),
    ("EssayClaim", "program_fit_fact_ids", "ProgramFitFact"),
    ("PipelineRun", "quality_check_ids", "QualityCheck"),
    ("ActionEvent", "source_evidence_ids", "SourceEvidence"),
    ("ActionEvent", "validation_results", "QualityCheck"),
]

VIRTUAL_LINEAGE_TYPES = {
    "WorkbookCell",
    "ChecklistItem",
    "Recommendation",
    "SOPParagraph",
    "EssayParagraph",
    "DashboardCard",
}


def rows(ontology: dict[str, Any], object_type: str) -> list[dict[str, Any]]:
    array_name, _ = OBJECT_ARRAYS[object_type]
    value = ontology.get(array_name, [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def add(report: list[dict[str, Any]], check: str, severity: str, message: str, obj: dict[str, Any] | None = None) -> None:
    report.append(
        {
            "check": check,
            "severity": severity,
            "message": message,
            "object_id": object_id(obj) if obj else "",
        }
    )


def object_id(obj: dict[str, Any]) -> str:
    for key, value in obj.items():
        if key.endswith("_id") and isinstance(value, str):
            return value
    return ""


def load_ontology(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Top-level JSON must be an object.")
    ontology = data.get("ontology", data)
    if not isinstance(ontology, dict):
        raise SystemExit("Ontology payload must be an object.")
    return ontology


def build_indexes(ontology: dict[str, Any], report: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    for object_type, (array_name, pk) in OBJECT_ARRAYS.items():
        index: dict[str, dict[str, Any]] = {}
        raw_rows = ontology.get(array_name, [])
        if raw_rows and not isinstance(raw_rows, list):
            add(report, "array_type", "error", f"{array_name} must be an array.")
            raw_rows = []
        for idx, row in enumerate(raw_rows if isinstance(raw_rows, list) else []):
            if not isinstance(row, dict):
                add(report, "row_type", "error", f"{array_name}[{idx}] must be an object.")
                continue
            value = row.get(pk)
            if not value:
                add(report, "primary_key_required", "error", f"{object_type} is missing primary key {pk}.", row)
                continue
            value = str(value)
            if value in index:
                add(report, "primary_key_unique", "error", f"Duplicate {object_type} primary key {value}.", row)
            index[value] = row
        indexes[object_type] = index
    return indexes


def check_refs(ontology: dict[str, Any], indexes: dict[str, dict[str, dict[str, Any]]], report: list[dict[str, Any]]) -> None:
    for object_type, field, target_type in REF_FIELDS:
        for row in rows(ontology, object_type):
            value = row.get(field)
            if not value:
                continue
            if str(value) not in indexes.get(target_type, {}):
                add(report, "reference_resolves", "error", f"{object_type}.{field} references missing {target_type}: {value}.", row)
    for object_type, field, target_type in LIST_REF_FIELDS:
        for row in rows(ontology, object_type):
            values = row.get(field)
            if not values:
                continue
            if not isinstance(values, list):
                add(report, "list_reference_type", "error", f"{object_type}.{field} must be a list.", row)
                continue
            for value in values:
                if str(value) not in indexes.get(target_type, {}):
                    add(report, "reference_resolves", "error", f"{object_type}.{field} references missing {target_type}: {value}.", row)


def lineage_edges(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    return rows(ontology, "LineageEdge")


def check_lineage_refs(ontology: dict[str, Any], indexes: dict[str, dict[str, dict[str, Any]]], report: list[dict[str, Any]]) -> None:
    known_types = set(OBJECT_ARRAYS) | VIRTUAL_LINEAGE_TYPES
    for edge in lineage_edges(ontology):
        for side in ("from", "to"):
            object_type = edge.get(f"{side}_object_type")
            object_id_value = edge.get(f"{side}_object_id")
            if not object_type or not object_id_value:
                add(report, "lineage_endpoint_required", "error", "LineageEdge must include object type and ID endpoints.", edge)
                continue
            object_type = str(object_type)
            object_id_value = str(object_id_value)
            if object_type not in known_types:
                add(report, "lineage_type_known", "error", f"LineageEdge references unknown object type {object_type}.", edge)
                continue
            if object_type in OBJECT_ARRAYS and object_id_value not in indexes.get(object_type, {}):
                add(report, "lineage_reference_resolves", "error", f"LineageEdge references missing {object_type}: {object_id_value}.", edge)


def lineage_adjacency(ontology: dict[str, Any]) -> dict[tuple[str, str], list[tuple[str, str]]]:
    adjacency: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for edge in lineage_edges(ontology):
        from_type = edge.get("from_object_type")
        from_id = edge.get("from_object_id")
        to_type = edge.get("to_object_type")
        to_id = edge.get("to_object_id")
        if not all(isinstance(value, str) and value for value in (from_type, from_id, to_type, to_id)):
            continue
        adjacency.setdefault((from_type, from_id), []).append((to_type, to_id))
    return adjacency


def has_lineage_path(
    adjacency: dict[tuple[str, str], list[tuple[str, str]]],
    starts: list[tuple[str, str]],
    target: tuple[str, str],
    required_intermediate_type: str | None = None,
) -> bool:
    queue: list[tuple[tuple[str, str], bool]] = [
        (start, start[0] == required_intermediate_type if required_intermediate_type else True) for start in starts
    ]
    seen: set[tuple[tuple[str, str], bool]] = set(queue)
    while queue:
        current, has_required = queue.pop(0)
        if current == target and has_required:
            return True
        for nxt in adjacency.get(current, []):
            next_has_required = has_required or (nxt[0] == required_intermediate_type if required_intermediate_type else True)
            state = (nxt, next_has_required)
            if state not in seen:
                seen.add(state)
                queue.append(state)
    return False


def snapshots_for_source(ontology: dict[str, Any], source_evidence_id: Any) -> list[tuple[str, str]]:
    if not source_evidence_id:
        return []
    source_id = str(source_evidence_id)
    starts: list[tuple[str, str]] = []
    for snapshot in rows(ontology, "SourceSnapshot"):
        if str(snapshot.get("source_evidence_id", "")) == source_id:
            snapshot_id = snapshot.get("source_snapshot_id")
            if snapshot_id:
                starts.append(("SourceSnapshot", str(snapshot_id)))
    return starts


def check_quality(ontology: dict[str, Any], indexes: dict[str, dict[str, dict[str, Any]]], report: list[dict[str, Any]]) -> None:
    sources = indexes["SourceEvidence"]
    adjacency = lineage_adjacency(ontology)
    for rule in rows(ontology, "RequirementRule"):
        status = rule.get("verification_status")
        source_id = rule.get("source_evidence_id")
        if status == "verified" and (not source_id or str(source_id) not in sources):
            add(report, "no_verified_requirement_without_source", "blocker", "Verified RequirementRule must resolve to SourceEvidence.", rule)
        if status == "verified" and source_id and str(source_id) in sources:
            starts = snapshots_for_source(ontology, source_id)
            target_id = rule.get("requirement_rule_id")
            has_path = bool(target_id) and has_lineage_path(
                adjacency,
                starts,
                ("RequirementRule", str(target_id)),
                required_intermediate_type="ExtractedFact",
            )
            if not has_path:
                add(
                    report,
                    "no_verified_output_from_raw_source",
                    "blocker",
                    "Verified RequirementRule must have SourceSnapshot -> ExtractedFact -> RequirementRule lineage.",
                    rule,
                )
        if rule.get("rule_category") in {"application_route", "visa", "work_rights", "post_study", "credential_evaluation"} and not rule.get("applies_when"):
            add(
                report,
                "route_rules_are_conditional",
                "warning",
                "Route, visa, work-right, post-study, and credential-evaluation rules should include applies_when conditions.",
                rule,
            )

    for deadline in rows(ontology, "Deadline"):
        if deadline.get("due_at") and not deadline.get("timezone"):
            add(report, "no_deadline_without_timezone", "blocker", "Deadline with due_at must include timezone.", deadline)

    open_statuses = {"blocked", "not_started", "in_progress", "waiting_external"}
    tasks_by_case: dict[str, list[dict[str, Any]]] = {}
    for task in rows(ontology, "Task"):
        case_id = str(task.get("application_case_id", ""))
        tasks_by_case.setdefault(case_id, []).append(task)
    for case in rows(ontology, "ApplicationCase"):
        if case.get("status") in {"submitted", "visa_submitted", "closed"}:
            case_id = str(case.get("application_case_id", ""))
            blockers = [task for task in tasks_by_case.get(case_id, []) if task.get("status") in open_statuses]
            if blockers:
                add(report, "no_submitted_case_with_open_blockers", "blocker", "Submitted or closed ApplicationCase has open tasks.", case)

    for fact in rows(ontology, "ProgramFitFact"):
        status = fact.get("verification_status")
        source_id = fact.get("source_evidence_id")
        if status == "verified" and (not source_id or str(source_id) not in sources):
            add(report, "no_verified_program_fit_without_source", "error", "Verified ProgramFitFact must resolve to SourceEvidence.", fact)
        if status == "verified" and source_id and str(source_id) in sources:
            starts = snapshots_for_source(ontology, source_id)
            target_id = fact.get("program_fit_fact_id")
            has_path = bool(target_id) and has_lineage_path(
                adjacency,
                starts,
                ("ProgramFitFact", str(target_id)),
                required_intermediate_type="ExtractedFact",
            )
            if not has_path:
                add(
                    report,
                    "no_verified_output_from_raw_source",
                    "error",
                    "Verified ProgramFitFact must have SourceSnapshot -> ExtractedFact -> ProgramFitFact lineage.",
                    fact,
                )

    student_evidence = indexes["StudentEvidence"]
    program_facts = indexes["ProgramFitFact"]
    for claim in rows(ontology, "EssayClaim"):
        if claim.get("status") != "approved":
            continue
        evidence_ids = claim.get("student_evidence_ids") or []
        fit_ids = claim.get("program_fit_fact_ids") or []
        evidence_ok = isinstance(evidence_ids, list) and evidence_ids and all(str(item) in student_evidence for item in evidence_ids)
        fit_ok = isinstance(fit_ids, list) and fit_ids and all(str(item) in program_facts for item in fit_ids)
        if not evidence_ok or not fit_ok:
            add(report, "no_approved_essay_claim_without_evidence", "error", "Approved EssayClaim must resolve StudentEvidence and ProgramFitFact.", claim)
            continue
        claim_id = claim.get("essay_claim_id")
        if claim_id:
            evidence_lineage = any(
                has_lineage_path(adjacency, [("StudentEvidence", str(item))], ("EssayClaim", str(claim_id)))
                for item in evidence_ids
            )
            fit_lineage = any(
                has_lineage_path(adjacency, [("ProgramFitFact", str(item))], ("EssayClaim", str(claim_id)))
                for item in fit_ids
            )
            if not evidence_lineage or not fit_lineage:
                add(
                    report,
                    "essay_claim_lineage_required",
                    "error",
                    "Approved EssayClaim must have lineage from StudentEvidence and ProgramFitFact.",
                    claim,
                )

    today = date.today()
    for source in rows(ontology, "SourceEvidence"):
        checked = parse_date(source.get("checked_at") or source.get("checked_date"))
        stale_days = source.get("stale_after_days")
        if checked is None or stale_days in (None, ""):
            continue
        try:
            stale_after = checked + timedelta(days=int(stale_days))
        except (TypeError, ValueError):
            add(report, "source_staleness_check", "warning", "SourceEvidence stale_after_days must be an integer.", source)
            continue
        if stale_after < today:
            add(report, "source_staleness_check", "warning", "SourceEvidence is stale and should be refreshed.", source)

    for setup in rows(ontology, "UserSetup"):
        setup_report = validate_setup_data(setup)
        if setup_report.get("status") == "passed":
            continue
        missing = setup_report.get("missing_fields", [])
        if missing:
            add(
                report,
                "task_gate_required_fields_present",
                "error",
                f"UserSetup task gate is missing required fields: {', '.join(map(str, missing))}.",
                setup,
            )
        for finding in setup_report.get("schema_findings", []):
            add(
                report,
                "valid_user_setup_mode",
                str(finding.get("severity", "error")),
                str(finding.get("message", "UserSetup schema validation failed.")),
                setup,
            )


def summarize(report: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"info": 0, "warning": 0, "error": 0, "blocker": 0}
    for item in report:
        severity = item.get("severity", "info")
        counts[severity] = counts.get(severity, 0) + 1
    status = "failed" if counts.get("blocker", 0) or counts.get("error", 0) else "passed"
    return {"status": status, "counts": counts, "findings": report}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate study-abroad-advisor ontology JSON.")
    parser.add_argument("input_json", type=Path, help="Ontology JSON file.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    report: list[dict[str, Any]] = []
    ontology = load_ontology(args.input_json)
    indexes = build_indexes(ontology, report)
    check_refs(ontology, indexes, report)
    check_lineage_refs(ontology, indexes, report)
    check_quality(ontology, indexes, report)
    result = summarize(report)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
