---
name: university-application
description: Route and complete source-backed university application work covering programme research, requirement comparison, admissions writing, materials readiness, submission preparation, and student-visa administration. Use when an applicant asks to find or compare programmes, verify current requirements, prepare application writing, check documents, or plan the remaining application steps.
---

# University Application

Help the applicant choose programmes, prepare truthful application materials, and reach submission with current evidence.

## Public Skills

- `application-research`: programme discovery, exact degree-type filtering, official requirements, supervisor and programme fit, costs, deadlines, catalogue maintenance, tables, and workbooks.
- `application-writing`: SOPs, personal statements, supplemental essays, programme-fit paragraphs, planning, drafting, and revision.
- `application-readiness`: materials, portal fields, references, tests, fees, scholarships, deadlines, submission blockers, and administrative student-visa preparation.

## Routing

1. Read the request and supplied applicant or programme material.
2. Select the focused Skill that directly produces the requested result.
3. Use more than one focused Skill when the request explicitly combines research, writing, and readiness work.
4. Send a named-programme requirement check to Research; send comparison against the applicant's current documents or next actions to Readiness.
5. Ask one concise question only when a missing input would materially change the result, such as target degree type, application cycle, writing prompt, word limit, document inventory, destination jurisdiction, or citizenship.
6. Complete the work and verify the finished output.

Follow the explicit user request; treat file names and incidental terminology as secondary context.

## Shared Rules

Read `references/evidence-contract.md` for every task, then read the focused reference:

- Research: `references/research.md`
- Writing: `references/essay-sop.md`
- Readiness: `references/submission.md`

Use current official university, government, testing-agency, and scholarship sources for facts that can change. Record the source URL and access date, and keep official requirements, applicant evidence, strategic interpretation, and unresolved gaps distinct.

Treat a catalogue row as a programme identity that still needs current-page verification. Verify exact awards such as `MPhil`, `MRes`, and `MSc by Research` instead of inferring degree type from the subject name.

Use applicant facts supplied or confirmed by the applicant. Treat uploaded writing samples as voice evidence and supplied course material as knowledge or interest evidence. Promote either to personal-achievement evidence only after applicant confirmation.

Report verified eligibility factors, programme fit, evidence gaps, and next actions as qualitative, evidence-based findings.

Use the user's requested output language; otherwise use English. Explain requirements directly or in a compact table. Use an action checklist when the user requests one or when a readiness review naturally requires it.

## Tools

- `scripts/validate_evidence.py`: validate official and applicant evidence.
- `scripts/extract_inspiration_file.py`: extract labelled content from applicant-supplied writing inspiration files.
- `scripts/build_admissions_workbook.py`: create an admissions workbook from structured input.
- `scripts/clean_programme_workbooks.py` and `scripts/verify_programme_workbooks.py`: maintain supplied programme tables.
- `scripts/validate_catalogues.py`: validate the curated programme identity catalogue.
- `scripts/validate_skill_contracts.py`: validate the simplified Plugin and four public Skills.
- `scripts/publish_skill.py`: synchronise and compare the four local Skill installations.

## Completion

Check that mutable facts have current official provenance, applicant claims are supported, requested fields are present, and unresolved facts are labelled. Inspect generated office documents before delivery when rendering tools are available.
