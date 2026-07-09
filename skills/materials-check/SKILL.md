---
name: materials-check
description: Application materials readiness workflow for University Application Skill. Use when the user wants to simulate submission, check transcripts, language tests, references, passports, personal statements, fees, portfolios, or other documents against source-backed programme requirements.
---

# Materials Check

Use this focused Skill to simulate application submission readiness.

## Workflow

1. Read [`../../references/submission.md`](../../references/submission.md), [`../../references/quality-checks.md`](../../references/quality-checks.md), and [`../../references/evidence-contract.md`](../../references/evidence-contract.md).
2. Load or build the programme's source-backed document checklist.
3. Collect normalized evidence records from the user. Keep the shipped default empty.
4. Check each required item for presence, evidence date, explicit confirmation, fact verification, completeness, application cycle, source availability, access date, staleness, format, and source-specific constraints.
5. Mark an item `pass` only when its evidence record satisfies the passing invariant; otherwise use `unresolved`, `fail`, or `not_required` as appropriate.
6. Route SOP, personal statement, or supplemental essay gaps to `application-writing-studio`.

## Output

Produce a materials checklist, blockers, evidence gaps, and a submission-readiness summary. Do not claim that a real application was submitted.

Default to English. Use another output language only when the user explicitly requests it.
