---
name: study-abroad-advisor
description: Build source-backed international university application plans, program shortlists, requirement tables, document checklists, essay/SOP plans, visa-readiness notes, and application workbooks.
---

# University Application Skill

Use this skill when the user asks for university admissions planning, study-abroad program research, application strategy, requirement checking, essay/SOP planning, scholarship planning, visa-readiness notes, or application workbooks.

## Rules

- Use official university, government, testing-agency, and scholarship sources when requirements, deadlines, fees, visa rules, or program availability may change.
- Record source URLs and access dates for every requirement used in a recommendation.
- Separate verified requirements from inferred fit advice.
- Do not invent rankings, deadlines, entry requirements, visa rules, scholarships, or acceptance probabilities.
- Mark missing evidence as a blocker or gap.
- Ask only for missing inputs that materially change the plan.

## Workflow

1. Setup: capture `workflow_mode`, `output_mode`, source policy, privacy/export settings, and applicant-specific fields under `profile`; validate setup JSON when available.
2. Intake: applicant profile, target country, degree level, subject, budget, timeline, language scores, academic records, constraints, and output format.
3. Source collection: official program pages, admissions pages, fee pages, scholarship pages, visa pages, and test-provider pages.
4. Structured case file: applicant, target routes, programs, requirements, documents, deadlines, risks, tasks, and source log.
5. Shortlist: separate eligibility, competitiveness, fit, cost, timing, and risk.
6. Gap review: missing prerequisites, missing documents, language tests, portfolio/research-proposal needs, funding gaps, visa risks, and deadline conflicts.
7. Output: chat summary, table, workbook, essay plan, document checklist, timeline, or source-backed action plan.
8. Quality check: verify every hard requirement against a source before presenting it as final.

## Reference files

- `references/intake.md`: applicant intake and missing-field handling.
- `references/research.md`: source collection and citation rules.
- `references/programme-table-cleaning.md`: cleaning official program tables.
- `references/workbook-schema.md`: workbook sheet structure.
- `references/essay-sop.md`: SOP and essay planning.
- `references/submission.md`: submission checklist.
- `references/quality-checks.md`: blocker and source checks.
- `references/setup/setup-workflow.md`: interactive setup flow.
- `references/setup/task-gates.yaml`: minimum fields by workflow mode.
- `references/setup/user-setup.schema.json`: setup JSON shape.

## Local scripts

- `scripts/validate_setup.py <setup.json>`: check setup completeness for `workflow_mode` and `output_mode`.
- `scripts/build_admissions_workbook.py <case.json> <output.xlsx>`: render a source-backed workbook.
- `scripts/onboard_admissions.py`: create a blank setup JSON template; fill required gate fields before validation.
- `scripts/check_setup_contract.py`: check setup schema, gates, fixtures, and template drift.
- `scripts/clean_programme_workbooks.py`: clean official program tables.
- `scripts/verify_programme_workbooks.py`: verify cleaned program workbooks.
