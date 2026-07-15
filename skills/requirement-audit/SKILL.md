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
   - application form fields and portal instructions;
   - personal-statement, SOP, proposal, or supplemental prompts;
   - word or character limits and file-format rules;
   - published AI-use or authorship rules;
   - fees and deposits;
   - deadlines and staged admissions;
   - references and referee procedures;
   - mandatory, recommended, optional, or unnecessary supervisor contact and other pre-application steps;
   - citizenship or visa-sensitive requirements.
4. Validate official requirements with `--purpose official_requirement --current-cycle <cycle>`. Use `applicant_comparison` for confirmed applicant facts; local documents or explicit user confirmation may support those personal facts, but cannot verify an official rule or complete a document gate.
5. Classify the requirement itself as `required`, `recommended`, `optional`, `not_required`, or `unknown`, then classify applicant status separately as `pass`, `gap`, `risk`, `not_applicable`, or `unknown`.
6. Explain unknowns plainly and do not infer eligibility when evidence is missing.

## Output

Explain the requirements directly and use a compact requirement table, gap list, and source log where useful. Create a next-action checklist only when the user explicitly asks for one.

Default to English. Use another output language only when the user explicitly requests it.
