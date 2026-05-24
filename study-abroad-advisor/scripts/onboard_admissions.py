#!/usr/bin/env python3
"""Create an initial Study Abroad Advisor setup packet."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_setup import validate_setup_data


DEFAULT_QUESTIONS = {
    "quick_triage": [
        "What degree level are you targeting?",
        "What field or major cluster should be explored?",
        "Which countries or regions are possible?",
        "What is your current education country and rough academic standing?",
    ],
    "full_shortlist": [
        "What degree level and intake are you targeting?",
        "Which countries should be included or excluded?",
        "What are your GPA, GPA scale, current major, and current education country?",
        "What are your citizenship, residence country, passport country, and education country?",
        "What is your annual budget ceiling and risk tolerance?",
    ],
    "requirement_audit": [
        "What official program name or URL should be audited?",
        "What target intake and degree level apply?",
        "What citizenship, residence country, education country, and passport country should rules use?",
    ],
    "essay_sop": [
        "What program or program cluster is the statement for?",
        "What prompt, word limit, and statement goal should be used?",
        "What real student evidence can support claims?",
    ],
    "workbook_build": [
        "What ontology JSON or structured case data should be rendered?",
        "Should the workbook be draft or verified?",
    ],
}


def setup_packet(args: argparse.Namespace) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    setup = {
        "user_setup_id": args.user_setup_id,
        "applicant_id": args.applicant_id,
        "workflow_mode": args.mode,
        "output_mode": args.output_mode,
        "recommendation_count": args.recommendation_count,
        "preferred_depth": args.depth,
        "ask_style": args.ask_style,
        "source_policy": args.source_policy,
        "privacy_mode": args.privacy_mode,
        "export_format": args.export_format,
        "created_at": now,
        "updated_at": now,
        "profile": {},
    }
    validation = validate_setup_data(setup)
    return {
        "user_setup": setup,
        "interaction_state": {
            "interaction_state_id": "state_001",
            "user_setup_id": args.user_setup_id,
            "current_step": "setup",
            "completed_cards": ["workflow_goal"],
            "missing_fields": validation["missing_fields"],
            "blocker_count": len(validation["missing_fields"]),
            "warning_count": 0,
            "next_recommended_action": "Ask the next compact setup batch.",
        },
        "next_questions": validation["next_questions"] or DEFAULT_QUESTIONS.get(args.mode, []),
        "setup_report": validation,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a Study Abroad Advisor setup packet.")
    parser.add_argument("--mode", default="quick_triage", choices=[
        "quick_triage",
        "full_shortlist",
        "exact_program_selection",
        "requirement_audit",
        "essay_sop",
        "workbook_build",
        "submission_readiness",
        "source_refresh",
        "visa_route",
    ])
    parser.add_argument("--output-mode", default="draft", choices=["brainstorm", "draft", "source_backed", "verified"])
    parser.add_argument("--user-setup-id", default="setup_001")
    parser.add_argument("--applicant-id", default="app_001")
    parser.add_argument("--recommendation-count", type=int, default=10)
    parser.add_argument("--depth", default="standard", choices=["brief", "standard", "deep"])
    parser.add_argument("--ask-style", default="compact_batches", choices=["compact_batches", "step_by_step", "form_like"])
    parser.add_argument("--source-policy", default="official_only", choices=["official_only", "official_plus_rankings", "draft_with_unverified_markers"])
    parser.add_argument("--privacy-mode", default="public_redacted", choices=["public_redacted", "private_working_copy"])
    parser.add_argument("--export-format", default="chat_summary", choices=["chat_summary", "table", "workbook", "ontology_json"])
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args(argv)

    packet = setup_packet(args)
    text = json.dumps(packet, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
