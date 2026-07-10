#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    return manifest


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
    ):
        if token not in evidence_script:
            fail(f"evidence validator status missing: {token}")


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


def check_tls_policy() -> None:
    scripts = [path for path in (ROOT / "scripts").glob("*.py") if path.name != Path(__file__).name]
    scanned = [
        *scripts,
        *(ROOT / "scripts").glob("*.mjs"),
        *(ROOT / "web" / "src").glob("*.ts"),
        *(ROOT / "web" / "src").glob("*.tsx"),
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

    app_path = ROOT / "web" / "src" / "App.tsx"
    if app_path.exists():
        app = text(app_path)
        narrative = app.split("const narrativeOptions", 1)[-1].split("function fileExtension", 1)[0]
        if re.search(r"evidence:\s*\[(?!\s*\])", narrative):
            fail("narrative options must not ship with seeded applicant evidence")
        checklist_actions = app.split("const recordGlobal", 1)[-1].split("return (", 1)[0]
        if re.search(r'status:\s*"Complete".*check:\s*"Pass"', checklist_actions, flags=re.DOTALL):
            fail("checklist action can pass placeholder evidence")

        combined_web = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (ROOT / "web" / "src").rglob("*")
            if path.is_file()
        )
        for phrase in ("acceptance probability", "chance score", "safe/match/reach"):
            if phrase in combined_web.lower():
                fail(f"banned probability wording found in web source: {phrase}")

    memory_page = ROOT / "web" / "public" / "memory.html"
    if memory_page.exists():
        memory_html = text(memory_page)
        if "user_confirmed: true" in memory_html or 'confirmation_status: "explicitly_confirmed"' in memory_html:
            fail("Memory Studio must not auto-confirm exported memory as applicant evidence")


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
    manifest = check_manifest()
    check_focused_skills(manifest)
    check_relative_resource_links()
    check_capability_manifest(manifest)
    check_shared_contracts()
    check_evidence_contract()
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
