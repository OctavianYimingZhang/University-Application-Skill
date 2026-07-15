#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from plan_workflow import (
    ROUTE_LABELS,
    build_plan,
    normalize_prompt,
    prompt_has_any,
    explicit_materials_readiness_request,
    supervisor_fit_requested,
)


BATCH_SIZE = 3
RESOLVED_DECISION_STATUSES = {
    "explicitly_confirmed",
    "confirmed",
    "adjusted",
    "rejected",
    "superseded",
    "not_applicable",
}
BLOCKING_DECISION_STATUSES = {"pending", "unconfirmed", "unresolved", "missing", "conflicted", "conflict"}
RESOLVED_COVERAGE_STATUSES = {
    "complete",
    "implemented",
    "covered",
    "rejected",
    "superseded",
    "not_applicable",
}
BLOCKING_COVERAGE_STATUSES = {"pending", "missing", "unresolved", "conflicted", "conflict"}
NO_LOCATION_COVERAGE_STATUSES = {"rejected", "superseded", "not_applicable"}
DECISION_STATUS_FIELDS = ("confirmation_status", "decision_status", "status")
COVERAGE_STATUS_FIELDS = ("coverage_status", "coverage_state")
CONFLICT_FIELDS = ("conflicts_with", "conflict_with")
IMPLEMENTATION_FIELDS = ("implementation_locations", "implementation_location")


