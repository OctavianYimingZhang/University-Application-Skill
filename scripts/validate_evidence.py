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
SOURCE_TYPES = {"public_url", "local_document", "user_confirmation"}
FACT_CLASSES = {"mutable_official_fact", "applicant_personal_fact"}
EVIDENCE_PURPOSES = {"writing", "applicant_comparison", "official_requirement", "material_document", "submission"}
REQUIRED_FIELDS = {
    "evidence_id", "value", "source", "evidence_date", "confirmation_status", "confirmed_at",
    "source_availability", "fact_verification", "completeness", "application_cycle", "accessed_at", "staleness",
}
OPTIONAL_FIELDS = {"fact_class", "evidence_use"}

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


def source_type(source: Any) -> str:
    if not isinstance(source, dict):
        return ""
    # Existing records predate source.type and remain public-URL records.
    if "type" not in source:
        return "public_url"
    return normalized_text(source.get("type"))


def looks_like_mutable_official_fact(record: dict[str, Any]) -> bool:
    """Conservatively identify unclassified records that plainly state mutable official rules."""
    raw_value = normalized_text(record.get("value"))
    value = raw_value.casefold()
    direct_official_claim = bool(re.search(
        r"\b(?:official guidance|applications? deadlines?|admissions? deadlines?|deadline\s*(?:is|:)|"
        r"applications? fees?|tuition fees?|tuition\s*(?:is|:)|"
        r"(?:entry|admissions?|language) requirements?|documents? required|required documents?|"
        r"word limits?|character limits?|application cycles?|supervisor contact|ai (?:use )?polic(?:y|ies))\b"
        r"|(?:申请截止|截止日期|申请费|学费|入学要求|申请要求|语言要求|需要提交|字数限制|字符限制|"
        r"联系导师要求|AI使用政策|人工智能使用政策)",
        value,
    ))
    if direct_official_claim:
        return True

    programme_or_institution = bool(
        re.search(r"\b(?:programme|program|course|university|college|institute|department|school)\b", value)
        or re.search(r"[\u4e00-\u9fff]{2,20}(?:大学|学院|研究所|项目|专业|课程)", raw_value)
        or re.search(
            r"\b[A-Z][A-Za-z&.'-]*(?:\s+(?:of|the|and|[A-Z][A-Za-z&.'-]*)){0,5}\s+"
            r"(?:requires?|accepts?|allows?|charges?|opens?|closes?|sets?|prohibits?)\b",
            raw_value,
        )
    )
    mutable_admissions_claim = bool(re.search(
        r"\b(?:requires?|mandates?)\b.{0,80}\b(?:applications?|documents?|statements?|essays?|"
        r"references?|scores?|supervisors?|contact|fees?|deposit|interviews?)\b"
        r"|\baccepts?\s+applications?\s+(?:until|through|from|between|before|after|by|for)\b"
        r"|\bapplications?\s+(?:open|opens|close|closes|must|should|may|are due|is due)\b"
        r"|\b(?:charges?|costs?|fees?|tuition)\b.{0,40}(?:\b\d|\bgbp\b|\busd\b|£|\$|€)"
        r"|\b(?:essay|statement|application)\s+prompts?\b"
        r"|\b(?:contact|email)\b.{0,40}\bsupervisors?\b"
        r"|(?:要求|必须|需要).{0,40}(?:申请|材料|文书|推荐信|成绩|导师|联系|费用|面试)"
        r"|(?:接受申请|开放申请|申请开放|申请关闭|停止申请).{0,30}(?:截至|直到|日期|时间|前|后)?",
        value,
    ))
    return programme_or_institution and mutable_admissions_claim


