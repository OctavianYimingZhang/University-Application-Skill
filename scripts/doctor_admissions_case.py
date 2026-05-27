#!/usr/bin/env python3
"""Diagnose what a Study Abroad Advisor case can do next."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_ontology import build_indexes, check_lineage_refs, check_quality, check_refs, load_ontology, summarize
from validate_setup import extract_setup, load_json, validate_setup_data


def ontology_report(path: Path) -> dict[str, Any]:
    report: list[dict[str, Any]] = []
    ontology = load_ontology(path)
    indexes = build_indexes(ontology, report)
    check_refs(ontology, indexes, report)
    check_lineage_refs(ontology, indexes, report)
    check_quality(ontology, indexes, report)
    return summarize(report)


def extract_setup_from_inputs(ontology_path: Path, setup_path: Path | None) -> dict[str, Any]:
    if setup_path:
        return extract_setup(load_json(setup_path))
    return extract_setup(load_json(ontology_path))


def can_do_from_setup(setup_report: dict[str, Any]) -> list[str]:
    outputs = setup_report.get("allowed_outputs", [])
    result = ["intake_summary", "missing_fields_report"]
    if isinstance(outputs, list):
        for output in outputs:
            if output not in result:
                result.append(str(output))
    return result


def cannot_do_from_reports(setup_report: dict[str, Any], ontology_report_data: dict[str, Any]) -> list[str]:
    blocked: list[str] = []
    blocked_outputs = setup_report.get("blocked_outputs", [])
    for output in (blocked_outputs if isinstance(blocked_outputs, list) else []):
        blocked.append(str(output))
    counts = ontology_report_data.get("counts", {})
    if counts.get("blocker") or counts.get("error"):
        blocked.extend(["verified_workbook", "verified_shortlist", "final_submission_checklist"])
    if setup_report.get("status") != "passed":
        blocked.extend(["verified_shortlist", "final_recommendation"])
    return sorted(set(blocked))


def blocker_items(setup_report: dict[str, Any], ontology_report_data: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    missing = setup_report.get("missing_fields", [])
    if missing:
        blockers.append({"gate": setup_report.get("gate", ""), "missing": missing})
    for finding in ontology_report_data.get("findings", []):
        if finding.get("severity") in {"blocker", "error"}:
            blockers.append(
                {
                    "check": finding.get("check", ""),
                    "object_id": finding.get("object_id", ""),
                    "issue": finding.get("message", ""),
                    "severity": finding.get("severity", ""),
                }
            )
    return blockers


def warning_items(setup_report: dict[str, Any], ontology_report_data: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for finding in setup_report.get("schema_findings", []):
        if finding.get("severity") == "warning":
            warnings.append(finding)
    for finding in ontology_report_data.get("findings", []):
        if finding.get("severity") == "warning":
            warnings.append(finding)
    return warnings


def status_from_reports(setup_report: dict[str, Any], ontology_report_data: dict[str, Any]) -> str:
    output_mode = setup_report.get("output_mode")
    if setup_report.get("status") != "passed":
        return f"blocked_for_{setup_report.get('workflow_mode') or 'selected_workflow'}"
    counts = ontology_report_data.get("counts", {})
    if counts.get("blocker") or counts.get("error"):
        return "blocked_for_verified_output"
    if output_mode == "verified":
        return "ready_for_verified_track"
    if output_mode in {"brainstorm", "draft"}:
        return "ready_for_draft_track"
    return "ready_for_source_backed_track"


def diagnose(ontology_path: Path, setup_path: Path | None = None) -> dict[str, Any]:
    setup = extract_setup_from_inputs(ontology_path, setup_path)
    setup_report = validate_setup_data(setup)
    ontology_report_data = ontology_report(ontology_path)
    blockers = blocker_items(setup_report, ontology_report_data)
    warnings = warning_items(setup_report, ontology_report_data)
    next_questions = setup_report.get("next_questions", [])
    if not next_questions and blockers:
        next_questions = ["Resolve the listed blockers before requesting a verified output."]
    return {
        "status": status_from_reports(setup_report, ontology_report_data),
        "workflow_mode": setup_report.get("workflow_mode", ""),
        "output_mode": setup_report.get("output_mode", ""),
        "can_do": can_do_from_setup(setup_report),
        "cannot_do": cannot_do_from_reports(setup_report, ontology_report_data),
        "blockers": blockers,
        "warnings": warnings,
        "next_questions": next_questions,
        "setup_report": setup_report,
        "ontology_quality": {
            "status": ontology_report_data.get("status"),
            "counts": ontology_report_data.get("counts", {}),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose Study Abroad Advisor ontology and setup state.")
    parser.add_argument("ontology_json", type=Path, help="Ontology JSON file.")
    parser.add_argument("--setup", type=Path, help="Optional setup JSON. Defaults to ontology.user_setups when present.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    report = diagnose(args.ontology_json, args.setup)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    sys.exit(main())
