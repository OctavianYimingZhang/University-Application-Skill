---
name: study-abroad-advisor
description: Source-backed university application planning and execution system. Use for international admissions research, programme shortlists, exact programme selection, requirement audits, materials readiness checks, SOP/personal-statement planning, submission readiness, visa-readiness notes, admissions workbooks, and official programme-table cleaning.
---

# University Application Skill

Use this Skill when the user asks for university admissions planning, study-abroad programme research, application strategy, requirement checking, essay/SOP planning, document readiness, scholarship or visa-readiness notes, or application workbooks.

## Core Rules

- Use official university, government, testing-agency, and scholarship sources when requirements, deadlines, fees, visa rules, or programme availability may change.
- Record source URLs and access dates for every hard requirement used in an output.
- Separate verified requirements from interpretation, fit advice, or planning suggestions.
- Do not invent rankings, deadlines, entry requirements, language rules, visa rules, scholarships, outcomes, or acceptance probabilities.
- Do not produce chance scores, safe/match/reach labels, or admission-probability predictions.
- Mark missing evidence as a gap or blocker.
- Ask only for missing inputs that materially change the plan.

## Multiple Skill System

This root Skill is the complete workflow contract. For new work, load `university-application-index` first when the route is not already confirmed. The index confirms the application task, source policy, and applicant-profile gaps, then routes to focused Skills.

| User request | Focused Skill |
| --- | --- |
| broad admissions help, shortlist, route unclear | [`university-application-index`](skills/university-application-index/SKILL.md) |
| programme discovery or official-source research | [`program-research`](skills/program-research/SKILL.md) |
| audit hard requirements for named programmes | [`requirement-audit`](skills/requirement-audit/SKILL.md) |
| simulate application-material readiness | [`materials-check`](skills/materials-check/SKILL.md) |
| brainstorm SOP, personal statement, supplement, or programme-fit writing | [`application-writing-studio`](skills/application-writing-studio/SKILL.md) |
| final submission checklist and blockers | [`submission-readiness`](skills/submission-readiness/SKILL.md) |
| clean official programme tables/workbooks | [`programme-table-cleaning`](skills/programme-table-cleaning/SKILL.md) |

If a focused Skill is installed as a sibling local Skill, prefer that installed focused Skill. If not, follow the linked source entrypoint and shared references in this package.

## Workflow

1. Setup: capture `workflow_mode`, `output_mode`, source policy, privacy/export settings, and applicant-specific fields under `profile`; validate setup JSON when available.
2. Intake: applicant profile, target country, degree level, subject, budget, intake, language scores, academic records, constraints, and output format.
3. Route review: use `scripts/plan_workflow.py` and `scripts/build_review_questions.py` or equivalent `request_user_input` payloads when the route, source policy, or applicant gaps materially affect the result.
4. Source collection: official programme pages, admissions pages, fee pages, scholarship pages, visa pages, and test-provider pages.
5. Structured case file: applicant, target routes, programmes, requirements, documents, deadlines, writing tasks, risks, tasks, and source log.
6. Hard-requirement audit: separate academic, language, subject, document, fee, deadline, and route-specific requirements from interpretation.
7. Materials check: simulate submission readiness by checking each required item against the programme source and applicant evidence.
8. Writing Studio: lock the writing brief, build evidence inventory, generate narrative options, map programme fit, review unsupported claims, then request planning approval before drafting.
9. Output: chat summary, table, workbook, essay plan, document checklist, timeline, source-backed action plan, or website case view.
10. Quality check: verify every hard requirement against a source before presenting it as final.

## Writing Studio Contract

Admissions writing is a planning and evidence task before it is a drafting task.

- Lock the writing brief before planning: programme, prompt, word limit, audience, submission use, applicant background, and source policy.
- Build an evidence inventory from the applicant before making claims.
- Generate multiple narrative options only from supplied evidence.
- Block unsupported claims about achievements, hardship, leadership, research, publications, awards, internships, or conversations.
- Use programme-specific facts only after source verification.
- Build the programme-fit paragraph from verified modules, research groups, facilities, teaching structure, placement, accreditation, or faculty fit.
- Ask for planning approval after the structure and evidence map are visible. Once approved, draft without asking a redundant start-writing question.
- If a plan-breaking issue appears after approval, return to the writing gate instead of silently changing the structure.

## Reference Files

- `references/intake.md`: applicant intake and missing-field handling.
- `references/research.md`: official-source collection and citation rules.
- `references/programme-table-cleaning.md`: cleaning official programme tables.
- `references/workbook-schema.md`: workbook sheet structure.
- `references/essay-sop.md`: SOP and essay planning.
- `references/submission.md`: submission checklist.
- `references/quality-checks.md`: blocker and source checks.
- `references/setup/setup-workflow.md`: interactive setup flow.
- `references/setup/task-gates.yaml`: minimum fields by workflow mode.
- `references/setup/user-setup.schema.json`: setup JSON shape.

## Local Scripts

- `scripts/plan_workflow.py`: detect and describe a route from a prompt or setup JSON.
- `scripts/build_review_questions.py`: build route/source/profile/writing review payloads.
- `scripts/validate_skill_contracts.py`: check manifest, focused Skills, route scripts, and website source contracts.
- `scripts/publish_skill.py`: push and/or sync this multi-skill package into local Codex Skills.
- `scripts/validate_setup.py <setup.json>`: check setup completeness for `workflow_mode` and `output_mode`.
- `scripts/build_admissions_workbook.py <case.json> <output.xlsx>`: render a source-backed workbook.
- `scripts/onboard_admissions.py`: create a blank setup JSON template.
- `scripts/check_setup_contract.py`: check setup schema, gates, fixtures, and template drift.
- `scripts/clean_programme_workbooks.py`: clean official programme tables.
- `scripts/verify_programme_workbooks.py`: verify cleaned programme workbooks.
