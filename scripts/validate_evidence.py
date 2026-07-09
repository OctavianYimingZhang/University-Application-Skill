#!/usr/bin/env python3
"""Validate normalized applicant-evidence records and confirmation invariants."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CONFIRMATION_STATUSES = {"unconfirmed", "explicitly_confirmed"}
SOURCE_AVAILABILITY_STATUSES = {"available", "unavailable", "unknown"}
FACT_VERIFICATION_STATUSES = {"unverified", "verified", "conflicted"}
COMPLETENESS_STATUSES = {"placeholder", "partial", "complete"}
STALENESS_STATUSES = {"fresh", "stale", "unknown"}
REQUIRED_FIELDS = {
    "evidence_id", "value", "source", "evidence_date", "confirmation_status", "confirmed_at",
    "source_availability", "fact_verification", "completeness", "application_cycle", "accessed_at", "staleness",
}

PLACEHOLDERS = {
    "-",
    "n/a",
    "na",
    "none",
    "not applicable",
    "not available",
    "not confirmed",
    "not provided",
    "placeholder",
    "pending",
    "recorded in session",
    "source required",
    "tbc",
    "tbd",
    "todo",
    "to be confirmed",
    "unknown",
}
PLACEHOLDER_HOSTS = {"localhost"}


def normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_placeholder(value: Any) -> bool:
    text = normalized_text(value).lower()
    return not text or text in PLACEHOLDERS or text.startswith("placeholder:")


def is_real_source_url(value: Any) -> bool:
    text = normalized_text(value)
    if is_placeholder(text):
        return False
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if host in PLACEHOLDER_HOSTS or host.startswith("example.") or host.endswith((".example", ".test", ".local")):
        return False
    try:
        if not ip_address(host).is_global:
            return False
    except ValueError:
        pass
    return "." in host


def is_link_only(value: Any) -> bool:
    text = normalized_text(value)
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and " " not in text


def is_iso_date_or_datetime(value: Any) -> bool:
    text = normalized_text(value)
    if not text:
        return False
    try:
        if "T" in text or " " in text:
            datetime.fromisoformat(text.replace("Z", "+00:00"))
        else:
            date.fromisoformat(text)
    except ValueError:
        return False
    return True


def is_iso_datetime(value: Any) -> bool:
    text = normalized_text(value)
    if "T" not in text and " " not in text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_evidence_record(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["record must be an object"]

    errors: list[str] = []
    missing_fields = sorted(REQUIRED_FIELDS - set(record))
    if missing_fields:
        errors.append("missing fields: " + ", ".join(missing_fields))
    extra_fields = sorted(set(record) - REQUIRED_FIELDS)
    if extra_fields:
        errors.append("unexpected fields: " + ", ".join(extra_fields))
    if is_placeholder(record.get("evidence_id")):
        errors.append("evidence_id must be non-empty and non-placeholder")

    value = record.get("value")
    if is_placeholder(value):
        errors.append("value must be non-empty and non-placeholder")
    elif is_link_only(value):
        errors.append("value must contain evidence, not only a link")

    source = record.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        missing_source_fields = sorted({"url", "title", "publisher"} - set(source))
        if missing_source_fields:
            errors.append("missing source fields: " + ", ".join(missing_source_fields))
        extra_source_fields = sorted(set(source) - {"url", "title", "publisher"})
        if extra_source_fields:
            errors.append("unexpected source fields: " + ", ".join(extra_source_fields))
        if not is_real_source_url(source.get("url")):
            errors.append("source.url must be a real non-placeholder URL")
        for field in ("title", "publisher"):
            if is_placeholder(source.get(field)):
                errors.append(f"source.{field} must be non-empty and non-placeholder")

    if not is_iso_date_or_datetime(record.get("evidence_date")):
        errors.append("evidence_date must be an ISO date or date-time")

    confirmation_status = record.get("confirmation_status")
    if confirmation_status not in CONFIRMATION_STATUSES:
        errors.append("confirmation_status must be unconfirmed or explicitly_confirmed")
    confirmed_at = record.get("confirmed_at")
    if confirmation_status == "explicitly_confirmed" and not is_iso_datetime(confirmed_at):
        errors.append("confirmed_at must be an ISO date-time for explicitly confirmed evidence")
    if confirmation_status == "unconfirmed" and normalized_text(confirmed_at):
        errors.append("confirmed_at must be empty for unconfirmed evidence")

    enum_fields = {
        "source_availability": SOURCE_AVAILABILITY_STATUSES,
        "fact_verification": FACT_VERIFICATION_STATUSES,
        "completeness": COMPLETENESS_STATUSES,
        "staleness": STALENESS_STATUSES,
    }
    for field, allowed in enum_fields.items():
        if record.get(field) not in allowed:
            errors.append(f"{field} must be one of: {', '.join(sorted(allowed))}")

    if is_placeholder(record.get("application_cycle")):
        errors.append("application_cycle must be non-empty and non-placeholder")
    if not is_iso_date_or_datetime(record.get("accessed_at")):
        errors.append("accessed_at must be an ISO date or date-time")
    return errors


def evidence_passes(record: Any) -> bool:
    if validate_evidence_record(record):
        return False
    return (
        not is_placeholder(record.get("value"))
        and not is_link_only(record.get("value"))
        and is_real_source_url(record["source"].get("url"))
        and is_iso_date_or_datetime(record.get("evidence_date"))
        and record.get("confirmation_status") == "explicitly_confirmed"
        and record.get("fact_verification") == "verified"
        and record.get("completeness") == "complete"
    )


def records_from_payload(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "evidence_id" in payload:
        return [payload]
    if isinstance(payload, dict):
        for key in ("evidence_records", "applicant_evidence"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise ValueError("payload must be an evidence record, a list, or contain evidence_records/applicant_evidence")


def validate_payload(payload: Any, *, require_pass: bool = False) -> list[dict[str, Any]]:
    results = []
    records = records_from_payload(payload)
    if require_pass and not records:
        return [{"index": None, "evidence_id": None, "passes": False, "errors": ["at least one evidence record is required"]}]
    for index, record in enumerate(records):
        errors = validate_evidence_record(record)
        passed = evidence_passes(record)
        if require_pass and not passed and not errors:
            errors.append("record does not satisfy the evidence passing invariant")
        evidence_id = record.get("evidence_id") if isinstance(record, dict) else None
        results.append({"index": index, "evidence_id": evidence_id, "passes": passed, "errors": errors})
    return results


def self_test() -> None:
    valid = {
        "evidence_id": "contract-test-record",
        "value": "Official guidance describes the Student visa route.",
        "source": {
            "url": "https://www.gov.uk/student-visa",
            "title": "Student visa",
            "publisher": "UK Government",
        },
        "evidence_date": "2026-07-01",
        "confirmation_status": "explicitly_confirmed",
        "confirmed_at": "2026-07-01T12:00:00+00:00",
        "source_availability": "available",
        "fact_verification": "verified",
        "completeness": "complete",
        "application_cycle": "2026-27",
        "accessed_at": "2026-07-01T11:30:00+00:00",
        "staleness": "fresh",
    }
    assert evidence_passes(valid)
    for patch in (
        {"value": ""},
        {"value": "TBD"},
        {"value": "https://www.gov.uk/student-visa"},
        {"source": {**valid["source"], "url": "https://invalid.test/evidence"}},
        {"source": {**valid["source"], "url": "http://127.0.0.1/evidence"}},
        {"evidence_date": ""},
        {"confirmation_status": "unconfirmed", "confirmed_at": None},
        {"fact_verification": "unverified"},
        {"completeness": "placeholder"},
    ):
        candidate = {**valid, **patch}
        assert not evidence_passes(candidate), patch
    stale = {**valid, "source_availability": "unavailable", "staleness": "stale"}
    assert evidence_passes(stale), "availability and staleness must remain separate from confirmation"
    assert validate_payload([], require_pass=True)[0]["errors"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate normalized applicant-evidence records.")
    parser.add_argument("evidence_json", type=Path, nargs="?")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("OK: evidence contract self-test passed")
        return
    if not args.evidence_json:
        parser.error("evidence_json is required unless --self-test is used")
    payload = json.loads(args.evidence_json.read_text(encoding="utf-8"))
    try:
        results = validate_payload(payload, require_pass=args.require_pass)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({"records": results}, ensure_ascii=False, indent=2))
    if any(item["errors"] for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
