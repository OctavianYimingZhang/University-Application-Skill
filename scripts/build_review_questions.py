#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from plan_workflow import ROUTE_LABELS, build_plan


def option(label: str, description: str) -> dict[str, str]:
    return {"label": label, "description": description}


def question(header: str, question_id: str, prompt: str, options: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "header": header[:12],
        "id": question_id,
        "question": prompt,
        "options": options[:3],
    }


def route_options(route: str) -> list[dict[str, str]]:
    ordered = [route] + [key for key in ROUTE_LABELS if key != route]
    descriptions = {
        "program_research": "Collect and compare official programme pages without predicting admission probability.",
        "requirement_audit": "Check hard requirements against official sources for named programmes.",
        "materials_check": "Simulate application document readiness and evidence gaps.",
        "application_writing_studio": "Lock the writing brief, build evidence, choose narrative options, and plan before drafting.",
        "submission_readiness": "Run the final pre-submission blocker checklist.",
        "programme_table_cleaning": "Clean and verify official programme workbooks or tables.",
        "visa_route": "Review visa-sensitive readiness from official government and university sources.",
    }
    return [
        option(f"{ROUTE_LABELS[item]}{' (Recommended)' if item == route else ''}", descriptions[item])
        for item in ordered[:3]
    ]


def build_payload(prompt: str, setup: dict[str, Any] | None = None) -> dict[str, Any]:
    plan = build_plan(prompt, setup or {})
    route = plan["route"]
    questions = [
        question(
            "Route",
            "application_route",
            "Which application workflow should be used for this request?",
            route_options(route),
        ),
        question(
            "Sources",
            "source_policy",
            "What source policy should control hard requirements, fees, and deadlines?",
            [
                option("Official only (Recommended)", "Use university, government, testing-agency, and scholarship sources for hard facts."),
                option("Official + academic context", "Use official sources for requirements and peer-reviewed sources for writing context."),
                option("User-provided sources only", "Use only sources supplied by the user and mark missing official facts as gaps."),
            ],
        ),
    ]
    if route == "application_writing_studio":
        questions.append(
            question(
                "Writing",
                "writing_brief_and_evidence",
                "What must be locked before the admissions writing plan is drafted?",
                [
                    option("Brief + evidence first (Recommended)", "Lock programme, prompt, word limit, applicant evidence, and source-backed fit facts first."),
                    option("Narrative options first", "Start with several evidence-limited story directions before selecting one."),
                    option("Revise supplied draft", "Use the existing draft as the main object and audit it for unsupported claims."),
                ],
            )
        )
    elif plan["profile_gaps"]:
        questions.append(
            question(
                "Profile",
                "profile_gaps",
                "Which missing applicant detail should be resolved first?",
                [
                    option(f"{plan['profile_gaps'][0].title()} (Recommended)", "This field materially changes requirement or shortlist interpretation."),
                    option("Continue with gaps marked", "Proceed but mark missing applicant facts as blockers or unknowns."),
                    option("Use supplied programme only", "Ignore broad applicant fit and audit only the named programme requirements."),
                ],
            )
        )
    else:
        questions.append(
            question(
                "Output",
                "route_specific_follow_up",
                "What output should be produced after route confirmation?",
                [
                    option("Source-backed table (Recommended)", "Return a compact table with source URLs and access dates."),
                    option("Checklist", "Return a blocker-focused action checklist."),
                    option("Workbook-ready case", "Prepare structured case data suitable for the workbook renderer."),
                ],
            )
        )
    return {"questions": questions}


def load_setup(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def self_test() -> None:
    payload = build_payload("help with my personal statement")
    assert len(payload["questions"]) == 3
    assert payload["questions"][0]["id"] == "application_route"
    assert payload["questions"][2]["id"] == "writing_brief_and_evidence"
    req = build_payload("check IELTS requirements", {"profile": {"target_degree_level": "undergraduate"}})
    assert req["questions"][0]["options"][0]["label"].startswith("Requirement Audit")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build request_user_input payloads for University Application review gates.")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--setup-json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("OK: build_review_questions self-test passed")
        return
    print(json.dumps(build_payload(args.prompt, load_setup(args.setup_json)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
