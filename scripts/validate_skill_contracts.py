#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from build_admissions_workbook import build_sheets

ROOT = Path(__file__).resolve().parents[1]

CONTRACT_FILES = {
    "README.md",
    "academic-task-context-v1.schema.json",
    "local-bridge-protocol-v1.schema.json",
    "plugin-capability-manifest-v2.schema.json",
    "source-record-v1.schema.json",
    "task-run-state-v1.schema.json",
}
EVIDENCE_FIELDS = {
    "evidence_id",
    "value",
    "source",
    "evidence_date",
    "confirmation_status",
    "confirmed_at",
    "source_availability",
    "fact_verification",
    "completeness",
    "application_cycle",
    "accessed_at",
    "staleness",
}
COMPANION_SITE_URL = "https://soleil-admissions.ready-loach-3659.chatgpt.site"
RETIRED_PATHS = (
    Path("web"),
    Path(".github/workflows/pages.yml"),
    Path("scripts/codex_oauth_bridge.mjs"),
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def json_schema_errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON Schema subset used by ApplicationCase v1."""
    errors: list[str] = []

    def matches_type(candidate: Any, expected: str) -> bool:
        checks = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        return checks.get(expected, lambda item: True)(candidate)

    expected_type = schema.get("type")
    if expected_type:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(matches_type(value, item) for item in allowed):
            return [f"{path}: expected type {allowed}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value is outside enum")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than minLength")
        if schema.get("pattern") and not re.search(schema["pattern"], value):
            errors.append(f"{path}: string does not match pattern")
        if schema.get("format") == "uri":
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                errors.append(f"{path}: invalid URI")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: array is shorter than minItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(json_schema_errors(item, item_schema, f"{path}[{index}]"))
        contains_schema = schema.get("contains")
        if isinstance(contains_schema, dict) and not any(
            not json_schema_errors(item, contains_schema, f"{path}[{index}]")
            for index, item in enumerate(value)
        ):
            errors.append(f"{path}: no array item matched contains")
    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                errors.append(f"{path}: missing required property {field}")
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in value:
                errors.extend(json_schema_errors(value[field], field_schema, f"{path}.{field}"))
        if schema.get("additionalProperties") is False:
            for field in set(value) - set(properties):
                errors.append(f"{path}: unexpected property {field}")
    if "anyOf" in schema:
        if not any(not json_schema_errors(value, branch, path) for branch in schema["anyOf"]):
            errors.append(f"{path}: no anyOf branch matched")
    if "oneOf" in schema:
        matches = sum(not json_schema_errors(value, branch, path) for branch in schema["oneOf"])
        if matches != 1:
            errors.append(f"{path}: expected exactly one oneOf branch, got {matches}")
    for branch in schema.get("allOf", []):
        errors.extend(json_schema_errors(value, branch, path))
    condition = schema.get("if")
    if isinstance(condition, dict) and not json_schema_errors(value, condition, path):
        then_schema = schema.get("then")
        if isinstance(then_schema, dict):
            errors.extend(json_schema_errors(value, then_schema, path))
    return errors


def application_case_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    """Validate ApplicationCase JSON shape plus cross-field provenance invariants."""
    errors = json_schema_errors(value, schema)
    if not isinstance(value, dict) or value.get("contract") != "ApplicationCase":
        return errors

    case_cycle = value.get("application_cycle")
    source_log = value.get("source_log") if isinstance(value.get("source_log"), list) else []
    source_ids: set[str] = set()
    current_official_ids: set[str] = set()
    for index, source in enumerate(source_log):
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        if isinstance(source_id, str):
            if source_id in source_ids:
                errors.append(f"$.source_log[{index}]: duplicate source_id {source_id}")
            source_ids.add(source_id)
        if source.get("source_type") == "official_url" and "current_cycle_match" in source:
            actual_match = (
                isinstance(case_cycle, str)
                and isinstance(source.get("application_cycle"), str)
                and source.get("application_cycle") == case_cycle
            )
            if source.get("current_cycle_match") is not actual_match:
                errors.append(
                    f"$.source_log[{index}]: current_cycle_match disagrees with the case application_cycle"
                )
            if (
                actual_match
                and source.get("current_cycle_match") is True
                and source.get("status") == "verified"
                and source.get("staleness") == "fresh"
                and isinstance(source_id, str)
            ):
                current_official_ids.add(source_id)

    referenced_sections = ("requirements", "documents", "deadlines", "writing_tasks")
    for section in referenced_sections:
        entries = value.get(section)
        if not isinstance(entries, list):
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or "source_ids" not in entry:
                continue
            refs = entry.get("source_ids")
            if not isinstance(refs, list):
                continue
            for source_id in refs:
                if isinstance(source_id, str) and source_id not in source_ids:
                    errors.append(f"$.{section}[{index}]: unknown source_id {source_id}")
    supervisor_fit = value.get("supervisor_fit")
    if isinstance(supervisor_fit, dict) and isinstance(supervisor_fit.get("source_ids"), list):
        for source_id in supervisor_fit["source_ids"]:
            if isinstance(source_id, str) and source_id not in source_ids:
                errors.append(f"$.supervisor_fit: unknown source_id {source_id}")
    workstreams = value.get("workstream_status") if isinstance(value.get("workstream_status"), dict) else {}
    complete_section_map = {
        "requirements": "requirements",
        "materials": "documents",
        "writing": "writing_tasks",
        "submission": "documents",
    }
    for workstream, section in complete_section_map.items():
        if workstreams.get(workstream) != "complete":
            continue
        entries = value.get(section) if isinstance(value.get(section), list) else []
        for index, entry in enumerate(entries):
            refs = entry.get("source_ids") if isinstance(entry, dict) else None
            if not isinstance(refs, list) or not current_official_ids.intersection(refs):
                errors.append(f"$.{section}[{index}]: {workstream} completion lacks current official provenance")
    if workstreams.get("supervisor") == "complete" or workstreams.get("programme_fit") == "complete":
        refs = supervisor_fit.get("source_ids") if isinstance(supervisor_fit, dict) else None
        if not isinstance(refs, list) or not current_official_ids.intersection(refs):
            errors.append("$.supervisor_fit: completed supervisor or programme fit lacks current official provenance")
    return errors


def check_manifest() -> dict[str, Any]:
    path = ROOT / "skill_manifest.json"
    if not path.exists():
        fail("skill_manifest.json missing")
    manifest = read_json(path)
    required = {
        "schema_version", "skill_id", "repo", "branch", "entrypoint", "multi_skill_system", "routes",
        "focused_skills", "plugin_router_skill", "index_skill", "compatibility_aliases", "capability_manifest", "application_case_schema",
        "catalogue_index", "catalogue_schemas",
        "supported_context_versions", "default_output_language",
    }
    missing = sorted(required - set(manifest))
    if missing:
        fail("manifest missing fields: " + ", ".join(missing))
    if manifest.get("skill_id") != "university-application-index":
        fail("university-application-index must be the canonical skill_id")
    if manifest.get("default_output_language") != "en":
        fail("manifest default_output_language must be en")
    if manifest.get("supported_context_versions") != [1]:
        fail("manifest must support AcademicTaskContext v1")
    if not (ROOT / manifest["entrypoint"]).exists():
        fail(f"manifest entrypoint missing: {manifest['entrypoint']}")
    router = manifest["plugin_router_skill"]
    if router.get("name") != "university-application-index" or router.get("path") != manifest.get("index_skill"):
        fail("plugin router and index_skill must both be university-application-index")
    if not (ROOT / router["path"]).exists():
        fail("canonical plugin router skill path missing")
    aliases = manifest.get("compatibility_aliases", [])
    expected_alias = {
        "name": "study-abroad-advisor",
        "path": "skills/study-abroad-advisor/SKILL.md",
        "canonical": "university-application-index",
    }
    if expected_alias not in aliases:
        fail("study-abroad-advisor compatibility alias metadata missing")
    if not (ROOT / manifest["capability_manifest"]).exists():
        fail("plugin capability manifest missing")
    if not (ROOT / manifest["application_case_schema"]).exists():
        fail("ApplicationCase schema missing")
    if not (ROOT / manifest["catalogue_index"]).exists():
        fail("Plugin-owned programme catalogue index missing")
    catalogue_schemas = manifest.get("catalogue_schemas")
    if not isinstance(catalogue_schemas, list) or len(catalogue_schemas) != 2:
        fail("catalogue_schemas must list the index and institution schemas")
    for schema_path in catalogue_schemas:
        if not (ROOT / schema_path).exists():
            fail(f"programme catalogue schema missing: {schema_path}")
    if "web" in manifest:
        fail("skill_manifest.json must not declare a retired web package")
    companion = manifest.get("companion_site")
    if not isinstance(companion, dict):
        fail("companion_site metadata missing")
    if companion.get("url") != COMPANION_SITE_URL:
        fail("companion_site URL must point to the owner-only Soleil Admissions Site")
    if companion.get("access") != "owner_only" or companion.get("source_in_repository") is not False:
        fail("companion_site must remain owner-only and external to this repository")
    for command in manifest.get("health_commands", []):
        if re.search(r"(?:^|[ /])(web|npm|vite)(?:$|[ /])", command, flags=re.IGNORECASE):
            fail(f"health command still depends on the retired web package: {command}")
    return manifest


def check_plugin_only_package() -> None:
    for relative_path in RETIRED_PATHS:
        if (ROOT / relative_path).exists():
            fail(f"retired public web surface returned: {relative_path.as_posix()}")

    plugin = read_json(ROOT / ".codex-plugin" / "plugin.json")
    if plugin.get("interface", {}).get("websiteURL") != COMPANION_SITE_URL:
        fail("Plugin websiteURL must point to the owner-only Soleil Admissions Site")

    workflow_dir = ROOT / ".github" / "workflows"
    for path in [*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]:
        body = text(path).lower()
        for token in ("actions/deploy-pages", "actions/upload-pages-artifact", "pages: write", "github-pages"):
            if token in body:
                fail(f"GitHub Pages functionality returned in {path.relative_to(ROOT)}: {token}")

    for path in (ROOT / "scripts").glob("*"):
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.is_file() and any(token in text(path) for token in ("/codex/start-oauth", "codex_bridge_nonce")):
            fail(f"browser OAuth bridge functionality returned in {path.relative_to(ROOT)}")

    forbidden_doc_phrases = (
        "octavianyimingzhang.github.io/University-Application-Skill",
        "Browser Memory Studio",
        "Website Memory Studio",
        "web/public/memory.html",
        "scripts/codex_oauth_bridge.mjs",
    )
    documentation = [
        ROOT / "README.md",
        ROOT / "COPY_PACKAGE.md",
        ROOT / "SKILL.md",
        ROOT / "references" / "memory-system.md",
        ROOT / "references" / "setup" / "setup-workflow.md",
        ROOT / "catalogues" / "README.md",
        ROOT / "memory" / "README.md",
    ]
    for path in documentation:
        body = text(path)
        for phrase in forbidden_doc_phrases:
            if phrase in body:
                fail(f"retired web documentation returned in {path.relative_to(ROOT)}: {phrase}")


def check_focused_skills(manifest: dict[str, Any]) -> None:
    seen: set[str] = set()
    for item in manifest.get("focused_skills", []):
        name = item.get("name")
        path = item.get("path")
        route = item.get("route")
        if not name or not path or not route:
            fail(f"focused skill entry incomplete: {item}")
        if name in seen:
            fail(f"duplicate focused skill: {name}")
        seen.add(name)
        skill_path = ROOT / path
        if not skill_path.exists():
            fail(f"focused skill file missing: {path}")
        body = text(skill_path)
        if f"name: {name}" not in body:
            fail(f"focused skill frontmatter mismatch: {path}")
        if "default to english" not in body.lower():
            fail(f"focused skill missing English default: {path}")
    if {"university-application-index", "visa-readiness"} - seen:
        fail("canonical index or visa-readiness focused Skill missing")

    alias_path = ROOT / "skills" / "study-abroad-advisor" / "SKILL.md"
    alias = text(alias_path)
    if len(alias.splitlines()) > 14 or "../university-application-index/SKILL.md" not in alias:
        fail("study-abroad-advisor must remain a thin compatibility alias")


def check_relative_resource_links() -> None:
    skill_files = [ROOT / "SKILL.md", *(ROOT / "skills").glob("*/SKILL.md")]
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for skill_path in skill_files:
        body = text(skill_path)
        for raw_target in link_pattern.findall(body):
            target = raw_target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "#")):
                continue
            if target.startswith("/"):
                fail(f"absolute local link in {skill_path.relative_to(ROOT)}: {target}")
            resolved = (skill_path.parent / target).resolve()
            if not resolved.exists():
                fail(f"broken local link in {skill_path.relative_to(ROOT)}: {target}")
            if skill_path.parent.parent == ROOT / "skills" and target.startswith(("references/", "scripts/", "contracts/", "catalogues/")):
                fail(f"focused Skill resource link is relative to the wrong directory: {skill_path.relative_to(ROOT)} -> {target}")


def check_capability_manifest(manifest: dict[str, Any]) -> None:
    path = ROOT / manifest["capability_manifest"]
    capabilities = read_json(path)
    if capabilities.get("contract") != "PluginCapabilityManifest" or capabilities.get("version") != 2:
        fail("capability manifest contract/version mismatch")
    if capabilities.get("plugin_id") != "university-application-skill":
        fail("capability manifest plugin_id mismatch")
    if capabilities.get("default_output_language") != "en":
        fail("capability manifest default output must be English")
    if capabilities.get("supported_context_versions") != [1]:
        fail("capability manifest must support AcademicTaskContext v1")

    routes = capabilities.get("routes")
    if not isinstance(routes, list):
        fail("capability manifest routes must be an array")
    route_ids = [item.get("route_id") for item in routes if isinstance(item, dict)]
    if len(route_ids) != len(set(route_ids)):
        fail("duplicate route_id in capability manifest")
    if set(route_ids) != set(manifest.get("routes", [])):
        fail("capability manifest routes differ from skill_manifest routes")

    focused_by_route = {item["route"]: item["name"] for item in manifest.get("focused_skills", [])}
    for route in routes:
        required = {
            "route_id", "owning_skill", "triggers", "required_inputs", "gates", "outputs",
            "adapter_entrypoint", "supported_context_versions",
        }
        if set(route) != required:
            fail(f"capability route fields drifted: {route.get('route_id')}")
        route_id = route["route_id"]
        if focused_by_route.get(route_id) != route.get("owning_skill"):
            fail(f"capability owning_skill mismatch: {route_id}")
        if route.get("supported_context_versions") != [1]:
            fail(f"route does not support AcademicTaskContext v1: {route_id}")
        triggers = route.get("triggers", {})
        if set(triggers) != {"semantic_intents", "examples", "direct_invocation"}:
            fail(f"route trigger fields drifted: {route_id}")
        if not isinstance(triggers.get("direct_invocation"), bool):
            fail(f"route direct_invocation must be boolean: {route_id}")
        if not any(any(ord(char) > 127 for char in example) for example in triggers.get("examples", [])):
            fail(f"route lacks a non-English routing example: {route_id}")
        for item in route.get("required_inputs", []):
            if not isinstance(item.get("input_id"), str) or not isinstance(item.get("required"), bool):
                fail(f"route input fields are invalid: {route_id}")
            schema_ref = item.get("schema_ref")
            if schema_ref and not (ROOT / schema_ref).exists():
                fail(f"route input schema_ref is missing: {route_id} -> {schema_ref}")
        for gate in route.get("gates", []):
            if not isinstance(gate.get("gate_id"), str) or not isinstance(gate.get("required"), bool):
                fail(f"route gate fields are invalid: {route_id}")
        for output in route.get("outputs", []):
            if not isinstance(output.get("output_id"), str):
                fail(f"route output fields are invalid: {route_id}")
            schema_ref = output.get("schema_ref")
            if schema_ref and not (ROOT / schema_ref).exists():
                fail(f"route output schema_ref is missing: {route_id} -> {schema_ref}")
        adapter = route.get("adapter_entrypoint", {})
        if adapter.get("type") != "skill" or not (ROOT / str(adapter.get("value", ""))).exists():
            fail(f"route adapter is missing: {route_id}")

    route_map = {item["route_id"]: item for item in routes}
    requirement_gates = {item["gate_id"]: item for item in route_map["requirement_audit"]["gates"]}
    applicant_gate = requirement_gates.get("applicant_evidence_confirmation")
    if not applicant_gate or applicant_gate.get("required") is not False:
        fail("requirements-only audit must not require applicant evidence")
    materials_inputs = {
        item["input_id"]: item for item in route_map["materials_check"]["required_inputs"]
    }
    for input_id in ("application_cycle", "applicant_document_inventory"):
        if not materials_inputs.get(input_id, {}).get("required"):
            fail(f"materials-check required input missing: {input_id}")
    visa_gates = {item["gate_id"] for item in route_map["visa_readiness"]["gates"]}
    if {"official_government_provenance", "applicant_evidence_confirmation", "non_legal_advice_boundary"} - visa_gates:
        fail("visa-readiness provenance, evidence, or non-legal-advice gate missing")
    maintenance_gates = {item["gate_id"] for item in route_map["programme_table_cleaning"]["gates"]}
    if "maintenance_authorization" not in maintenance_gates:
        fail("programme-table-cleaning must require explicit maintenance authorization")


def check_shared_contracts() -> None:
    contracts_dir = ROOT / "contracts"
    actual = {path.name for path in contracts_dir.iterdir()} if contracts_dir.exists() else set()
    if actual != CONTRACT_FILES:
        fail("shared Soleil contract set is missing or contains unexpected files")
    context = read_json(contracts_dir / "academic-task-context-v1.schema.json")
    decision_status = context["properties"]["decisions"]["items"]["properties"]["status"]["enum"]
    if decision_status != ["suggested", "explicitly_confirmed"]:
        fail("AcademicTaskContext decision statuses drifted")
    route_status = context["properties"]["route_selection"]["properties"]["status"]["enum"]
    if route_status != ["suggested", "explicitly_confirmed"]:
        fail("AcademicTaskContext route statuses drifted")
    contract_readme = text(contracts_dir / "README.md")
    if "All shipped output defaults to English" not in contract_readme:
        fail("shared contracts missing English output default")


def check_evidence_contract() -> None:
    evidence_reference = text(ROOT / "references" / "evidence-contract.md")
    evidence_script = text(ROOT / "scripts" / "validate_evidence.py")
    setup_schema = text(ROOT / "references" / "setup" / "user-setup.schema.json")
    for field in EVIDENCE_FIELDS:
        if any(field not in body for body in (evidence_reference, evidence_script, setup_schema)):
            fail(f"evidence contract field missing from reference, validator, or schema: {field}")
    for token in (
        "unconfirmed", "explicitly_confirmed", "available", "unavailable", "unknown", "unverified",
        "verified", "conflicted", "placeholder", "partial", "complete", "fresh", "stale",
        "public_url", "local_document", "user_confirmation", "official_requirement", "submission",
    ):
        if token not in evidence_script:
            fail(f"evidence validator status missing: {token}")
    for token in ("fact_class", "evidence_use", "mutable_official_fact", "applicant_personal_fact"):
        if any(token not in body for body in (evidence_reference, evidence_script, setup_schema)):
            fail(f"evidence fact-class or purpose contract missing: {token}")


def check_workbook_contract() -> None:
    evidence = {
        "evidence_id": "workbook-evidence",
        "value": "Applicant evidence for workbook validation.",
        "fact_class": "applicant_personal_fact",
        "source": {
            "type": "user_confirmation",
            "confirmed_by": "current_user",
            "title": "Workbook validation confirmation",
        },
        "evidence_date": "2026-07-15",
        "confirmation_status": "explicitly_confirmed",
        "confirmed_at": "2026-07-15T00:00:00+00:00",
        "source_availability": "available",
        "fact_verification": "verified",
        "completeness": "complete",
        "application_cycle": "2026-27",
        "accessed_at": "2026-07-15T00:00:00+00:00",
        "staleness": "fresh",
    }
    sheets = build_sheets({
        "application_cycle": "2026-27",
        "applicant_evidence": [evidence],
        "supervisor_fit": {"contact_requirement": "recommended", "source_ids": ["source_programme"]},
        "writing_tasks": [{"writing_task_id": "writing_sop", "document_type": "SOP", "status": "planning"}],
        "risks": [{"risk_id": "risk_1", "description": "Example risk", "status": "open"}],
        "actions": [{"action_id": "action_1", "description": "Example action", "status": "pending"}],
        "source_log": [{"source_id": "source_programme", "title": "Programme page"}],
        "workstream_status": {"writing": "in_progress"},
    })
    evidence_headers = sheets["Applicant_Evidence"][0]
    if "evidence_passes" not in evidence_headers:
        fail("workbook dropped the legacy evidence_passes column")
    for sheet_name in ("Supervisor_Fit", "Writing_Tasks", "Risks_Gaps", "Tasks", "Source_Log", "Workstream_Status"):
        if sheet_name not in sheets or sheets[sheet_name] == [["No data"]]:
            fail(f"workbook does not render optional ApplicationCase section: {sheet_name}")


def check_application_case_schema(manifest: dict[str, Any]) -> None:
    schema = read_json(ROOT / manifest["application_case_schema"])
    if schema.get("properties", {}).get("contract", {}).get("const") != "ApplicationCase":
        fail("ApplicationCase schema contract mismatch")
    if schema.get("properties", {}).get("version", {}).get("const") != 1:
        fail("ApplicationCase schema version mismatch")
    required = {
        "contract", "version", "case_id", "institution", "programme_name", "degree_level",
        "official_programme_url", "application_cycle", "source_availability", "fact_verification",
        "completeness", "accessed_at", "staleness", "custom_case", "created_at", "updated_at",
    }
    if set(schema.get("required", [])) != required:
        fail("ApplicationCase required fields drifted")
    properties = schema.get("properties", {})
    expected_enums = {
        "source_availability": ["available", "unavailable", "unknown"],
        "fact_verification": ["unverified", "verified", "conflicted"],
        "completeness": ["placeholder", "partial", "complete"],
        "staleness": ["fresh", "stale", "unknown"],
    }
    for field, values in expected_enums.items():
        if properties.get(field, {}).get("enum") != values:
            fail(f"ApplicationCase enum drifted: {field}")
    if properties.get("official_programme_url", {}).get("pattern") != "^https://":
        fail("ApplicationCase official_programme_url must require HTTPS")
    optional_state = {
        "lifecycle_status", "requirements", "documents", "deadlines", "supervisor_fit",
        "writing_tasks", "risks", "actions", "source_log", "workstream_status", "last_verified_at",
    }
    missing_optional = sorted(optional_state - set(properties))
    if missing_optional:
        fail("ApplicationCase optional workflow state missing: " + ", ".join(missing_optional))
    workstreams = properties.get("workstream_status", {}).get("properties", {})
    expected_workstreams = {"requirements", "supervisor", "programme_fit", "materials", "writing", "submission"}
    if set(workstreams) != expected_workstreams:
        fail("ApplicationCase workstream status fields drifted")

    old_case = {
        "contract": "ApplicationCase",
        "version": 1,
        "case_id": "case_example",
        "institution": "Example University",
        "programme_name": "Example MRes",
        "degree_level": "postgraduate",
        "official_programme_url": "https://www.example.edu/programme",
        "application_cycle": "2026-27",
        "source_availability": "available",
        "fact_verification": "verified",
        "completeness": "complete",
        "accessed_at": "2026-07-15T00:00:00+00:00",
        "staleness": "fresh",
        "custom_case": True,
        "created_at": "2026-07-15T00:00:00+00:00",
        "updated_at": "2026-07-15T00:00:00+00:00",
    }
    source_record = {
        "source_id": "source_programme",
        "source_type": "official_url",
        "title": "Official programme page",
        "status": "verified",
        "url": "https://www.example.edu/programme",
        "application_cycle": "2026-27",
        "accessed_at": "2026-07-15T00:00:00+00:00",
        "staleness": "fresh",
        "current_cycle_match": True,
    }
    extended_case = {
        **old_case,
        "lifecycle_status": "requirements_review",
        "requirements": [{
            "requirement_id": "req_statement",
            "category": "writing",
            "description": "A statement is required.",
            "status": "required",
            "source_ids": ["source_programme"],
        }],
        "documents": [{
            "document_id": "doc_cv",
            "name": "CV",
            "status": "available",
            "evidence_ids": ["evidence_cv"],
            "source_ids": ["source_programme"],
        }],
        "deadlines": [{
            "deadline_id": "deadline_main",
            "name": "Application deadline",
            "date": "2027-01-15",
            "status": "upcoming",
            "source_ids": ["source_programme"],
        }],
        "supervisor_fit": {
            "contact_requirement": "recommended",
            "source_ids": ["source_programme"],
            "candidates": [],
            "research_fit": [],
            "publication_fit": [],
            "module_or_structure_fit": [],
        },
        "writing_tasks": [{
            "writing_task_id": "writing_sop",
            "document_type": "statement of purpose",
            "programme": "Example MRes",
            "status": "planning",
            "source_ids": ["source_programme"],
        }],
        "risks": [{"risk_id": "risk_deadline", "description": "Deadline is near.", "status": "open"}],
        "actions": [{"action_id": "action_draft", "description": "Draft the statement.", "status": "pending"}],
        "source_log": [source_record],
        "workstream_status": {field: "not_started" for field in expected_workstreams},
        "last_verified_at": "2026-07-15T00:00:00+00:00",
    }
    for label, case in (("legacy", old_case), ("extended", extended_case)):
        errors = application_case_errors(case, schema)
        if errors:
            fail(f"{label} ApplicationCase failed JSON Schema validation: {'; '.join(errors)}")

    constrained_fields = ("requirements", "documents", "deadlines", "writing_tasks", "risks", "actions", "source_log")
    for field in constrained_fields:
        invalid_case = {**old_case, field: [{}]}
        if not application_case_errors(invalid_case, schema):
            fail(f"ApplicationCase {field} accepts an empty object")
    if not application_case_errors({**old_case, "supervisor_fit": {}}, schema):
        fail("ApplicationCase supervisor_fit accepts an empty object")
    for completed_workstream in sorted(expected_workstreams):
        statuses = {
            field: "complete" if field == completed_workstream else "not_started"
            for field in expected_workstreams
        }
        valid_complete = {**extended_case, "workstream_status": statuses}
        if completed_workstream == "programme_fit":
            valid_complete = {
                **valid_complete,
                "supervisor_fit": {
                    **extended_case["supervisor_fit"],
                    "research_fit": [{"topic": "Example verified research fit"}],
                },
            }
        elif completed_workstream == "writing":
            valid_complete = {
                **valid_complete,
                "writing_tasks": [{**extended_case["writing_tasks"][0], "status": "complete"}],
            }
        elif completed_workstream == "submission":
            valid_complete = {
                **valid_complete,
                "lifecycle_status": "submission_ready",
                "documents": [{**extended_case["documents"][0], "status": "verified"}],
                "actions": [{**extended_case["actions"][0], "status": "complete"}],
            }
        valid_errors = application_case_errors(valid_complete, schema)
        if valid_errors:
            fail(
                f"ApplicationCase rejects {completed_workstream} completion with current official provenance: "
                + "; ".join(valid_errors)
            )
        source_less_complete = {**valid_complete, "source_log": []}
        if not application_case_errors(source_less_complete, schema):
            fail(f"ApplicationCase allows {completed_workstream} completion without official provenance")
        stale_complete = {
            **valid_complete,
            "source_log": [{**source_record, "staleness": "stale"}],
        }
        if not application_case_errors(stale_complete, schema):
            fail(f"ApplicationCase allows {completed_workstream} completion from a stale official source")
        wrong_cycle_complete = {
            **valid_complete,
            "source_log": [{
                **source_record,
                "application_cycle": "2025-26",
                "current_cycle_match": False,
            }],
        }
        if not application_case_errors(wrong_cycle_complete, schema):
            fail(f"ApplicationCase allows {completed_workstream} completion from a wrong-cycle official source")
    requirements_statuses = {
        field: "complete" if field == "requirements" else "not_started"
        for field in expected_workstreams
    }
    requirements_without_entities = {
        key: value
        for key, value in {**extended_case, "workstream_status": requirements_statuses}.items()
        if key != "requirements"
    }
    if not application_case_errors(requirements_without_entities, schema):
        fail("ApplicationCase allows requirements completion without requirement entities")
    requirements_with_unknown = {
        **extended_case,
        "workstream_status": requirements_statuses,
        "requirements": [{**extended_case["requirements"][0], "status": "unknown"}],
    }
    if not application_case_errors(requirements_with_unknown, schema):
        fail("ApplicationCase allows requirements completion with an unknown requirement")
    blocking_workstream_cases = {
        "supervisor": {
            **extended_case,
            "supervisor_fit": {**extended_case["supervisor_fit"], "contact_requirement": "unknown"},
        },
        "programme_fit": extended_case,
        "writing": extended_case,
        "submission": extended_case,
    }
    for workstream, base_case in blocking_workstream_cases.items():
        candidate = {
            **base_case,
            "workstream_status": {
                field: "complete" if field == workstream else "not_started"
                for field in expected_workstreams
            },
        }
        if not application_case_errors(candidate, schema):
            fail(f"ApplicationCase allows {workstream} completion with blocking or missing state")
    materials_complete = {
        **extended_case,
        "workstream_status": {
            field: "complete" if field == "materials" else "not_started"
            for field in expected_workstreams
        },
    }
    if not application_case_errors({**materials_complete, "documents": []}, schema):
        fail("ApplicationCase allows materials completion without applicant document evidence")
    document_without_evidence = {
        **materials_complete,
        "documents": [{**extended_case["documents"][0], "evidence_ids": []}],
    }
    if not application_case_errors(document_without_evidence, schema):
        fail("ApplicationCase allows materials completion with empty applicant evidence_ids")
    materials_with_missing = {
        **materials_complete,
        "documents": [
            *extended_case["documents"],
            {
                "document_id": "doc_missing",
                "name": "Missing document",
                "status": "missing",
                "evidence_ids": [],
                "source_ids": ["source_programme"],
            },
        ],
    }
    if not application_case_errors(materials_with_missing, schema):
        fail("ApplicationCase allows materials completion while a document is missing")
    mislabelled_cycle = {
        **extended_case,
        "workstream_status": requirements_statuses,
        "source_log": [{
            **source_record,
            "application_cycle": "2025-26",
            "current_cycle_match": True,
        }],
    }
    if not application_case_errors(mislabelled_cycle, schema):
        fail("ApplicationCase trusts a false current_cycle_match flag")
    for section in ("requirements", "documents", "deadlines", "writing_tasks"):
        dangling = {
            **extended_case,
            section: [{**extended_case[section][0], "source_ids": ["missing_source"]}],
        }
        if not application_case_errors(dangling, schema):
            fail(f"ApplicationCase allows dangling source_ids in {section}")
    dangling_supervisor = {
        **extended_case,
        "supervisor_fit": {**extended_case["supervisor_fit"], "source_ids": ["missing_source"]},
    }
    if not application_case_errors(dangling_supervisor, schema):
        fail("ApplicationCase allows dangling source_ids in supervisor_fit")
    supervisor_without_sources = {
        **old_case,
        "supervisor_fit": {"contact_requirement": "recommended", "source_ids": []},
    }
    if not application_case_errors(supervisor_without_sources, schema):
        fail("ApplicationCase supervisor_fit allows empty source_ids")


def check_route_scripts(manifest: dict[str, Any]) -> None:
    plan = text(ROOT / "scripts" / "plan_workflow.py")
    questions = text(ROOT / "scripts" / "build_review_questions.py")
    for route in manifest.get("routes", []):
        if route not in plan:
            fail(f"route missing from plan_workflow.py: {route}")
        if route not in questions:
            fail(f"route missing from build_review_questions.py: {route}")
    for target in manifest.get("human_review_targets", []):
        if target not in questions and target not in plan:
            fail(f"human review target missing from route scripts: {target}")
    if '"default_output_language": "English"' not in plan:
        fail("route planner does not preserve the English default")
    for token in ('"matched"', '"needs_confirmation"', '"out_of_scope"'):
        if token not in plan:
            fail(f"route planner missing route status: {token}")
    if 'return "program_research"\n\n\ndef profile_gaps' in plan:
        fail("unresolved prompts still default to program_research")
    for token in (
        "writing-revision", "writing-coverage", "--batch-start", "next_batch_start",
        "--reviewed-question-id", "next_reviewed_question_ids", "single_sentence", "label_word_count",
    ):
        if token not in questions:
            fail(f"review question pagination or writing gate missing: {token}")


def check_tls_policy() -> None:
    scripts = [path for path in (ROOT / "scripts").glob("*.py") if path.name != Path(__file__).name]
    scanned = [
        *scripts,
        *(ROOT / "scripts").glob("*.mjs"),
    ]
    combined = "\n".join(text(path) for path in scanned)
    for token in (
        "_create_unverified_context", "CERT_NONE", "verify=False", "verify = False",
        "NODE_TLS_REJECT_UNAUTHORIZED", "rejectUnauthorized: false", "--insecure",
    ):
        if token in combined:
            fail(f"TLS verification bypass found: {token}")
    for path in scripts:
        body = text(path)
        if path.name.startswith("build_") and "urlopen(" in body and "TLS verification remains enabled" not in body:
            fail(f"network builder does not fail explicitly on verified TLS errors: {path.name}")


def check_programme_table_english_defaults() -> None:
    cleaner = text(ROOT / "scripts" / "clean_programme_workbooks.py")
    verifier = text(ROOT / "scripts" / "verify_programme_workbooks.py")
    reference = text(ROOT / "references" / "programme-table-cleaning.md")
    required = (
        '"Institution"',
        '"Programme"',
        '"Type / Delivery / Mode"',
        '"Course and Training Content"',
        '"Academic Requirements and Restrictions"',
        '"Official Source"',
        '"Accessed Date"',
        'MISSING = "Not stated on the official source"',
        "Processing note: 11-column official-source structure",
        "Knowledge topics:",
        "Degree and grades:",
    )
    for token in required:
        if token not in cleaner:
            fail(f"programme workbook cleaner missing English output contract: {token}")
    for token in required[:7]:
        if token not in verifier:
            fail(f"programme workbook verifier missing English output header: {token}")
    for token in ("`Institution`", "`Programme`", "`Official Source`", "`Accessed Date`"):
        if token not in reference:
            fail(f"programme table reference missing English canonical field: {token}")
    for generated_chinese in ('result = f"知识主题', 'ws.append(["处理说明', 'return "官网未列明。"'):
        if generated_chinese in cleaner:
            fail(f"programme workbook cleaner still emits Chinese default content: {generated_chinese}")


def check_catalogue_contract(manifest: dict[str, Any]) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_catalogues.py"), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"programme catalogue validation failed\n{proc.stdout}\n{proc.stderr}")
    report = json.loads(proc.stdout)
    if report.get("status") != "ok" or report.get("programme_count", 0) <= 0:
        fail("programme catalogue validator returned an invalid coverage report")
    if Path(manifest["catalogue_index"]) != Path("catalogues/index.json"):
        fail("catalogue_index must point to the Plugin-owned lazy-load index")

    builders = [
        *sorted((ROOT / "scripts").glob("build_*_catalogue.py")),
        ROOT / "scripts" / "build_us_singapore_catalogues.py",
        ROOT / "scripts" / "build_oxford_catalogue.mjs",
    ]
    builders = list(dict.fromkeys(path for path in builders if path.exists()))
    if len(builders) != 10:
        fail(f"expected 10 official-source catalogue builders, found {len(builders)}")
    for path in builders:
        body = text(path)
        if "web/src/data" in body or re.search(r'"web"\s*/\s*"src"\s*/\s*"data"', body):
            fail(f"catalogue builder still targets the legacy website: {path.name}")
        if "catalogue" not in body.lower():
            fail(f"catalogue builder does not target Plugin-owned catalogue data: {path.name}")


def check_shipped_data() -> None:
    for path in (ROOT / "tests" / "fixtures").glob("*.json"):
        fixture = read_json(path)
        if isinstance(fixture, dict):
            if any(value not in ("", [], {}) for value in fixture.get("profile", {}).values()):
                fail(f"fixture contains seeded applicant profile data: {path.relative_to(ROOT)}")
            if fixture.get("applicant") not in (None, {}):
                fail(f"fixture contains seeded applicant data: {path.relative_to(ROOT)}")
            if fixture.get("applicant_evidence") not in (None, []):
                fail(f"fixture contains seeded applicant evidence: {path.relative_to(ROOT)}")
            if fixture.get("evidence_records") not in (None, []):
                fail(f"fixture contains seeded evidence records: {path.relative_to(ROOT)}")

def check_plugin_and_agents(manifest: dict[str, Any]) -> None:
    plugin_path = ROOT / ".codex-plugin" / "plugin.json"
    if not plugin_path.exists():
        fail(".codex-plugin/plugin.json missing")
    plugin = read_json(plugin_path)
    if plugin.get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json must point skills to ./skills/")
    capabilities = read_json(ROOT / manifest["capability_manifest"])
    if plugin.get("version") != capabilities.get("plugin_version"):
        fail("plugin and capability manifest versions differ")
    if plugin.get("version") != "0.5.0":
        fail("University Application Skill version must be 0.5.0")
    agents = text(ROOT / "agents" / "openai.yaml")
    for token in (
        "$university-application-index", 'plugin_router_skill: "skills/university-application-index/SKILL.md"',
        '"visa-readiness"', 'default_output_language: "en"', 'programme_identity_catalogue: "catalogues/index.json',
    ):
        if token not in agents:
            fail(f"agents/openai.yaml metadata missing: {token}")


def run_self_tests() -> None:
    for script in (
        "scripts/plan_workflow.py",
        "scripts/build_review_questions.py",
        "scripts/validate_evidence.py",
        "scripts/publish_skill.py",
    ):
        proc = subprocess.run([sys.executable, str(ROOT / script), "--self-test"], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode != 0:
            fail(f"{script} --self-test failed\n{proc.stdout}\n{proc.stderr}")


def main() -> None:
    check_plugin_only_package()
    manifest = check_manifest()
    check_focused_skills(manifest)
    check_relative_resource_links()
    check_capability_manifest(manifest)
    check_shared_contracts()
    check_evidence_contract()
    check_workbook_contract()
    check_application_case_schema(manifest)
    check_route_scripts(manifest)
    check_tls_policy()
    check_programme_table_english_defaults()
    check_catalogue_contract(manifest)
    check_shipped_data()
    check_plugin_and_agents(manifest)
    run_self_tests()
    print("OK: skill contract checks passed")


if __name__ == "__main__":
    main()
