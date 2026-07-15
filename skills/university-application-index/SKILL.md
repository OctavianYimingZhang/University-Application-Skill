---
name: university-application-index
description: Canonical controller for University Application requests. Route programme research, requirement audits, materials checks, admissions writing, submission readiness, student visa readiness, explicit programme-catalogue maintenance, and memory orchestration after inspecting the prompt, profile gaps, source policy, and output mode; recognize intent expressed in languages other than English.
---

# University Application Index

Use this Skill as the controller for the University Application multiple Skill system.

## Required Workflow

1. Inspect supplied prompts, setup JSON, applicant profile, programme URLs, screenshots, tables, documents, and memory exports before choosing a public route. Treat raw applicant values as unconfirmed.
2. Use [`../../scripts/plan_workflow.py`](../../scripts/plan_workflow.py) or equivalent semantic logic to produce `route_status = matched | needs_confirmation | out_of_scope`. Only `matched` carries a real route. Do not default unknown or generic Word-formatting requests to programme research.
3. Route explicit acts before incidental vocabulary: drafting or revision goes to `application_writing_studio` even when portal or submission wording is incidental; review of the applicant's current materials goes to `materials_check` even when the inventory mentions IELTS or another requirement. Route a combined supervisor research/publication-fit and contact-status request to `program_research`; route a contact-requirement-only check to `requirement_audit`. Other application-document, prompt, limit, AI-policy, fee, cycle, deadline, or pre-contact requirements go to `requirement_audit`.
4. Use [`../../scripts/build_review_questions.py`](../../scripts/build_review_questions.py) in batches of at most three. Ask only unresolved, route-specific inputs. Do not repeat route, source-policy, degree-filter, or output-format questions when direct intent already resolves them. Carry `next_reviewed_question_ids` forward through `--reviewed-question-id`; this stable cursor prevents regenerated gaps or normalized ledger items from being skipped. Use positional `next_batch_start` only when the question set is unchanged and no cursor is available. If the payload has `request_user_input_required: false` and `questions: []`, do not call `request_user_input`; continue directly with the matched route.
5. Keep proposed `AcademicTaskContext` routes and decisions at `suggested`; set them to `explicitly_confirmed` only after the user selects them.
6. Apply the user's answers and route to the focused Skill.
7. Keep official-source requirements separate from strategic interpretation.
8. Use blank memory and applicant-evidence defaults when no user-supplied data exists.
9. Preserve one `ApplicationCase` per programme and keep shared applicant narrative separate from programme-specific supervisor, course, evidence, document, and writing adaptations.

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

`needs_confirmation` and `out_of_scope` are dispositions, not focused routes. Generic file backup, Word beautification, or unrelated document formatting stays out of scope unless the user states an admissions-writing task.

## Shared Rules

- Official sources are required for hard requirements, deadlines, fees, and programme availability.
- Missing source evidence is a gap, not a reason to guess.
- Apply [`../../references/evidence-contract.md`](../../references/evidence-contract.md) with the correct purpose. Official facts require `public_url`; applicant writing may use a verified local document or explicit user confirmation; `material_document` requires available applicant `local_document` evidence, while submission cannot pass from user confirmation alone.
- Do not calculate admission probabilities or label programmes as safe, match, or reach.
- Route-specific questions should be compact and material to the plan.
- Explain requirements directly or in a compact table by default. Generate a checklist only when explicitly requested or when the user invokes a checklist-oriented readiness route.
- Do not import populated user memory from the public repository; memory must come from the current user, a private local file, or an explicit browser export.
- Default to English. Use another output language only when the user explicitly requests it.
