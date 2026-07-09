---
name: university-application-index
description: Canonical controller for University Application requests. Route programme research, requirement audits, materials checks, admissions writing, submission readiness, student visa readiness, explicit programme-catalogue maintenance, and memory orchestration after inspecting the prompt, profile gaps, source policy, and output mode; recognize intent expressed in languages other than English.
---

# University Application Index

Use this Skill as the controller for the University Application multiple Skill system.

## Required Workflow

1. Inspect supplied prompts, setup JSON, applicant profile, programme URLs, screenshots, tables, documents, and memory exports before choosing a public route. Treat raw applicant values as unconfirmed.
2. Use [`../../scripts/plan_workflow.py`](../../scripts/plan_workflow.py) or equivalent semantic logic to produce a preliminary route and output plan. Recognize non-English intent without changing the default output language.
3. Display the route diagnosis when it materially affects output.
4. Use [`../../scripts/build_review_questions.py`](../../scripts/build_review_questions.py) or equivalent `request_user_input` payloads to confirm or correct:
   - application route;
   - source policy;
   - missing applicant profile fields;
   - memory category needed, if any;
   - writing gates when SOP or personal statement work is requested.
5. Keep proposed `AcademicTaskContext` routes and decisions at `suggested`; set them to `explicitly_confirmed` only after the user selects them.
6. Apply the user's answers and route to the focused Skill.
7. Keep official-source requirements separate from strategic interpretation.
8. Use blank memory and applicant-evidence defaults when no user-supplied data exists.

## Focused Routing

| Confirmed route | Focused Skill |
| --- | --- |
| `program_research` | [`program-research`](../program-research/SKILL.md) |
| `requirement_audit` | [`requirement-audit`](../requirement-audit/SKILL.md) |
| `materials_check` | [`materials-check`](../materials-check/SKILL.md) |
| `application_writing_studio` | [`application-writing-studio`](../application-writing-studio/SKILL.md) |
| `submission_readiness` | [`submission-readiness`](../submission-readiness/SKILL.md) |
| `visa_readiness` | [`visa-readiness`](../visa-readiness/SKILL.md) |
| `programme_table_cleaning` | [`programme-table-cleaning`](../programme-table-cleaning/SKILL.md), only for explicit maintenance requests |
| `memory_pack` | Use [`../../references/memory-system.md`](../../references/memory-system.md) and the package memory contract. |

For broad shortlist work, use `program-research` first, then `requirement-audit` for named programmes.

## Shared Rules

- Official sources are required for hard requirements, deadlines, fees, and programme availability.
- Missing source evidence is a gap, not a reason to guess.
- Apply [`../../references/evidence-contract.md`](../../references/evidence-contract.md) before any applicant value passes a requirement, materials, writing, or submission gate.
- Do not calculate admission probabilities or label programmes as safe, match, or reach.
- Route-specific questions should be compact and material to the plan.
- Do not import populated user memory from the public repository; memory must come from the current user, a private local file, or an explicit browser export.
- Default to English. Use another output language only when the user explicitly requests it.
