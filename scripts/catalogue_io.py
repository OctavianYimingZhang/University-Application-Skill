#!/usr/bin/env python3
"""Write and index Plugin-owned programme identity catalogues."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
DEGREE_LEVELS = {"Undergraduate", "Postgraduate"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _https_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"Official catalogue URL must use HTTPS: {value!r}")
    return urlunsplit(parsed)


def _host_allowed(url: str, allowed_hosts: set[str]) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return host in allowed_hosts


def _sha256_ids(ids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()


def normalise_programme(
    row: dict[str, Any],
    *,
    institution_id: str,
    accessed_at: str,
    allowed_hosts: set[str],
) -> dict[str, Any]:
    required = {"id", "name", "level", "award", "url", "note"}
    missing = sorted(required - set(row))
    if missing:
        raise ValueError(f"Catalogue row is missing fields: {', '.join(missing)}")

    programme_id = str(row["id"]).strip()
    if not ID_RE.fullmatch(programme_id):
        raise ValueError(f"Invalid stable programme ID: {programme_id!r}")
    level = str(row["level"]).strip()
    if level not in DEGREE_LEVELS:
        raise ValueError(f"Invalid degree level for {programme_id}: {level!r}")
    official_url = _https_url(str(row["url"]))
    if not _host_allowed(official_url, allowed_hosts):
        raise ValueError(f"Official URL host is not allowlisted for {institution_id}: {official_url}")
    date.fromisoformat(accessed_at)

    record: dict[str, Any] = {
        "id": programme_id,
        "institution_id": institution_id,
        "name": str(row["name"]).strip(),
        "degree_level": level,
        "award": str(row["award"]).strip(),
        "official_url": official_url,
        "identity_status": "official_source_listed",
        "requirements_status": "not_collected",
        "provenance": {
            "source_url": official_url,
            "accessed_at": accessed_at,
            "source_note": str(row["note"]).strip(),
        },
    }
    optional_map = {
        "duration": "duration",
        "mode": "mode",
        "status": "catalogue_status",
    }
    for source_key, output_key in optional_map.items():
        value = str(row.get(source_key, "")).strip()
        if value and not CJK_RE.search(value):
            record[output_key] = value
    if not record["name"] or not record["award"] or not record["provenance"]["source_note"]:
        raise ValueError(f"Catalogue row contains an empty identity field: {programme_id}")
    return record


def rebuild_index(root: Path) -> Path:
    index_path = root / "catalogues" / "index.json"
    index = _read_json(index_path)
    all_ids: list[str] = []
    updated_dates: list[str] = []

    for entry in index["institutions"]:
        catalogue_path = root / "catalogues" / entry["source_file"]
        catalogue = _read_json(catalogue_path)
        programmes = catalogue["programmes"]
        ids = [item["id"] for item in programmes]
        accessed_at = catalogue["catalogue_provenance"]["accessed_at"]
        entry.update(
            {
                "accessed_at": accessed_at,
                "identity_status": "official_source_listed",
                "requirements_status": "not_collected",
                "programme_count": len(programmes),
                "undergraduate_count": sum(item["degree_level"] == "Undergraduate" for item in programmes),
                "postgraduate_count": sum(item["degree_level"] == "Postgraduate" for item in programmes),
                "programme_id_sha256": _sha256_ids(ids),
            }
        )
        all_ids.extend(ids)
        updated_dates.append(accessed_at)

    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Programme IDs must be globally unique before the index can be rebuilt")
    index["updated_at"] = max(updated_dates)
    index["programme_count"] = len(all_ids)
    index["programme_id_sha256"] = _sha256_ids(all_ids)
    _write_json(index_path, index)
    return index_path


def write_programmes(
    root: Path,
    institution_id: str,
    rows: list[dict[str, Any]],
    accessed_at: str,
    *,
    refresh_index: bool = True,
) -> Path:
    path = root / "catalogues" / "institutions" / f"{institution_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Institution catalogue metadata is missing: {path}")
    catalogue = _read_json(path)
    if catalogue["institution"]["id"] != institution_id:
        raise ValueError(f"Institution catalogue ID mismatch: {path}")
    allowed_hosts = set(catalogue["catalogue_provenance"]["allowed_official_hosts"])
    programmes = [
        normalise_programme(
            row,
            institution_id=institution_id,
            accessed_at=accessed_at,
            allowed_hosts=allowed_hosts,
        )
        for row in rows
    ]
    ids = [item["id"] for item in programmes]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate programme IDs in {institution_id} catalogue")
    catalogue["catalogue_provenance"]["accessed_at"] = accessed_at
    catalogue["programmes"] = programmes
    _write_json(path, catalogue)
    if refresh_index:
        rebuild_index(root)
    return path
