---
name: requirement-audit
description: Hard-requirement audit for named university programmes. Use when the user needs exact academic, language, subject, document, fee, deadline, or route requirements checked against official sources and separated from fit advice.
---

# Requirement Audit

Use this focused Skill for exact programme requirement checks.

## Workflow

1. Read [`../../references/research.md`](../../references/research.md), [`../../references/quality-checks.md`](../../references/quality-checks.md), and [`../../references/evidence-contract.md`](../../references/evidence-contract.md).
2. Collect the official programme page plus admissions, fee, English-language, scholarship, and government pages when relevant.
3. Extract only verified requirements:
   - academic qualification and grade;
   - subject prerequisites;
   - English tests and component scores;
   - documents;
   - fees and deposits;
   - deadlines and staged admissions;
   - citizenship or visa-sensitive requirements.
4. Compare the applicant profile to each requirement only when its normalized evidence record passes the evidence invariant. Empty, placeholder, link-only, partial, unverified, or unconfirmed values remain `unknown`.
5. Classify each item as `pass`, `gap`, `risk`, `not_applicable`, or `unknown`.
6. Explain unknowns plainly and do not infer eligibility when evidence is missing.

## Output

Return a requirement table, gap list, source log, and next-action checklist.

Default to English. Use another output language only when the user explicitly requests it.
