---
name: university-application-index
description: Route broad University Application Skill requests after inspecting the prompt, applicant profile, target level, source policy, and output mode. Use for programme shortlists, exact programme selection, requirement audits, materials readiness, SOP/personal-statement planning, submission readiness, visa-readiness notes, and programme-table cleaning when the route is not already confirmed.
---

# University Application Index

Use this Skill as the controller for the University Application multiple Skill system.

## Required Workflow

1. Inspect supplied prompts, setup JSON, applicant profile, programme URLs, screenshots, tables, and documents before choosing a public route.
2. Use `scripts/plan_workflow.py` or equivalent logic to produce a preliminary route and output plan.
3. Display the route diagnosis when it materially affects output.
4. Use `scripts/build_review_questions.py` or equivalent `request_user_input` payloads to confirm or correct:
   - application route;
   - source policy;
   - missing applicant profile fields;
   - writing gates when SOP or personal statement work is requested.
5. Apply the user's answers and route to the focused Skill.
6. Keep official-source requirements separate from strategic interpretation.

## Focused Routing

| Confirmed route | Focused Skill |
| --- | --- |
| `program_research` | [`program-research`](../program-research/SKILL.md) |
| `requirement_audit` | [`requirement-audit`](../requirement-audit/SKILL.md) |
| `materials_check` | [`materials-check`](../materials-check/SKILL.md) |
| `application_writing_studio` | [`application-writing-studio`](../application-writing-studio/SKILL.md) |
| `submission_readiness` | [`submission-readiness`](../submission-readiness/SKILL.md) |
| `programme_table_cleaning` | [`programme-table-cleaning`](../programme-table-cleaning/SKILL.md) |

For broad shortlist work, use `program-research` first, then `requirement-audit` for named programmes.

## Shared Rules

- Official sources are required for hard requirements, deadlines, fees, and programme availability.
- Missing source evidence is a gap, not a reason to guess.
- Do not calculate admission probabilities or label programmes as safe, match, or reach.
- Route-specific questions should be compact and material to the plan.
