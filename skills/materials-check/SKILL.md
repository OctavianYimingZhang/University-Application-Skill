---
name: materials-check
description: Application materials readiness workflow for University Application Skill. Use when the user wants to simulate submission, check transcripts, language tests, references, passports, personal statements, fees, portfolios, or other documents against source-backed programme requirements.
---

# Materials Check

Use this focused Skill to simulate application submission readiness.

## Workflow

1. Read [`../../references/submission.md`](../../references/submission.md), [`../../references/quality-checks.md`](../../references/quality-checks.md), and [`../../references/evidence-contract.md`](../../references/evidence-contract.md).
2. Load or build the programme's source-backed document requirements for the current application cycle.
3. Collect normalized evidence records from the user. Keep the shipped default empty.
4. Check each required item for presence, evidence date, explicit confirmation, fact verification, completeness, application cycle, source availability, access date, staleness, format, and source-specific constraints.
5. Mark a required document present only when applicant-owned `local_document` evidence passes `material_document`; an official requirement page proves what is required, not that the applicant possesses the file. Use the separate `submission` purpose for the broader submission gate. `user_confirmation` alone cannot mark a required material complete. Applicant facts used only for writing or comparison may still use confirmed local or user provenance without completing the material itself. Otherwise use `unresolved`, `fail`, or `not_required` as appropriate.
6. Route SOP, personal statement, or supplemental essay gaps to `application-writing-studio`.

## Output

Produce a materials checklist, blockers, evidence gaps, and a submission-readiness summary. Do not claim that a real application was submitted.

Default to English. Use another output language only when the user explicitly requests it.