def validate_evidence_record(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["record must be an object"]

    errors: list[str] = []
    missing_fields = sorted(REQUIRED_FIELDS - set(record))
    if missing_fields:
        errors.append("missing fields: " + ", ".join(missing_fields))
    extra_fields = sorted(set(record) - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if extra_fields:
        errors.append("unexpected fields: " + ", ".join(extra_fields))
    if is_placeholder(record.get("evidence_id")):
        errors.append("evidence_id must be non-empty and non-placeholder")
    if record.get("fact_class") is not None and record.get("fact_class") not in FACT_CLASSES:
        errors.append("fact_class must be mutable_official_fact or applicant_personal_fact")
    if record.get("evidence_use") is not None and record.get("evidence_use") not in EVIDENCE_PURPOSES:
        errors.append("evidence_use is not supported")

    value = record.get("value")
    if is_placeholder(value):
        errors.append("value must be non-empty and non-placeholder")
    elif is_link_only(value):
        errors.append("value must contain evidence, not only a link")

    source = record.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        kind = source_type(source)
        if kind not in SOURCE_TYPES:
            errors.append("source.type must be public_url, local_document, or user_confirmation")
        allowed_source_fields = {"type", "url", "title", "publisher", "opaque_local_ref", "confirmed_by"}
        extra_source_fields = sorted(set(source) - allowed_source_fields)
        if extra_source_fields:
            errors.append("unexpected source fields: " + ", ".join(extra_source_fields))
        if kind == "public_url":
            missing_source_fields = sorted({"url", "title", "publisher"} - set(source))
            if missing_source_fields:
                errors.append("missing public source fields: " + ", ".join(missing_source_fields))
            if not is_real_source_url(source.get("url")):
                errors.append("source.url must be a real non-placeholder URL for public_url evidence")
            for field in ("title", "publisher"):
                if is_placeholder(source.get(field)):
                    errors.append(f"source.{field} must be non-empty and non-placeholder")
        elif kind == "local_document":
            if is_placeholder(source.get("opaque_local_ref")):
                errors.append("source.opaque_local_ref must identify the private local or uploaded document")
            if is_placeholder(source.get("title")):
                errors.append("source.title must identify the local document")
            if normalized_text(source.get("url")) and not is_real_source_url(source.get("url")):
                errors.append("source.url must be real when a local_document also records a URL")
        elif kind == "user_confirmation":
            if is_placeholder(source.get("confirmed_by")):
                errors.append("source.confirmed_by must identify the confirming user")
            if is_placeholder(source.get("title")):
                errors.append("source.title must identify the confirmation context")

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


def effective_fact_class(record: dict[str, Any], purpose: str) -> str:
    if record.get("evidence_use") == "official_requirement" or looks_like_mutable_official_fact(record):
        return "mutable_official_fact"
    explicit = record.get("fact_class")
    if explicit in FACT_CLASSES:
        return str(explicit)
    if source_type(record.get("source")) in {"local_document", "user_confirmation"}:
        return "applicant_personal_fact"
    # Legacy records did not declare a fact class. Preserve their applicant-evidence
    # behavior unless the caller explicitly evaluates an official requirement.
    return "mutable_official_fact" if purpose == "official_requirement" else "applicant_personal_fact"


def evidence_passes(
    record: Any,
    purpose: str = "writing",
    *,
    current_cycle: str | None = None,
) -> bool:
    if purpose not in EVIDENCE_PURPOSES:
        raise ValueError(f"unsupported evidence purpose: {purpose}")
    if validate_evidence_record(record):
        return False
    kind = source_type(record.get("source"))
    fact_class = effective_fact_class(record, purpose)
    base_passes = (
        not is_placeholder(record.get("value"))
        and not is_link_only(record.get("value"))
        and is_iso_date_or_datetime(record.get("evidence_date"))
        and record.get("confirmation_status") == "explicitly_confirmed"
        and record.get("fact_verification") == "verified"
        and record.get("completeness") == "complete"
    )
    if not base_passes:
        return False
    if purpose == "official_requirement":
        if fact_class != "mutable_official_fact":
            return False
        return (
            kind == "public_url"
            and record.get("source_availability") == "available"
            and record.get("staleness") == "fresh"
            and current_cycle is not None
            and normalized_text(record.get("application_cycle")) == normalized_text(current_cycle)
        )
    if purpose == "material_document":
        return (
            fact_class == "applicant_personal_fact"
            and kind == "local_document"
            and record.get("source_availability") == "available"
        )
    if fact_class == "mutable_official_fact":
        return (
            kind == "public_url"
            and record.get("source_availability") == "available"
            and record.get("staleness") == "fresh"
            and current_cycle is not None
            and normalized_text(record.get("application_cycle")) == normalized_text(current_cycle)
        )
    if purpose == "submission":
        return kind in {"public_url", "local_document"} and record.get("source_availability") == "available"
    return kind in SOURCE_TYPES


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


def validate_payload(
    payload: Any,
    *,
    require_pass: bool = False,
    purpose: str = "writing",
    current_cycle: str | None = None,
) -> list[dict[str, Any]]:
    results = []
    records = records_from_payload(payload)
    if require_pass and not records:
        return [{"index": None, "evidence_id": None, "passes": False, "errors": ["at least one evidence record is required"]}]
    for index, record in enumerate(records):
        errors = validate_evidence_record(record)
        requested_purpose = record.get("evidence_use") if isinstance(record, dict) else None
        record_purpose = (
            purpose
            if purpose in {"official_requirement", "material_document", "submission"}
            else requested_purpose if requested_purpose in EVIDENCE_PURPOSES else purpose
        )
        passed = evidence_passes(record, purpose=record_purpose, current_cycle=current_cycle)
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
    assert evidence_passes(valid, purpose="official_requirement", current_cycle="2026-27")
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
        assert not evidence_passes(candidate, purpose="official_requirement", current_cycle="2026-27"), patch
    stale = {**valid, "source_availability": "unavailable", "staleness": "stale"}
    legacy_applicant = {
        **valid,
        "value": "The applicant completed a named public research project.",
        "source": {
            "url": "https://www.ox.ac.uk/students/academic/guidance/skills",
            "title": "Applicant research project page",
            "publisher": "University of Oxford",
        },
    }
    stale_legacy_applicant = {
        **legacy_applicant,
        "source_availability": "unavailable",
        "staleness": "stale",
    }
    assert evidence_passes(legacy_applicant)
    assert evidence_passes(stale_legacy_applicant), "legacy applicant-evidence behavior must remain compatible"
    local_document = {
        **valid,
        "evidence_id": "local-cv-record",
        "value": "The applicant completed a named laboratory placement.",
        "source": {
            "type": "local_document",
            "opaque_local_ref": "local://cv/current",
            "title": "Applicant CV",
        },
    }
    user_confirmation = {
        **valid,
        "evidence_id": "user-confirmed-record",
        "value": "The applicant confirms that this experience is accurate.",
        "source": {
            "type": "user_confirmation",
            "confirmed_by": "current_user",
            "title": "Explicit confirmation in the current task",
        },
    }
    local_document["fact_class"] = "applicant_personal_fact"
    user_confirmation["fact_class"] = "applicant_personal_fact"
    assert evidence_passes(local_document, purpose="writing")
    assert evidence_passes(local_document, purpose="material_document")
    assert evidence_passes(local_document, purpose="submission")
    assert not evidence_passes(local_document, purpose="official_requirement")
    assert evidence_passes(user_confirmation, purpose="writing")
    assert not evidence_passes(user_confirmation, purpose="submission")
    assert not evidence_passes(user_confirmation, purpose="official_requirement")
    unavailable_local_document = {**local_document, "source_availability": "unavailable"}
    assert not evidence_passes(unavailable_local_document, purpose="material_document")
    assert not evidence_passes(unavailable_local_document, purpose="submission")
    assert evidence_passes(local_document, purpose="applicant_comparison")
    assert evidence_passes(user_confirmation, purpose="applicant_comparison")
    assert evidence_passes(valid, purpose="official_requirement", current_cycle="2026-27")
    assert not evidence_passes(valid, purpose="official_requirement")
    assert not evidence_passes(stale, purpose="official_requirement", current_cycle="2026-27")
    unavailable = {**valid, "source_availability": "unavailable"}
    assert not evidence_passes(unavailable, purpose="official_requirement", current_cycle="2026-27")
    assert not evidence_passes(valid, purpose="official_requirement", current_cycle="2027-28")
    explicit_official = {**valid, "fact_class": "mutable_official_fact"}
    assert evidence_passes(explicit_official, purpose="writing", current_cycle="2026-27")
    assert not evidence_passes(explicit_official, purpose="writing", current_cycle="2027-28")
    unclassified_user_official = {
        **valid,
        "source": {
            "type": "user_confirmation",
            "confirmed_by": "current_user",
            "title": "Unverified programme claim in the current task",
        },
    }
    assert not evidence_passes(unclassified_user_official, purpose="writing", current_cycle="2026-27")
    unclassified_oxford_deadline = {
        **unclassified_user_official,
        "value": "Oxford accepts applications until 1 December.",
    }
    assert not evidence_passes(unclassified_oxford_deadline, purpose="writing", current_cycle="2026-27")
    disguised_oxford_deadline = {
        **unclassified_oxford_deadline,
        "fact_class": "applicant_personal_fact",
        "evidence_use": "writing",
    }
    assert not evidence_passes(disguised_oxford_deadline, purpose="writing", current_cycle="2026-27")
    caller_purpose_downgrade = {**user_confirmation, "evidence_use": "writing"}
    assert validate_payload(
        caller_purpose_downgrade,
        purpose="official_requirement",
        current_cycle="2026-27",
    )[0]["passes"] is False
    synthetic_official_cv_requirement = {
        "evidence_id": "synthetic_official_cv_requirement",
        "value": "The programme requires a curriculum vitae as an application document.",
        "fact_class": "mutable_official_fact",
        "evidence_use": "official_requirement",
        "source": {
            "type": "public_url",
            "url": "https://www.ox.ac.uk/this-path-is-intentionally-not-verified-by-the-test",
            "title": "Synthetic official programme record",
            "publisher": "University of Oxford",
        },
        "evidence_date": "2026-07-16",
        "confirmation_status": "explicitly_confirmed",
        "confirmed_at": "2026-07-16T10:00:00+08:00",
        "source_availability": "available",
        "fact_verification": "verified",
        "completeness": "complete",
        "application_cycle": "2027-28",
        "accessed_at": "2026-07-16T10:00:00+08:00",
        "staleness": "fresh",
    }
    assert not evidence_passes(
        synthetic_official_cv_requirement,
        purpose="material_document",
        current_cycle="2027-28",
    )
    assert validate_payload(
        synthetic_official_cv_requirement,
        require_pass=True,
        purpose="material_document",
        current_cycle="2027-28",
    )[0]["passes"] is False
    assert evidence_passes(
        synthetic_official_cv_requirement,
        purpose="official_requirement",
        current_cycle="2027-28",
    )
    assert evidence_passes(
        synthetic_official_cv_requirement,
        purpose="submission",
        current_cycle="2027-28",
    )
    explicit_empty_type = {**valid, "source": {**valid["source"], "type": ""}}
    assert validate_evidence_record(explicit_empty_type)
    assert validate_payload([], require_pass=True)[0]["errors"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate normalized applicant-evidence records.")
    parser.add_argument("evidence_json", type=Path, nargs="?")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--purpose", choices=sorted(EVIDENCE_PURPOSES), default="writing")
    parser.add_argument("--current-cycle")
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
        results = validate_payload(
            payload,
            require_pass=args.require_pass,
            purpose=args.purpose,
            current_cycle=args.current_cycle,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({"records": results}, ensure_ascii=False, indent=2))
    if any(item["errors"] for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
