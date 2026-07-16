---
name: university-application
description: Route and complete source-backed university application work covering programme research, requirement comparison, admissions writing, materials readiness, submission preparation, student-visa administration, and programme-data maintenance. Use when an applicant asks to find or compare programmes, verify current requirements, prepare writing, check documents, plan visa steps, or maintain programme tables and catalogues.
---

# University Application

Help the applicant choose programmes, prepare truthful application materials, and reach submission with current evidence.

## Public Skills

- `application-research`: programme discovery, exact degree-type filtering, official requirements, supervisor and programme fit, costs, deadlines, and applicant-facing comparisons.
- `application-writing`: SOPs, personal statements, supplemental essays, programme-fit paragraphs, planning, drafting, and revision.
- `application-readiness`: materials, portal fields, references, tests, fees, scholarships, deadlines, and submission blockers.
- `application-visa`: jurisdiction-specific administrative student-visa requirements, evidence, timelines, and next actions.
- `application-data`: programme catalogue, table, CSV, XLSX, and workbook maintenance with lineage and validation.

## Skill Boundaries

Treat the manifest-declared Skill list as the current architecture rather than a fixed quota. Split a focused Skill when its trigger intent, evidence authority, workflow, toolchain, or output is materially independent. Merge focused Skills when those elements are shared and the variants can be handled reliably by one workflow.

## Routing

1. Read the request and supplied applicant or programme material.
2. Select the focused Skill that directly produces the requested result.
3. Use more than one focused Skill when the request explicitly combines applicant research, writing, readiness, visa, or programme-data work.
4. Send a named-programme requirement check to Research; send comparison against the applicant's current documents or next actions to Readiness.
5. Route visa rules and administrative immigration steps to Visa. Route explicit catalogue, table, or workbook maintenance to Application Data.
6. Ask one concise question only when a missing input would materially change the result, such as target degree type, application cycle, writing prompt, word limit, document inventory, destination jurisdiction, citizenship, or supplied data schema.
7. Complete the work and verify the finished output.

Follow the explicit user request; treat file names and incidental terminology as secondary context.

## Shared Rules

Read `references/evidence-contract.md` for every task, then read the focused reference:

- Research: `references/research.md`
- Writing: `references/essay-sop.md`
- Readiness: `references/submission.md`
- Visa: `references/submission.md`
- Programme Data: `references/research.md` and `catalogues/README.md`

Use current official university, government, testing-agency, and scholarship sources for facts that can change. Record the source URL and access date, and keep official requirements, applicant evidence, strategic interpretation, and unresolved gaps distinct.

Treat a catalogue row as a programme identity that still needs current-page verification. Verify exact awards such as `MPhil`, `MRes`, and `MSc by Research` instead of inferring degree type from the subject name.

Use applicant facts supplied or confirmed by the applicant. Treat uploaded writing samples as voice evidence and supplied course material as knowledge or interest evidence. Promote either to personal-achievement evidence only after applicant confirmation.

Report verified eligibility factors, programme fit, evidence gaps, and next actions as qualitative, evidence-based findings.

Use the user's requested output language; otherwise use English. Explain requirements directly or in a compact table. Use an action checklist when the user requests one or when a readiness review naturally requires it.

## Tools

- `scripts/validate_evidence.py`: validate official and applicant evidence.
- `scripts/extract_inspiration_file.py`: extract labelled content from applicant-supplied writing inspiration files.
- `scripts/build_admissions_workbook.py`: create an applicant-facing admissions workbook from structured input.
- `scripts/clean_programme_workbooks.py` and `scripts/verify_programme_workbooks.py`: maintain supplied programme data.
- `scripts/validate_catalogues.py`: validate the curated programme identity catalogue.
- `scripts/validate_skill_contracts.py`: validate the manifest-driven Plugin architecture.
- `scripts/publish_skill.py`: synchronise and compare the manifest-declared local Skill installations.

## Completion

Check that mutable facts have current official provenance, applicant claims are supported, requested fields are present, and unresolved facts are labelled. Inspect generated office documents before delivery when rendering tools are available.
