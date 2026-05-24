#!/usr/bin/env python3
"""Validate Study Abroad Advisor setup JSON.

This script is dependency-free. It checks the lightweight user-facing setup
contract before the ontology layer is exposed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "references" / "setup" / "user-setup.schema.json"
DEFAULT_TASK_GATES = ROOT / "references" / "setup" / "task-gates.yaml"

FIELD_ALIASES = {
    "target_degree_level": ["target_degree_level", "degree_level"],
    "target_countries_or_regions": ["target_countries", "target_regions", "target_countries_or_regions"],
    "current_education_country": ["education_country", "current_education_country"],
    "gpa_or_equivalent": ["gpa_value", "gpa", "gpa_or_equivalent"],
    "gpa_value": ["gpa_value", "gpa"],
    "budget_annual": ["budget_annual", "annual_budget", "budget"],
    "language_status": ["language_status", "language_scores", "tests"],
    "applicant_route_fields": ["citizenship_countries", "residence_country", "education_country", "passport_country"],
    "program_official_name_or_url": ["program_official_name", "target_program", "official_url", "program_url"],
    "academic_background": ["current_major", "major", "gpa_value", "gpa", "core_courses"],
    "school_list": ["school_list", "schools", "shortlist"],
    "target_program_or_program_cluster": ["target_program", "target_programs", "program_cluster"],
    "essay_prompt_or_statement_goal": ["essay_prompt", "statement_goal", "prompt"],
    "word_limit_if_known": ["word_limit", "word_limit_if_known"],
    "ontology_json_or_structured_case_data": ["ontology_json", "structured_case_data", "ontology"],
    "target_application_cases": ["target_application_cases", "application_cases"],
    "document_status": ["document_status", "document_artifacts"],
    "deadline_timezone": ["deadline_timezone", "timezone", "deadlines"],
    "application_system": ["application_system", "route"],
    "source_log": ["source_log", "source_evidence"],
    "source_evidence_or_ontology_json": ["source_evidence", "ontology_json", "ontology"],
    "destination_country": ["destination_country", "target_country"],
    "offer_or_post_offer_document_status": ["offer_or_post_offer_document_status", "offer_decision", "post_offer_document_status"],
}

NEXT_QUESTIONS = {
    "target_degree_level": "What degree level are you applying for?",
    "target_field": "What field or major cluster are you targeting?",
    "target_countries_or_regions": "Which countries or regions should be included or excluded?",
    "current_education_country": "Which country is your current or most recent education from?",
    "gpa_or_equivalent": "What is your GPA, class, or equivalent academic standing?",
    "target_intake": "What intake year and term are you targeting?",
    "target_countries": "Which target countries should be researched?",
    "citizenship_countries": "What citizenship country or countries do you hold?",
    "residence_country": "What is your current residence country?",
    "education_country": "What country is your current or most recent education from?",
    "passport_country": "What country issued your passport?",
    "gpa_value": "What is your GPA or grade value?",
    "gpa_scale": "What is the GPA scale or grading system?",
    "budget_annual": "What is the annual budget ceiling?",
    "language_status": "What is your language-test or English-medium-instruction status?",
    "risk_tolerance": "Do you prefer ambitious, balanced, or conservative choices?",
    "applicant_route_fields": "Provide citizenship, residence country, education country, and passport country.",
    "program_official_name_or_url": "Provide the official program name or URL.",
    "target_program_or_program_cluster": "Which target program or program cluster is the essay for?",
    "essay_prompt_or_statement_goal": "What prompt or statement goal should the essay answer?",
    "student_evidence": "What real courses, projects, research, work, or achievements support the essay?",
    "ontology_json_or_structured_case_data": "Provide ontology JSON or structured case data for workbook rendering.",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Setup JSON must be an object.")
    return data


def extract_setup(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("user_setup"), dict):
        return data["user_setup"]
    ontology = data.get("ontology")
    if isinstance(ontology, dict):
        setups = ontology.get("user_setups")
        if isinstance(setups, list) and setups and isinstance(setups[0], dict):
            merged = dict(setups[0])
            applicants = ontology.get("applicants")
            profile: dict[str, Any] = {}
            if isinstance(applicants, list) and applicants and isinstance(applicants[0], dict):
                profile.update(applicants[0])
            credentials = ontology.get("education_credentials")
            if isinstance(credentials, list) and credentials and isinstance(credentials[0], dict):
                credential = credentials[0]
                profile.setdefault("gpa_value", credential.get("gpa_value"))
                profile.setdefault("gpa_scale", credential.get("gpa_scale"))
                profile.setdefault("current_institution", credential.get("institution"))
                profile.setdefault("current_major", credential.get("major"))
                profile.setdefault("education_country", credential.get("country"))
            if profile:
                merged.setdefault("profile", profile)
            return merged
    return data


def type_ok(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    return True


def validate_schema(setup: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for field in (required if isinstance(required, list) else []):
        if not present(setup.get(str(field))):
            findings.append({"severity": "error", "field": str(field), "message": "Required setup field is missing."})
    for field, spec in (properties.items() if isinstance(properties, dict) else []):
        if field not in setup or not isinstance(spec, dict):
            continue
        value = setup[field]
        expected = spec.get("type")
        if isinstance(expected, str) and not type_ok(value, expected):
            findings.append({"severity": "error", "field": field, "message": f"Expected {expected}."})
            continue
        allowed = spec.get("enum")
        if isinstance(allowed, list) and value not in allowed:
            findings.append({"severity": "error", "field": field, "message": f"Value must be one of: {', '.join(map(str, allowed))}."})
        if isinstance(value, int):
            if "minimum" in spec and value < int(spec["minimum"]):
                findings.append({"severity": "error", "field": field, "message": f"Value must be >= {spec['minimum']}."})
            if "maximum" in spec and value > int(spec["maximum"]):
                findings.append({"severity": "error", "field": field, "message": f"Value must be <= {spec['maximum']}."})
    return findings


def load_task_gates(path: Path) -> dict[str, dict[str, Any]]:
    gates: dict[str, dict[str, Any]] = {}
    current_gate: str | None = None
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#") or line.strip() == "task_gates:":
            continue
        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            current_gate = line.strip()[:-1]
            gates[current_gate] = {}
            current_key = None
            continue
        if current_gate and line.startswith("    ") and not line.startswith("      "):
            key, _, value = line.strip().partition(":")
            current_key = key
            if value.strip():
                gates[current_gate][key] = value.strip()
            else:
                gates[current_gate][key] = []
            continue
        if current_gate and current_key and line.startswith("      - "):
            gates[current_gate].setdefault(current_key, [])
            gates[current_gate][current_key].append(line.strip()[2:].strip())
    return gates


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and not normalized.startswith("needs ") and normalized not in {"unknown", "n/a", "none", "tbd"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def lookup_field(setup: dict[str, Any], field: str) -> Any:
    aliases = FIELD_ALIASES.get(field, [field])
    scopes: list[dict[str, Any]] = [setup]
    for key in ("profile", "applicant", "education", "preferences", "preference_weights"):
        value = setup.get(key)
        if isinstance(value, dict):
            scopes.append(value)
    for scope in scopes:
        for alias in aliases:
            if present(scope.get(alias)):
                return scope.get(alias)
    if field == "applicant_route_fields":
        return all(present(lookup_field(setup, part)) for part in FIELD_ALIASES[field])
    return None


def gate_for_mode(gates: dict[str, dict[str, Any]], workflow_mode: str) -> tuple[str | None, dict[str, Any]]:
    for gate_name, gate in gates.items():
        if gate.get("workflow_mode") == workflow_mode:
            return gate_name, gate
    return None, {}


def validate_setup_data(setup: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA, gates_path: Path = DEFAULT_TASK_GATES) -> dict[str, Any]:
    schema = load_json(schema_path)
    findings = validate_schema(setup, schema)
    gates = load_task_gates(gates_path)
    workflow_mode = str(setup.get("workflow_mode", ""))
    gate_name, gate = gate_for_mode(gates, workflow_mode)
    missing: list[str] = []
    if workflow_mode and not gate:
        findings.append({"severity": "error", "field": "workflow_mode", "message": "No task gate is defined for workflow_mode."})
    required_fields = gate.get("required", [])
    for field in (required_fields if isinstance(required_fields, list) else []):
        if not present(lookup_field(setup, str(field))):
            missing.append(str(field))
    status = "passed" if not findings and not missing else "failed"
    return {
        "status": status,
        "workflow_mode": workflow_mode,
        "output_mode": setup.get("output_mode", ""),
        "gate": gate_name or "",
        "missing_fields": missing,
        "schema_findings": findings,
        "allowed_outputs": gate.get("allowed_outputs", []),
        "blocked_outputs": gate.get("blocked_outputs", []),
        "next_questions": [NEXT_QUESTIONS.get(field, f"Provide {field}.") for field in missing[:7]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Study Abroad Advisor setup JSON.")
    parser.add_argument("setup_json", type=Path, help="Setup JSON, or ontology JSON containing ontology.user_setups.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Setup JSON schema path.")
    parser.add_argument("--task-gates", type=Path, default=DEFAULT_TASK_GATES, help="Task gates YAML path.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    setup = extract_setup(load_json(args.setup_json))
    report = validate_setup_data(setup, args.schema, args.task_gates)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