def single_sentence(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or value.strip()[-1] not in ".!?":
        return False
    return len(re.findall(r"[.!?](?=\s|$)", value.strip())) == 1


def label_word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|[\u4e00-\u9fff]+", value))


def option(label: str, description: str) -> dict[str, str]:
    if not 1 <= label_word_count(label) <= 5:
        raise ValueError(f"option label must contain 1-5 words: {label!r}")
    if not single_sentence(description):
        raise ValueError(f"option description must be one sentence: {description!r}")
    return {"label": label, "description": description}


def question(header: str, question_id: str, prompt: str, options: list[dict[str, str]]) -> dict[str, Any]:
    if not isinstance(header, str) or not header.strip() or len(header) > 12:
        raise ValueError(f"question header must contain 1-12 characters: {header!r}")
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("question id must be non-empty text")
    if not single_sentence(prompt):
        raise ValueError(f"question must be one sentence: {prompt!r}")
    if not 2 <= len(options) <= 3:
        raise ValueError("question must contain 2-3 options")
    return {
        "header": header,
        "id": question_id,
        "question": prompt,
        "options": options,
    }


def slug(value: Any, fallback: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")
    return normalized or fallback


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def paged_payload(
    questions: list[dict[str, Any]],
    batch_start: int,
    reviewed_question_ids: list[str] | None = None,
) -> dict[str, Any]:
    if not questions:
        return {
            "questions": [],
            "request_user_input_required": False,
            "continuation": {
                "batch_start": 0,
                "requested_batch_start": batch_start,
                "batch_size": 0,
                "total_questions": 0,
                "remaining_questions": 0,
                "has_more": False,
                "next_batch_start": None,
                "cursor_applied": reviewed_question_ids is not None,
                "reviewed_question_ids": list(dict.fromkeys(reviewed_question_ids or [])),
                "batch_question_ids": [],
                "next_reviewed_question_ids": list(dict.fromkeys(reviewed_question_ids or [])),
            },
        }
    cursor_applied = reviewed_question_ids is not None
    reviewed = [] if reviewed_question_ids is None else strict_string_list(
        reviewed_question_ids,
        "reviewed_question_ids",
        0,
        allow_string=False,
    )
    reviewed = list(dict.fromkeys(reviewed))
    remaining = [item for item in questions if item["id"] not in set(reviewed)]
    effective_start = 0 if cursor_applied else batch_start
    if not remaining or effective_start >= len(remaining):
        raise ValueError(
            f"no unreviewed questions are available at batch_start {batch_start}"
        )
    batch = remaining[effective_start : effective_start + BATCH_SIZE]
    next_start = effective_start + len(batch)
    has_more = next_start < len(remaining)
    batch_ids = [item["id"] for item in batch]
    return {
        "questions": batch,
        "request_user_input_required": True,
        "continuation": {
            "batch_start": effective_start,
            "requested_batch_start": batch_start,
            "batch_size": len(batch),
            "total_questions": len(questions),
            "remaining_questions": len(remaining),
            "has_more": has_more,
            "next_batch_start": next_start if has_more else None,
            "cursor_applied": cursor_applied,
            "reviewed_question_ids": reviewed,
            "batch_question_ids": batch_ids,
            "next_reviewed_question_ids": list(dict.fromkeys([*reviewed, *batch_ids])),
        },
    }


def route_options(route: str | None) -> list[dict[str, str]]:
    if route is None:
        return [
            option("Clarify admissions goal (Recommended)", "State the exact programme, requirement, materials, writing, submission, or visa task."),
            option("Programme or requirements", "Research programmes or verify a named programme's official application requirements."),
            option("Writing or materials", "Work on admissions writing or compare current application documents with verified requirements."),
        ]
    recommended = route or "program_research"
    ordered = [recommended] + [
        item
        for item in ("requirement_audit", "application_writing_studio", "materials_check", "program_research")
        if item != recommended
    ]
    descriptions = {
        "program_research": "Find and filter programmes from current official sources without predicting admission probability.",
        "requirement_audit": "Verify a named programme's requirements, documents, prompts, policies, fees, and deadlines.",
        "materials_check": "Compare the applicant's current document inventory with verified programme requirements.",
        "application_writing_studio": "Plan, draft, or revise admissions writing from confirmed applicant and programme evidence.",
    }
    return [
        option(
            f"{ROUTE_LABELS[item]}{' (Recommended)' if item == recommended else ''}",
            descriptions[item],
        )
        for item in ordered[:3]
    ]


def research_degree_requested(prompt: str) -> bool:
    normalized = normalize_prompt(prompt)
    return prompt_has_any(normalized, [
        "research degree", "research master", "research masters", "mphil", "mres", "msc by research",
        "master by research", "研究型硕士", "研究学位", "研究型项目",
    ])


def route_follow_up_resolved(route: str, prompt: str, setup: dict[str, Any]) -> bool:
    """Return whether the user has already fixed the route-specific scope or presentation choice."""
    normalized = normalize_prompt(prompt)
    if route == "requirement_audit":
        return prompt_has_any(normalized, [
            "explain it directly", "explain directly", "direct explanation", "explanation only",
            "not as a checklist", "without a checklist", "do not create a checklist",
            "compact table", "as a checklist", "create a checklist", "give me a checklist",
            "直接解释", "不要清单", "不使用清单", "用紧凑表格", "生成清单",
        ])
    if route == "materials_check":
        return explicit_materials_readiness_request(prompt)
    if route == "program_research" and supervisor_fit_requested(prompt, setup):
        return bool(
            prompt_has_any(normalized, ["representative publications", "current research", "supervisor publications"])
            and prompt_has_any(normalized, ["confirmed interest", "research interest", "proposed topic"])
        )
    if route == "program_research" and research_degree_requested(prompt):
        return bool(
            re.search(r"\b(?:only|strictly|limited to|restrict(?:ed)? to)\b.{0,140}\b(?:mphil|mres|msc by research)\b", normalized)
            or re.search(r"(?:只包括|仅包括|只列出|仅列出).{0,100}(?:mphil|mres|msc by research)", normalized)
        )
    return False


def route_follow_up(route: str, prompt: str = "", setup: dict[str, Any] | None = None) -> dict[str, Any]:
    if route == "requirement_audit":
        return question(
            "Output",
            "requirement_output",
            "How should the verified application requirements be presented?",
            [
                option("Explanation + table (Recommended)", "Explain the requirements directly and use a compact table where comparison helps."),
                option("Explanation only", "Give a direct sourced explanation without creating a checklist."),
                option("Checklist requested", "Create a checklist only because the user explicitly wants one."),
            ],
        )
    if route == "program_research":
        if supervisor_fit_requested(prompt, setup):
            return question(
                "Supervisor",
                "supervisor_fit_scope",
                "What should the supervisor and programme-fit review establish?",
                [
                    option(
                        "Fit + evidence (Recommended)",
                        "Verify contact status, current research, representative publications, and fit with confirmed applicant interests.",
                    ),
                    option(
                        "Contact requirement only",
                        "Verify whether supervisor contact is required, recommended, optional, not required, or unknown.",
                    ),
                    option(
                        "Programme fit only",
                        "Compare research areas, structure, modules, groups, and facilities without ranking individual supervisors.",
                    ),
                ],
            )
        exact_research = research_degree_requested(prompt)
        return question(
            "Degree",
            "research_degree_filter",
            "How strictly should programme discovery apply the requested research degree type?"
            if exact_research
            else "What award filter should programme discovery use?",
            [
                option(
                    "Exact research degrees (Recommended)" if exact_research else "Best award fit (Recommended)",
                    "Keep only verified MPhil, MRes, MSc by Research, or equivalent thesis-led awards."
                    if exact_research
                    else "Match award level and structure to the stated goal without assuming a research-only degree filter.",
                ),
                option(
                    "Research-heavy taught degrees" if exact_research else "Research awards only",
                    "Include taught degrees only when the user explicitly accepts them."
                    if exact_research
                    else "Narrow the search to verified MPhil, MRes, MSc by Research, or equivalent thesis-led awards.",
                ),
                option("Named awards only", "Use only the exact award labels supplied by the user."),
            ],
        )
    if route == "application_writing_studio":
        return question(
            "Writing",
            "writing_brief_and_evidence",
            "What should control the admissions writing workflow?",
            [
                option("Brief + evidence first (Recommended)", "Lock the prompt, limit, applicant evidence, programme fit, and revision ledger before drafting."),
                option("Revise supplied draft", "Use the supplied draft as the object and confirm every requested change before rewriting."),
                option("Narrative options first", "Compare evidence-limited narrative options before selecting the structure."),
            ],
        )
    if route == "materials_check":
        return question(
            "Materials",
            "materials_scope",
            "What should the materials review establish?",
            [
                option("Compare current inventory (Recommended)", "Map supplied files and statuses to the verified requirements for the named programme."),
                option("Identify missing evidence", "Focus on incomplete, unverified, stale, or unavailable applicant documents."),
                option("Submission blockers", "Limit the output to issues that currently prevent submission."),
            ],
        )
    if route == "submission_readiness":
        return question(
            "Readiness",
            "submission_scope",
            "What should the final submission review prioritize?",
            [
                option("Blockers first (Recommended)", "Check current-cycle requirements, portal fields, documents, deadlines, and mandatory actions."),
                option("Full readiness audit", "Review every application workstream and its evidence status."),
                option("Deadline-critical only", "Limit the review to time-sensitive actions and unresolved submission risks."),
            ],
        )
    if route == "visa_readiness":
        return question(
            "Visa",
            "visa_scope",
            "What should the visa-readiness review prioritize?",
            [
                option("Official rules + gaps (Recommended)", "Use current government sources and identify unresolved funding or document gaps."),
                option("Sponsor-specific steps", "Combine government rules with official university sponsor instructions."),
                option("Document readiness", "Limit the review to the applicant's current visa-document inventory."),
            ],
        )
    if route == "programme_table_cleaning":
        return question(
            "Workbook",
            "programme_table_scope",
            "What should the programme-table maintenance preserve?",
            [
                option("Lineage + verified rows (Recommended)", "Preserve raw values, sources, cycles, access dates, and verification status."),
                option("Schema cleanup", "Normalize structure without changing unsupported programme facts."),
                option("Verification report", "Focus on invalid, stale, duplicated, or incomplete rows."),
            ],
        )
    return question(
        "Output",
        "route_specific_follow_up",
        "What route-specific output should be produced?",
        [
            option("Source-backed summary (Recommended)", "Use the official source policy required by the selected route."),
            option("Gap analysis", "Focus on unresolved inputs and blockers."),
            option("Structured case update", "Return verified state suitable for ApplicationCase."),
        ],
    )


def route_review_questions(prompt: str, setup: dict[str, Any]) -> list[dict[str, Any]]:
    plan = build_plan(prompt, setup)
    route = plan["route"]
    if plan["route_status"] != "matched" or not route:
        status = plan["route_status"]
        prompt_text = (
            "Which admissions task, if any, should replace this out-of-scope request?"
            if status == "out_of_scope"
            else "Which workflow should be used for this unresolved admissions request?"
        )
        return [question("Route", "application_route", prompt_text, route_options(None))]

    questions: list[dict[str, Any]] = []
    for gap in plan["profile_gaps"]:
        questions.append(
            question(
                "Input",
                f"gap_{slug(gap, 'input')}",
                f"How should the missing {gap} be handled for this {ROUTE_LABELS[route]} task?",
                [
                    option("Provide input (Recommended)", "Supply or confirm this route-specific input before relying on it."),
                    option("Continue as unknown", "Proceed only where possible and keep the missing value explicit."),
                    option("Narrow the task", "Remove the comparison or output that depends on this input."),
                ],
            )
        )
    if not route_follow_up_resolved(route, prompt, setup):
        questions.append(route_follow_up(route, prompt, setup))
    return questions


def normalized_semantic_value(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip().casefold()
    if isinstance(value, list):
        return [normalized_semantic_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): normalized_semantic_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    return value


def inline_fragment(value: Any) -> str:
    text = re.sub(r"\s+", " ", value if isinstance(value, str) else "").strip()
    return re.sub(r"[.!?]+(?=\s|$)", ";", text).strip(" ;")


def ledger_semantic_key(item: dict[str, Any]) -> str:
    """Return a stable key for feedback meaning, excluding identity, provenance, and workflow state."""
    excluded = {
        "decision_id", "id", "decision_ids", "source_locations", "source_location",
        "confirmation_status", "decision_status", "status", "coverage_status", "coverage_state",
        "implementation_locations", "implementation_location", "conflicts_with", "conflict_with",
        "conflict_resolution_status",
    }
    aliases = {
        "target": ("target", "document"),
        "instruction": ("instruction", "requirement"),
    }
    consumed = {field for fields in aliases.values() for field in fields}
    projection = {
        key: normalized_semantic_value(value)
        for key, value in item.items()
        if key not in excluded and key not in consumed
    }
    for canonical, fields in aliases.items():
        values: list[Any] = []
        fingerprints: set[str] = set()
        for field in fields:
            if field not in item:
                continue
            normalized = normalized_semantic_value(item[field])
            fingerprint = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if fingerprint not in fingerprints:
                fingerprints.add(fingerprint)
                values.append(normalized)
        if values:
            projection[canonical] = values[0] if len(values) == 1 else {"alias_values": values}
    return json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def strict_string_list(value: Any, field: str, index: int, *, allow_string: bool = True) -> list[str]:
    if value is None:
        return []
    if allow_string and isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        raise ValueError(f"revision item {index} field {field} must be a string or string list")
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"revision item {index} field {field} contains an invalid locator or ID")
    return [item.strip() for item in values]


def canonical_text_alias(item: dict[str, Any], fields: tuple[str, ...], index: int) -> str:
    values: list[str] = []
    for field in fields:
        if field not in item or item[field] is None:
            continue
        value = item[field]
        if not isinstance(value, str):
            raise ValueError(f"revision item {index} field {field} must be text")
        if value.strip():
            values.append(value.strip())
    normalized = {re.sub(r"\s+", " ", value).casefold() for value in values}
    if len(normalized) > 1:
        raise ValueError(f"revision item {index} has conflicting aliases: {', '.join(fields)}")
    return values[0] if values else ""


def item_status(item: dict[str, Any], fields: tuple[str, ...], index: int) -> str:
    values: list[str] = []
    for field in fields:
        if field not in item or item[field] is None:
            continue
        value = item[field]
        if not isinstance(value, str):
            raise ValueError(f"revision item {index} field {field} must be text")
        normalized = normalized_status(value)
        if normalized:
            values.append(normalized)
    unique = list(dict.fromkeys(values))
    return unique[0] if len(unique) == 1 else "conflicted" if unique else ""


def aggregate_decision_status(*statuses: str) -> str:
    values = [normalized_status(value) or "missing" for value in statuses]
    invalid = [value for value in values if value not in RESOLVED_DECISION_STATUSES | BLOCKING_DECISION_STATUSES]
    if invalid:
        return invalid[0]
    for value in ("conflicted", "conflict", "unresolved", "pending", "unconfirmed", "missing"):
        if value in values:
            return value
    unique = set(values)
    active = {"explicitly_confirmed", "confirmed", "adjusted"}
    if unique <= active:
        return "adjusted" if "adjusted" in unique else "explicitly_confirmed"
    return next(iter(unique)) if len(unique) == 1 else "conflicted"


def aggregate_coverage_status(*statuses: str) -> str:
    values = [normalized_status(value) or "missing" for value in statuses]
    invalid = [value for value in values if value not in RESOLVED_COVERAGE_STATUSES | BLOCKING_COVERAGE_STATUSES]
    if invalid:
        return invalid[0]
    for value in ("conflicted", "conflict", "unresolved", "pending", "missing"):
        if value in values:
            return value
    unique = set(values)
    return next(iter(unique)) if len(unique) == 1 else "pending"


def ledger_items(setup: dict[str, Any]) -> list[dict[str, Any]]:
    canonical = setup.get("revision_decision_ledger")
    if isinstance(canonical, dict):
        canonical = canonical.get("items", canonical.get("decisions", []))
    compatibility = setup.get("writing_revision_items")
    raw = canonical if isinstance(canonical, list) and canonical else compatibility
    if not isinstance(raw, list) or not raw:
        raise ValueError("writing revision stages require a populated revision_decision_ledger")
    items: list[dict[str, Any]] = []
    semantic_positions: dict[str, int] = {}
    seen_ids: dict[str, str] = {}
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"revision item {index} must be an object")
        raw_id = item.get("decision_id") or item.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise ValueError(f"revision item {index} is missing decision_id")
        for field in ("category", *DECISION_STATUS_FIELDS, *COVERAGE_STATUS_FIELDS, "conflict_resolution_status"):
            if field in item and item[field] is not None and not isinstance(item[field], str):
                raise ValueError(f"revision item {index} field {field} must be text")
        decision_ids = [raw_id.strip(), *strict_string_list(item.get("decision_ids"), "decision_ids", index)]
        unique_ids: list[str] = []
        current_normalized_ids: set[str] = set()
        for decision_id in decision_ids:
            normalized_id = slug(decision_id, "")
            if not normalized_id:
                raise ValueError(f"revision item {index} has an invalid decision_id")
            if normalized_id in current_normalized_ids:
                continue
            if normalized_id in seen_ids:
                raise ValueError(
                    f"revision decision ID collision: {decision_id!r} conflicts with {seen_ids[normalized_id]!r}"
                )
            current_normalized_ids.add(normalized_id)
            seen_ids[normalized_id] = decision_id
            unique_ids.append(decision_id)
        source_locations: list[str] = []
        for field in ("source_locations", "source_location"):
            if field in item:
                source_locations.extend(strict_string_list(item[field], field, index))
        conflicts: list[str] = []
        for field in CONFLICT_FIELDS:
            if field in item:
                conflicts.extend(strict_string_list(item[field], field, index))
        implementation_locations: list[str] = []
        for field in IMPLEMENTATION_FIELDS:
            if field in item:
                implementation_locations.extend(strict_string_list(item[field], field, index))
        target = canonical_text_alias(item, ("target", "document"), index)
        instruction = canonical_text_alias(item, ("instruction", "requirement"), index)
        decision_status = item_status(item, DECISION_STATUS_FIELDS, index)
        coverage_status = item_status(item, COVERAGE_STATUS_FIELDS, index)
        conflict_resolution = item_status(item, ("conflict_resolution_status",), index)
        prepared = dict(item)
        for field in {
            "id", "decision_ids", "source_locations", "source_location", "target", "document",
            "instruction", "requirement", *DECISION_STATUS_FIELDS, *COVERAGE_STATUS_FIELDS,
            *CONFLICT_FIELDS, *IMPLEMENTATION_FIELDS, "conflict_resolution_status",
        }:
            prepared.pop(field, None)
        prepared["decision_id"] = unique_ids[0]
        prepared["decision_ids"] = unique_ids
        prepared["source_locations"] = list(dict.fromkeys(source_locations))
        if target:
            prepared["target"] = target
        if instruction:
            prepared["instruction"] = instruction
        if decision_status:
            prepared["confirmation_status"] = decision_status
        if coverage_status:
            prepared["coverage_status"] = coverage_status
        if conflicts:
            prepared["conflicts_with"] = list(dict.fromkeys(conflicts))
        if implementation_locations:
            prepared["implementation_locations"] = list(dict.fromkeys(implementation_locations))
        if conflict_resolution:
            prepared["conflict_resolution_status"] = conflict_resolution
        semantic_key = ledger_semantic_key(prepared)
        existing_position = semantic_positions.get(semantic_key)
        if existing_position is None:
            semantic_positions[semantic_key] = len(items)
            items.append(prepared)
            continue
        existing = items[existing_position]
        existing["decision_ids"] = list(dict.fromkeys([
            *normalized_list(existing.get("decision_ids")),
            *unique_ids,
        ]))
        existing["source_locations"] = list(dict.fromkeys([
            *normalized_list(existing.get("source_locations")),
            *source_locations,
        ]))
        existing_status = normalized_status(existing.get("confirmation_status"))
        merged_status = aggregate_decision_status(existing_status, decision_status)
        existing["confirmation_status"] = merged_status
        existing_coverage = normalized_status(existing.get("coverage_status"))
        merged_coverage = aggregate_coverage_status(existing_coverage, coverage_status)
        existing_locations = normalized_list(existing.get("implementation_locations"))
        new_locations = list(dict.fromkeys(implementation_locations))
        if existing_locations != new_locations and merged_coverage not in NO_LOCATION_COVERAGE_STATUSES:
            merged_coverage = "pending" if existing_locations and new_locations else "missing"
        existing["coverage_status"] = merged_coverage
        existing["implementation_locations"] = list(dict.fromkeys([
            *existing_locations,
            *new_locations,
        ]))
        existing["conflicts_with"] = list(dict.fromkeys([
            *normalized_list(existing.get("conflicts_with")),
            *conflicts,
        ]))
        existing_resolution = normalized_status(existing.get("conflict_resolution_status"))
        if existing["conflicts_with"]:
            existing["conflict_resolution_status"] = (
                existing_resolution
                if existing_resolution and existing_resolution == conflict_resolution
                else "unresolved"
            )
    return items


def ledger_context(item: dict[str, Any], index: int) -> tuple[str, str]:
    item_id = slug(item.get("decision_id") or item.get("id"), f"revision_{index}")
    decision_ids = normalized_list(item.get("decision_ids")) or [str(item.get("decision_id") or item_id)]
    category = inline_fragment(item.get("category")) or "revision requirement"
    target = inline_fragment(item.get("target") or item.get("document")) or "the application document"
    instruction = inline_fragment(item.get("instruction") or item.get("requirement")) or "review this requirement"
    sources = normalized_list(item.get("source_locations") or item.get("source_location"))
    source_text = ", ".join(inline_fragment(value) for value in sources) or "unlocated"
    conflicts = normalized_list(item.get("conflicts_with") or item.get("conflict_with"))
    context_parts = [f"{category} for {target}: {instruction}", f"sources: {source_text}"]
    if len(decision_ids) > 1:
        context_parts.append(f"decision IDs: {', '.join(inline_fragment(value) for value in decision_ids)}")
    if conflicts:
        context_parts.append(f"conflicts with: {', '.join(inline_fragment(value) for value in conflicts)}")
    context = "; ".join(context_parts)
    return item_id, context


def normalized_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def normalized_status(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[\s-]+", "_", value.strip().casefold())


def revision_blockers(item: dict[str, Any], coverage: bool) -> list[str]:
    blockers: list[str] = []
    if not str(item.get("category") or "").strip():
        blockers.append("missing category")
    if not str(item.get("target") or item.get("document") or "").strip():
        blockers.append("missing target")
    sources = normalized_list(item.get("source_locations") or item.get("source_location"))
    if not sources or any(value.casefold() in {"unlocated", "not recorded", "missing", "pending"} for value in sources):
        blockers.append("unlocated source")
    instruction = str(item.get("instruction") or item.get("requirement") or "").strip()
    if not instruction:
        blockers.append("missing instruction")
    status = normalized_status(
        item.get("confirmation_status") or item.get("decision_status") or item.get("status") or ""
    )
    if not status:
        blockers.append("missing decision status")
    elif status in BLOCKING_DECISION_STATUSES:
        blockers.append(f"decision status {status}")
    elif status not in RESOLVED_DECISION_STATUSES:
        blockers.append(f"invalid decision status {status}")
    conflicts = normalized_list(item.get("conflicts_with") or item.get("conflict_with"))
    conflict_resolution = normalized_status(item.get("conflict_resolution_status"))
    if conflicts and conflict_resolution not in {"resolved", "superseded", "not_applicable"} and status not in {
        "rejected", "superseded", "not_applicable"
    }:
        blockers.append("unresolved conflict")
    if coverage:
        coverage_status = normalized_status(item.get("coverage_status") or item.get("coverage_state"))
        locations = normalized_list(item.get("implementation_locations") or item.get("implementation_location"))
        if coverage_status not in NO_LOCATION_COVERAGE_STATUSES and (
            not locations
            or any(normalized_status(value) in {"not_recorded", "missing", "pending", "unlocated"} for value in locations)
        ):
            blockers.append("missing implementation location")
        if not coverage_status:
            blockers.append("missing coverage status")
        elif coverage_status in BLOCKING_COVERAGE_STATUSES:
            blockers.append(f"coverage status {coverage_status}")
        elif coverage_status not in RESOLVED_COVERAGE_STATUSES:
            blockers.append(f"invalid coverage status {coverage_status}")
    return blockers


def ledger_diagnostics(items: list[dict[str, Any]], coverage: bool) -> dict[str, Any]:
    blocked: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        item_id, _ = ledger_context(item, index)
        reasons = revision_blockers(item, coverage)
        decision_ids = normalized_list(item.get("decision_ids")) or [item_id]
        if reasons:
            blocked.append({"decision_id": item_id, "decision_ids": decision_ids, "reasons": reasons})
        linked = normalized_list(item.get("conflicts_with") or item.get("conflict_with"))
        if linked:
            conflicts.append({"decision_id": item_id, "conflicts_with": linked})
    return {
        "decision_count": len(items),
        "source_decision_count": sum(
            len(normalized_list(item.get("decision_ids")) or [item.get("decision_id")])
            for item in items
        ),
        "blocked_decisions": blocked,
        "conflicts": conflicts,
        "delivery_blocked": bool(blocked),
    }


def writing_revision_questions(setup: dict[str, Any], coverage: bool) -> list[dict[str, Any]]:
    questions = []
    for index, item in enumerate(ledger_items(setup), start=1):
        item_id, context = ledger_context(item, index)
        blockers = revision_blockers(item, coverage)
        blocker_text = f"; blocking issues: {', '.join(blockers)}" if blockers else ""
        if coverage:
            locations = normalized_list(item.get("implementation_locations") or item.get("implementation_location"))
            location = ", ".join(inline_fragment(value) for value in locations) or "not recorded"
            coverage_status = normalized_status(item.get("coverage_status") or item.get("coverage_state"))
            prompt_text = f"How should coverage be handled for {context}; final implementation locations: {location}{blocker_text}?"
            options = (
                [
                    option("Needs correction (Recommended)", "Keep delivery blocked until every coverage issue is resolved."),
                    option("Resolve mapping", "Add or correct the final implementation location and coverage state."),
                    option("Superseded or not applicable", "Use only with an explicit replacement, rejection, or exclusion reason."),
                ]
                if blockers
                else [
                    option(
                        "Confirm final disposition (Recommended)",
                        "Accept the explicitly rejected, superseded, or not-applicable outcome and its recorded reason.",
                    ),
                    option("Needs correction", "Keep delivery blocked until the disposition or reason is corrected."),
                    option("Restore decision", "Return the decision to active coverage and map it to final text."),
                ]
                if coverage_status in NO_LOCATION_COVERAGE_STATUSES
                else [
                    option("Confirm implemented (Recommended)", "Accept the mapped final text and location as satisfying this decision."),
                    option("Needs correction", "Keep delivery blocked until the draft or mapping is corrected."),
                    option("Superseded or not applicable", "Use only when the user explicitly replaced, rejected, or excluded the decision with a reason."),
                ]
            )
            suffix = "coverage"
        else:
            prompt_text = f"How should this revision decision be resolved before planning or drafting for {context}{blocker_text}?"
            options = (
                [
                    option("Resolve blockers (Recommended)", "Locate the source, supply the missing instruction, and resolve any conflict before confirmation."),
                    option("Adjust requirement", "Correct the decision record without treating it as confirmed."),
                    option("Reject or replace", "Explicitly reject or supersede this item with a reason."),
                ]
                if blockers
                else [
                    option("Confirm as written (Recommended)", "Keep the exact requirement and make it part of the approved writing plan."),
                    option("Adjust requirement", "Change the target, role, evidence use, wording, or boundary before drafting."),
                    option("Reject or replace", "Explicitly reject or supersede this item; do not silently prefer a newer conflict."),
                ]
            )
            suffix = "review"
        questions.append(question("Revision", f"{item_id}_{suffix}", prompt_text, options))
    return questions


def build_payload(
    prompt: str,
    setup: dict[str, Any] | None = None,
    *,
    stage: str = "route-review",
    batch_start: int = 0,
    reviewed_question_ids: list[str] | None = None,
) -> dict[str, Any]:
    setup = setup or {}
    if stage == "route-review":
        questions = route_review_questions(prompt, setup)
        diagnostics = None
    elif stage == "writing-revision":
        questions = writing_revision_questions(setup, coverage=False)
        diagnostics = ledger_diagnostics(ledger_items(setup), coverage=False)
    else:
        questions = writing_revision_questions(setup, coverage=True)
        diagnostics = ledger_diagnostics(ledger_items(setup), coverage=True)
    payload = paged_payload(questions, batch_start, reviewed_question_ids)
    if diagnostics is not None:
        payload["revision_decision_ledger"] = diagnostics
    return payload


def load_setup(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def self_test() -> None:
    writing = build_payload("help brainstorm my personal statement")
    assert 1 <= len(writing["questions"]) <= BATCH_SIZE
    assert all(item["id"] != "application_route" for item in writing["questions"])

    requirements = build_payload(
        "检查这个项目都需要什么文书",
        {"program_name": "Example MSc", "application_cycle": "2026-27"},
    )
    assert requirements["questions"][0]["id"] == "requirement_output"
    assert requirements["questions"][0]["options"][0]["label"].startswith("Explanation + table")

    sop_portal_prompt = (
        "Draft a 1,000-word statement of purpose for my 2027-28 application to the University of "
        "Cambridge MPhil in Biological Science (Biochemistry) by thesis. It will be submitted in the "
        "admissions portal. I have not yet given you my academic experiences or the exact official prompt."
    )
    sop_portal = build_payload(sop_portal_prompt)
    assert all(item["id"] != "application_route" for item in sop_portal["questions"])
    assert "gap_target_programme" not in {item["id"] for item in sop_portal["questions"]}

    materials_prompt = (
        "I am applying to UCL's Cognitive Neuroscience MRes for 2027 entry. I currently have a transcript "
        "and CV, my referee has agreed to write, but I do not yet have an IELTS result or personal statement. "
        "Check whether my application materials are ready to submit."
    )
    materials = build_payload(materials_prompt)
    assert materials["questions"] == []
    assert materials["request_user_input_required"] is False

    institution_list_prompt = (
        "请用中文列出 Cambridge、Oxford、Imperial、UCL、NTU 和 NUS 在 2027-28 入学周期中与 Biological "
        "Sciences 相关的 Research 类型 Master 项目。只包括 MPhil、MRes、MSc by Research 或明确以 thesis "
        "为主的同等学位，使用当前官方来源。"
    )
    institution_list = build_payload(institution_list_prompt)
    assert institution_list["questions"] == []
    assert institution_list["continuation"]["total_questions"] == 0

    supervisor_prompt = (
        "For the University of Cambridge MPhil in Biological Science (Biochemistry) by thesis for 2027-28, "
        "identify potential supervisors and compare their current research and representative publications "
        "with my confirmed interest in enhancer regulation and single-cell genomics. Also verify whether "
        "supervisor contact is required before applying."
    )
    supervisor = build_payload(supervisor_prompt)
    assert supervisor["questions"] == []
    assert supervisor["request_user_input_required"] is False

    confirmed_fact_prompt = (
        "Draft a programme-fit paragraph for my 2027-28 Cambridge MPhil in Biological Science (Biochemistry) "
        "application. My local CV says I completed an eight-week CRISPR screen placement, and I explicitly "
        "confirm that this is accurate. Use only that confirmed applicant fact plus verified official programme facts."
    )
    confirmed_fact = build_payload(confirmed_fact_prompt)
    supplied_gap_ids = {
        "gap_target_programme", "gap_intended_use", "gap_applicant_evidence_or_background",
    }
    assert supplied_gap_ids.isdisjoint(item["id"] for item in confirmed_fact["questions"])

    direct_requirement_prompt = (
        "For the University of Oxford MSc by Research in Biochemistry, 2027-28 entry, tell me exactly which "
        "application documents I must submit, the statement prompt and word limit, reference requirements, "
        "application fee, deadline, and whether I must contact a supervisor before applying. Use current "
        "official sources. Explain it directly, not as a checklist."
    )
    direct_requirement = build_payload(direct_requirement_prompt)
    assert direct_requirement["questions"] == []
    assert direct_requirement["request_user_input_required"] is False

    natural_word_prompt = (
        "Please back up my Word document, improve the typography, fix the spacing, and make it look more "
        "polished. It is not an admissions document."
    )
    natural_word = build_payload(natural_word_prompt)
    assert natural_word["questions"][0]["id"] == "application_route"

    out_of_scope = build_payload("备份并美化Word排版")
    assert out_of_scope["questions"][0]["id"] == "application_route"

    requirement_gaps = build_payload("check requirements", {"program_name": "Example MSc"})
    serialized = json.dumps(requirement_gaps)
    assert "GPA" not in serialized and "language-test status" not in serialized

    ledger_records = [
        {
            "decision_id": f"decision_{index}",
            "category": "preserve" if index == 1 else "programme-specific emphasis",
            "target": "shared statement" if index < 4 else "second programme essay",
            "instruction": f"Requirement {index}",
            "source_locations": [f"conversation:{index}"],
            "conflicts_with": ["decision_1"] if index == 5 else [],
            "implementation_locations": [f"paragraph:{index}"],
        }
        for index in range(1, 6)
    ]
    ledger_records.append({
        **ledger_records[1],
        "decision_id": "decision_2_duplicate",
        "source_locations": ["conversation:duplicate"],
    })
    ledger = {
        "writing_revision_items": [],
        "revision_decision_ledger": ledger_records,
    }
    normalized_ledger = ledger_items(ledger)
    assert len(normalized_ledger) == 5
    assert normalized_ledger[1]["decision_ids"] == ["decision_2", "decision_2_duplicate"]
    assert normalized_ledger[1]["source_locations"] == ["conversation:2", "conversation:duplicate"]
    first = build_payload("", ledger, stage="writing-revision")
    second = build_payload("", ledger, stage="writing-revision", batch_start=3)
    ids = [item["id"] for item in first["questions"] + second["questions"]]
    assert len(ids) == len(set(ids)) == 5
    assert first["continuation"]["next_batch_start"] == 3
    assert second["continuation"]["has_more"] is False
    assert first["revision_decision_ledger"]["decision_count"] == 5
    assert first["revision_decision_ledger"]["source_decision_count"] == 6
    assert "decision_2_duplicate" in first["questions"][1]["question"]
    assert "conversation:duplicate" in first["questions"][1]["question"]
    coverage = build_payload("", ledger, stage="writing-coverage", batch_start=3)
    assert len(coverage["questions"]) == 2
    assert "conflicts with" in coverage["questions"][1]["question"]
    assert coverage["revision_decision_ledger"]["delivery_blocked"] is True
    assert not coverage["questions"][1]["options"][0]["label"].startswith("Confirm")
    assert all(item["question"].isascii() for item in first["questions"] + second["questions"])

    two_documents = {
        "revision_decision_ledger": [
            {
                "decision_id": "shared_statement_detail",
                "category": "preserve",
                "target": "shared statement",
                "instruction": "Keep the verified research detail.",
                "source_locations": ["turn:20"],
            },
            {
                "decision_id": "second_essay_detail",
                "category": "preserve",
                "target": "second programme essay",
                "instruction": "Keep the verified research detail.",
                "source_locations": ["turn:21"],
            },
        ]
    }
    assert len(ledger_items(two_documents)) == 2
    conflict_and_instruction_changes = {
        "revision_decision_ledger": [
            {
                "decision_id": "base_instruction",
                "category": "preserve",
                "target": "opening",
                "instruction": "Keep the opening.",
                "source_locations": ["turn:22"],
            },
            {
                "decision_id": "different_instruction",
                "category": "preserve",
                "target": "opening",
                "instruction": "Replace the opening.",
                "source_locations": ["turn:23"],
            },
            {
                "decision_id": "conflicting_instruction",
                "category": "preserve",
                "target": "opening",
                "instruction": "Keep the opening.",
                "source_locations": ["turn:24"],
                "conflicts_with": ["different_instruction"],
            },
        ]
    }
    normalized_conflicts = ledger_items(conflict_and_instruction_changes)
    assert len(normalized_conflicts) == 2
    assert normalized_conflicts[0]["decision_ids"] == ["base_instruction", "conflicting_instruction"]
    assert normalized_conflicts[0]["conflicts_with"] == ["different_instruction"]
    assert "unresolved conflict" in revision_blockers(normalized_conflicts[0], coverage=False)

    duplicate_state_disagreement = {
        "revision_decision_ledger": [
            {
                "decision_id": "pending_copy",
                "category": "preserve",
                "target": "opening",
                "instruction": "Keep the verified opening.",
                "source_locations": ["turn:25"],
                "confirmation_status": "pending",
                "coverage_status": "complete",
                "implementation_locations": ["paragraph:1"],
            },
            {
                "decision_id": "confirmed_copy",
                "category": "preserve",
                "target": "opening",
                "instruction": "Keep the verified opening.",
                "source_locations": ["turn:26"],
                "confirmation_status": "explicitly_confirmed",
                "coverage_status": "complete",
                "implementation_locations": ["paragraph:2"],
            },
        ]
    }
    merged_disagreement = ledger_items(duplicate_state_disagreement)
    assert len(merged_disagreement) == 1
    assert merged_disagreement[0]["confirmation_status"] == "pending"
    assert merged_disagreement[0]["coverage_status"] == "pending"
    assert merged_disagreement[0]["implementation_locations"] == ["paragraph:1", "paragraph:2"]
    assert ledger_diagnostics(merged_disagreement, coverage=False)["delivery_blocked"] is True
    assert ledger_diagnostics(merged_disagreement, coverage=True)["delivery_blocked"] is True

    invalid_typed_fields = (
        {"decision_id": {"bad": "id"}},
        {"decision_id": "bad_category", "category": {}},
        {"decision_id": "bad_source", "source_locations": {}},
        {"decision_id": "bad_status", "confirmation_status": 1},
        {"decision_id": "bad_coverage", "coverage_status": []},
        {"decision_id": "bad_location", "implementation_locations": {}},
    )
    for invalid_item in invalid_typed_fields:
        try:
            ledger_items({"revision_decision_ledger": [invalid_item]})
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid typed ledger field passed: {invalid_item}")

    generic_research = route_follow_up("program_research", "Find masters programmes in the UK")
    assert generic_research["options"][0]["label"].startswith("Best award fit")
    exact_research = route_follow_up("program_research", "Find MRes programmes in the UK")
    assert exact_research["options"][0]["label"].startswith("Exact research degrees")
    supervisor_fit = route_follow_up("program_research", "Compare supervisors for this programme")
    assert supervisor_fit["id"] == "supervisor_fit_scope"
    assert supervisor_fit["options"][0]["label"].startswith("Fit + evidence")
    supervisor_intake = build_payload("帮我筛选导师")
    assert [item["id"] for item in supervisor_intake["questions"]] == [
        "gap_named_programme_or_institution",
        "gap_confirmed_research_interests_or_proposed_topic",
        "supervisor_fit_scope",
    ]
    supplied_supervisor = build_payload(
        "帮我筛选牛津大学导师，我的研究方向是计算神经科学",
        {"supervisor_fit_scope": "fit + evidence", "application_cycle": "2026-27"},
    )
    assert [item["id"] for item in supplied_supervisor["questions"]] == ["supervisor_fit_scope"]
    contact_supervisor = build_payload(
        "帮我筛选牛津大学导师，我的研究方向是计算神经科学",
        {"supervisor_fit_scope": "contact requirement only"},
    )
    assert contact_supervisor["questions"][0]["id"] == "gap_application_cycle_or_target_intake"
    assert all(
        phrase not in json.dumps(contact_supervisor, ensure_ascii=False)
        for phrase in ("target degree level", "destination country or region", "target field")
    )

    writing_first = build_payload("Write my SOP")
    first_cursor = writing_first["continuation"]["next_reviewed_question_ids"]
    writing_setup = {
        "program_name": "Example MRes",
        "prompt": "Explain your preparation.",
        "word_limit": 1000,
    }
    writing_second = build_payload(
        "Write my SOP",
        writing_setup,
        batch_start=3,
        reviewed_question_ids=first_cursor,
    )
    writing_third = build_payload(
        "Write my SOP",
        writing_setup,
        batch_start=3,
        reviewed_question_ids=writing_second["continuation"]["next_reviewed_question_ids"],
    )
    paged_ids = [
        item["id"]
        for payload in (writing_first, writing_second, writing_third)
        for item in payload["questions"]
    ]
    assert len(paged_ids) == len(set(paged_ids)) == 9
    assert writing_second["continuation"]["cursor_applied"] is True
    assert writing_second["continuation"]["batch_start"] == 0
    assert writing_third["continuation"]["has_more"] is False

    cursor_second = build_payload(
        "",
        ledger,
        stage="writing-revision",
        batch_start=3,
        reviewed_question_ids=first["continuation"]["next_reviewed_question_ids"],
    )
    assert [item["id"] for item in cursor_second["questions"]] == [
        item["id"] for item in second["questions"]
    ]

    for route in ROUTE_LABELS:
        route_prompt = "Compare supervisors" if route == "program_research" else ""
        follow_up = route_follow_up(route, route_prompt)
        assert len(follow_up["header"]) <= 12
        assert single_sentence(follow_up["question"])
        assert 2 <= len(follow_up["options"]) <= 3
        assert all(1 <= label_word_count(item["label"]) <= 5 for item in follow_up["options"])

    collision = {
        "revision_decision_ledger": [
            {"decision_id": "Decision A", "instruction": "Keep A", "source_locations": ["turn:1"]},
            {"decision_id": "decision-a", "instruction": "Keep B", "source_locations": ["turn:2"]},
        ]
    }
    try:
        build_payload("", collision, stage="writing-revision")
    except ValueError as exc:
        assert "collision" in str(exc)
    else:
        raise AssertionError("colliding revision decision IDs must fail")

    blocked = {
        "revision_decision_ledger": [{
            "decision_id": "pending_item",
            "instruction": "Keep the opening",
            "source_locations": [],
            "confirmation_status": "pending",
            "implementation_locations": [],
        }]
    }
    pending_review = build_payload("", blocked, stage="writing-revision")
    pending_coverage = build_payload("", blocked, stage="writing-coverage")
    assert pending_review["questions"][0]["options"][0]["label"].startswith("Resolve blockers")
    assert pending_coverage["questions"][0]["options"][0]["label"].startswith("Needs correction")

    resolved = {
        "revision_decision_ledger": [{
            "decision_id": "resolved_item",
            "category": "preserve",
            "target": "opening paragraph",
            "instruction": "Preserve the verified research question.",
            "source_locations": ["turn:12"],
            "confirmation_status": "explicitly_confirmed",
            "implementation_locations": ["paragraph:1"],
            "coverage_status": "complete",
        }]
    }
    resolved_review = build_payload("", resolved, stage="writing-revision")
    resolved_coverage = build_payload("", resolved, stage="writing-coverage")
    assert resolved_review["questions"][0]["options"][0]["label"].startswith("Confirm as written")
    assert resolved_coverage["questions"][0]["options"][0]["label"].startswith("Confirm implemented")

    invalid_status = {
        "revision_decision_ledger": [{
            "decision_id": "invalid_status",
            "category": "preserve",
            "target": "opening paragraph",
            "instruction": "Preserve the opening.",
            "source_locations": ["turn:15"],
            "confirmation_status": "banana",
            "implementation_locations": ["paragraph:1"],
            "coverage_status": "banana",
        }]
    }
    invalid_coverage = build_payload("", invalid_status, stage="writing-coverage")
    assert invalid_coverage["revision_decision_ledger"]["delivery_blocked"] is True
    assert "invalid decision status" in invalid_coverage["questions"][0]["question"]
    assert "invalid coverage status" in invalid_coverage["questions"][0]["question"]

    superseded = {
        "revision_decision_ledger": [{
            "decision_id": "superseded_item",
            "category": "delete",
            "target": "old sentence",
            "instruction": "Remove the old sentence.",
            "source_locations": ["turn:16"],
            "confirmation_status": "superseded",
            "coverage_status": "superseded",
        }]
    }
    superseded_coverage = build_payload("", superseded, stage="writing-coverage")
    assert superseded_coverage["revision_decision_ledger"]["delivery_blocked"] is False
    assert superseded_coverage["questions"][0]["options"][0]["label"].startswith("Confirm final disposition")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build request_user_input payloads for University Application review gates.")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--setup-json")
    parser.add_argument(
        "--stage",
        choices=("route-review", "writing-revision", "writing-coverage"),
        default="route-review",
    )
    parser.add_argument("--batch-start", type=non_negative_int, default=0)
    parser.add_argument("--reviewed-question-id", action="append", dest="reviewed_question_ids")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("OK: build_review_questions self-test passed")
        return
    try:
        payload = build_payload(
            args.prompt,
            load_setup(args.setup_json),
            stage=args.stage,
            batch_start=args.batch_start,
            reviewed_question_ids=args.reviewed_question_ids,
        )
    except ValueError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
