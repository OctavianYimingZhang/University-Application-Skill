#!/usr/bin/env python3
"""Validate Plugin-owned programme identity catalogues and emit coverage counts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOGUES = ROOT / "catalogues"
INDEX = CATALOGUES / "index.json"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
DEGREE_LEVELS = {"Undergraduate", "Postgraduate"}
MIGRATION_SOURCES = {
    "cambridgePrograms.ts",
    "edinburghPrograms.ts",
    "imperialPrograms.ts",
    "kclPrograms.ts",
    "lbsPrograms.ts",
    "lsePrograms.ts",
    "manchesterPrograms.ts",
    "oxfordPrograms.ts",
    "singaporePrograms.ts",
    "uclPrograms.ts",
    "usPrograms.ts",
    "warwickPrograms.ts",
}
EXPECTED_INDEX_KEYS = {
    "$schema",
    "contract",
    "version",
    "language",
    "verification_scope",
    "identity_status",
    "requirements_status",
    "updated_at",
    "programme_count",
    "programme_id_sha256",
    "institutions",
}
EXPECTED_CATALOGUE_KEYS = {
    "$schema",
    "contract",
    "version",
    "language",
    "institution",
    "catalogue_scope",
    "catalogue_provenance",
    "illustrative_examples",
    "programmes",
}
EXPECTED_INDEX_ENTRY_KEYS = {
    "id",
    "name",
    "short_name",
    "group",
    "region",
    "accessed_at",
    "identity_status",
    "requirements_status",
    "programme_count",
    "undergraduate_count",
    "postgraduate_count",
    "programme_id_sha256",
    "source_file",
    "migration_source",
}
REQUIRED_INSTITUTION_KEYS = {"id", "name", "short_name", "group", "region"}
OPTIONAL_INSTITUTION_KEYS = {"rank_note"}
EXPECTED_PROVENANCE_KEYS = {
    "accessed_at",
    "official_sources",
    "allowed_official_hosts",
    "extraction_note",
    "caveat",
    "migration_source",
}
EXPECTED_SOURCE_KEYS = {"degree_level", "title", "official_url", "coverage", "note"}
EXPECTED_EXAMPLE_KEYS = {"id", "name", "degree_level", "award", "official_url", "selection_status"}
REQUIRED_PROGRAMME_KEYS = {
    "id",
    "institution_id",
    "name",
    "degree_level",
    "award",
    "official_url",
    "identity_status",
    "requirements_status",
    "provenance",
}
OPTIONAL_PROGRAMME_KEYS = {"duration", "mode", "catalogue_status"}


def fail(message: str) -> None:
    raise ValueError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read valid JSON from {path.relative_to(ROOT)}: {exc}")


def sha256_ids(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()


def require_date(value: Any, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError:
        fail(f"{label} must be an ISO date: {value!r}")
    return value


def require_https(value: Any, label: str, allowed_hosts: set[str]) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be a URL string")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        fail(f"{label} must be a credential-free HTTPS URL: {value!r}")
    if parsed.hostname.lower() not in allowed_hosts:
        fail(f"{label} host is not in the institution allowlist: {value!r}")
    return value


def require_english_metadata(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"English catalogue metadata is empty: {label}")
    if CJK_RE.search(value):
        fail(f"Catalogue metadata must default to English: {label}")
    return value


def validate_catalogues() -> dict[str, Any]:
    for schema_name in ("catalogue-index-v1.schema.json", "institution-catalogue-v1.schema.json"):
        schema = read_json(CATALOGUES / "schemas" / schema_name)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail(f"Catalogue schema is not Draft 2020-12: {schema_name}")

    index = read_json(INDEX)
    if set(index) != EXPECTED_INDEX_KEYS:
        fail("Catalogue index fields drifted")
    expected_values = {
        "$schema": "schemas/catalogue-index-v1.schema.json",
        "contract": "ProgrammeCatalogueIndex",
        "version": 1,
        "language": "en",
        "verification_scope": "programme_identity_only",
        "identity_status": "official_source_listed",
        "requirements_status": "not_collected",
    }
    for key, expected in expected_values.items():
        if index.get(key) != expected:
            fail(f"Catalogue index {key} must be {expected!r}")
    require_date(index.get("updated_at"), "index.updated_at")
    if not SHA_RE.fullmatch(str(index.get("programme_id_sha256", ""))):
        fail("Catalogue index programme_id_sha256 is invalid")

    institutions = index.get("institutions")
    if not isinstance(institutions, list) or not institutions:
        fail("Catalogue index institutions must be a non-empty array")
    institution_ids: set[str] = set()
    programme_ids: set[str] = set()
    all_programme_ids: list[str] = []
    by_degree: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    by_institution: dict[str, dict[str, int]] = {}
    indexed_paths: set[Path] = set()

    for entry in institutions:
        if not isinstance(entry, dict) or set(entry) != EXPECTED_INDEX_ENTRY_KEYS:
            fail("Institution index entry fields drifted")
        institution_id = entry.get("id")
        if not isinstance(institution_id, str) or not ID_RE.fullmatch(institution_id):
            fail(f"Invalid institution ID: {institution_id!r}")
        if institution_id in institution_ids:
            fail(f"Duplicate institution ID: {institution_id}")
        institution_ids.add(institution_id)
        migration_source = entry.get("migration_source")
        if migration_source not in MIGRATION_SOURCES:
            fail(f"Unexpected migration source for {institution_id}: {migration_source!r}")
        if migration_source == "programs.ts":
            fail("Detailed placeholder programs.ts must never feed the identity catalogue")

        relative_path = entry.get("source_file")
        expected_path = f"institutions/{institution_id}.json"
        if relative_path != expected_path:
            fail(f"Index source_file must be {expected_path}: {relative_path!r}")
        catalogue_path = (CATALOGUES / relative_path).resolve()
        if CATALOGUES.resolve() not in catalogue_path.parents:
            fail(f"Catalogue path escapes catalogues/: {relative_path}")
        indexed_paths.add(catalogue_path)
        catalogue = read_json(catalogue_path)
        if set(catalogue) != EXPECTED_CATALOGUE_KEYS:
            fail(f"Institution catalogue fields drifted: {institution_id}")
        if catalogue.get("$schema") != "../schemas/institution-catalogue-v1.schema.json":
            fail(f"Institution catalogue schema reference drifted: {institution_id}")
        if catalogue.get("contract") != "InstitutionProgrammeCatalogue" or catalogue.get("version") != 1:
            fail(f"Institution catalogue contract/version drifted: {institution_id}")
        if catalogue.get("language") != "en":
            fail(f"Institution catalogue metadata must default to English: {institution_id}")

        institution = catalogue.get("institution", {})
        if not REQUIRED_INSTITUTION_KEYS <= set(institution) or set(institution) - REQUIRED_INSTITUTION_KEYS - OPTIONAL_INSTITUTION_KEYS:
            fail(f"Institution metadata fields drifted: {institution_id}")
        if institution.get("id") != institution_id:
            fail(f"Institution ID does not match filename/index: {institution_id}")
        for key in ("name", "short_name", "group", "region"):
            if entry.get(key) != institution.get(key):
                fail(f"Institution metadata drift between index and file: {institution_id}.{key}")
        for key in ("name", "short_name", "group", "region", "rank_note"):
            if key in institution:
                require_english_metadata(institution[key], f"{institution_id}.institution.{key}")
        if entry.get("identity_status") != "official_source_listed" or entry.get("requirements_status") != "not_collected":
            fail(f"Institution index verification scope drifted: {institution_id}")

        scope = catalogue.get("catalogue_scope", {})
        if scope != {
            "record_type": "programme_identity",
            "identity_status": "official_source_listed",
            "requirements_status": "not_collected",
            "placeholder_records_verified": False,
            "link_only_records_verified": False,
        }:
            fail(f"Identity-only verification scope drifted: {institution_id}")

        provenance = catalogue.get("catalogue_provenance", {})
        if set(provenance) != EXPECTED_PROVENANCE_KEYS:
            fail(f"Catalogue provenance fields drifted: {institution_id}")
        accessed_at = require_date(provenance.get("accessed_at"), f"{institution_id}.accessed_at")
        if entry.get("accessed_at") != accessed_at:
            fail(f"Access date drift between index and file: {institution_id}")
        if provenance.get("migration_source") != migration_source:
            fail(f"Migration source drift between index and file: {institution_id}")
        allowed_list = provenance.get("allowed_official_hosts")
        if not isinstance(allowed_list, list) or not allowed_list or len(allowed_list) != len(set(allowed_list)):
            fail(f"Official-host allowlist is empty or duplicated: {institution_id}")
        allowed_hosts = set(allowed_list)
        for allowed_host in allowed_hosts:
            if not re.fullmatch(r"[a-z0-9.-]+", allowed_host):
                fail(f"Invalid official-host allowlist entry: {institution_id} -> {allowed_host!r}")
        if allowed_list != sorted(allowed_list):
            fail(f"Official-host allowlist must be sorted: {institution_id}")
        sources = provenance.get("official_sources")
        if not isinstance(sources, list) or not sources:
            fail(f"Official catalogue sources are missing: {institution_id}")
        for position, source in enumerate(sources):
            if not isinstance(source, dict) or set(source) != EXPECTED_SOURCE_KEYS:
                fail(f"Official source fields drifted: {institution_id}[{position}]")
            if source.get("degree_level") not in DEGREE_LEVELS:
                fail(f"Invalid source degree level: {institution_id}[{position}]")
            require_https(source.get("official_url"), f"{institution_id}.official_sources[{position}]", allowed_hosts)
            for key in ("title", "coverage", "note"):
                require_english_metadata(source.get(key), f"{institution_id}.official_sources[{position}].{key}")
        for key in ("extraction_note", "caveat"):
            require_english_metadata(provenance.get(key), f"{institution_id}.{key}")

        examples = catalogue.get("illustrative_examples")
        if not isinstance(examples, list):
            fail(f"Illustrative examples must be an array: {institution_id}")
        for position, example in enumerate(examples):
            if not isinstance(example, dict) or set(example) != EXPECTED_EXAMPLE_KEYS:
                fail(f"Illustrative example fields drifted: {institution_id}[{position}]")
            if example.get("selection_status") != "illustrative_only":
                fail(f"Example cannot be treated as verified data: {institution_id}[{position}]")
            require_https(example.get("official_url"), f"{institution_id}.examples[{position}]", allowed_hosts)
            if example.get("degree_level") not in DEGREE_LEVELS:
                fail(f"Illustrative example degree level is invalid: {institution_id}[{position}]")
            for key in ("name", "award"):
                if not isinstance(example.get(key), str) or not example[key].strip():
                    fail(f"Illustrative example identity is empty: {institution_id}[{position}].{key}")

        programmes = catalogue.get("programmes")
        if not isinstance(programmes, list):
            fail(f"Programmes must be an array: {institution_id}")
        local_ids: list[str] = []
        local_degree: Counter[str] = Counter()
        for position, programme in enumerate(programmes):
            actual_keys = set(programme)
            if not REQUIRED_PROGRAMME_KEYS <= actual_keys or actual_keys - REQUIRED_PROGRAMME_KEYS - OPTIONAL_PROGRAMME_KEYS:
                fail(f"Programme fields drifted: {institution_id}[{position}]")
            programme_id = programme.get("id")
            if not isinstance(programme_id, str) or not ID_RE.fullmatch(programme_id):
                fail(f"Invalid stable programme ID: {institution_id}[{position}]")
            if programme_id in programme_ids:
                fail(f"Programme ID is not globally unique: {programme_id}")
            programme_ids.add(programme_id)
            local_ids.append(programme_id)
            all_programme_ids.append(programme_id)
            if programme.get("institution_id") != institution_id:
                fail(f"Programme institution_id mismatch: {programme_id}")
            level = programme.get("degree_level")
            if level not in DEGREE_LEVELS:
                fail(f"Invalid degree level: {programme_id}")
            local_degree[level] += 1
            by_degree[level] += 1
            for key in ("name", "award"):
                if not isinstance(programme.get(key), str) or not programme[key].strip():
                    fail(f"Programme identity field is empty: {programme_id}.{key}")
            if programme.get("identity_status") != "official_source_listed":
                fail(f"Programme identity status exceeds identity-only verification: {programme_id}")
            if programme.get("requirements_status") != "not_collected":
                fail(f"Programme requirements must remain uncollected: {programme_id}")
            official_url = require_https(programme.get("official_url"), f"{programme_id}.official_url", allowed_hosts)
            record_provenance = programme.get("provenance", {})
            if set(record_provenance) != {"source_url", "accessed_at", "source_note"}:
                fail(f"Programme provenance fields drifted: {programme_id}")
            if record_provenance.get("source_url") != official_url:
                fail(f"Programme source URL must match its official identity URL: {programme_id}")
            if require_date(record_provenance.get("accessed_at"), f"{programme_id}.accessed_at") != accessed_at:
                fail(f"Programme access date must match catalogue provenance: {programme_id}")
            if not isinstance(record_provenance.get("source_note"), str) or not record_provenance["source_note"].strip():
                fail(f"Programme source note is empty: {programme_id}")
            require_english_metadata(record_provenance.get("source_note"), f"{programme_id}.source_note")
            for key in ("duration", "mode", "catalogue_status"):
                if key in programme:
                    require_english_metadata(programme[key], f"{programme_id}.{key}")

        expected_local_hash = sha256_ids(local_ids)
        if entry.get("programme_id_sha256") != expected_local_hash:
            fail(f"Institution programme ID checksum drifted: {institution_id}")
        expected_counts = {
            "programme_count": len(programmes),
            "undergraduate_count": local_degree["Undergraduate"],
            "postgraduate_count": local_degree["Postgraduate"],
        }
        for key, expected in expected_counts.items():
            if entry.get(key) != expected:
                fail(f"Institution count drifted: {institution_id}.{key}")
        by_institution[institution_id] = {
            "total": len(programmes),
            "undergraduate": local_degree["Undergraduate"],
            "postgraduate": local_degree["Postgraduate"],
        }
        by_source[migration_source] += len(programmes)

    actual_paths = {path.resolve() for path in (CATALOGUES / "institutions").glob("*.json")}
    if actual_paths != indexed_paths:
        fail("Institution catalogue files and lazy-load index differ")
    if index.get("programme_count") != len(all_programme_ids):
        fail("Global programme count drifted")
    if index.get("programme_id_sha256") != sha256_ids(all_programme_ids):
        fail("Global stable programme ID checksum drifted")
    if index.get("updated_at") != max(entry["accessed_at"] for entry in institutions):
        fail("Catalogue index updated_at must equal the newest institution access date")
    if set(by_source) != MIGRATION_SOURCES:
        fail("All 12 identity source catalogues must remain represented")

    return {
        "status": "ok",
        "institution_count": len(institutions),
        "programme_count": len(all_programme_ids),
        "programme_id_sha256": sha256_ids(all_programme_ids),
        "by_degree": dict(sorted(by_degree.items())),
        "by_institution": by_institution,
        "by_migration_source": dict(sorted(by_source.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the full coverage report as JSON.")
    args = parser.parse_args()
    try:
        report = validate_catalogues()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "OK: validated "
            f"{report['programme_count']} programme identities across "
            f"{report['institution_count']} institutions"
        )


if __name__ == "__main__":
    main()
