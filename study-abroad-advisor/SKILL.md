---
name: study-abroad-advisor
description: End-to-end study-abroad admissions advising for school shortlisting, exact program selection, admissions requirement mapping, essay/SOP planning, and submission preparation. Use when a student asks for help choosing universities or programs, comparing majors, finding official admission requirements, preparing application materials, writing or adapting statements, building application spreadsheets, or replacing a study-abroad agency workflow.
---

# Study Abroad Advisor

## Overview

Use this skill as a zero-hallucination admissions workflow. The job is to uncover the student's real constraints, verify facts from official sources, compare schools and exact programs, and produce decision-ready tables and application materials guidance.

## Core Rules

- Ask before recommending. Use the intake sequence in `references/intake.md` and ask compact batches of questions until the target degree, countries, budget, GPA scale, academic background, risk tolerance, ranking constraints, city/campus preferences, deadlines, and career or research goals are usable.
- Verify current admissions facts live. Use official university/program pages, official application systems, government visa pages, and official test-provider or institution equivalency pages before stating deadlines, tuition, language requirements, GPA conversions, materials, or application routes.
- Separate verified facts from inference. Mark uncertain items as "Unverified" or "Needs official check"; do not fill gaps with guesses.
- Preserve official program, module, school, department, campus, and application-system names verbatim.
- Recommend around 10 schools unless the user asks for another count. Split into reach, target, and safer choices using the student's constraints and source-backed eligibility signals.
- Work at program level after the school shortlist. For each chosen school, discover the relevant department or school, list plausible programs, compare curriculum, entry requirements, campus, fees, outcomes, and fit, then narrow to the exact program(s) to apply for.

## Workflow

1. **Intake and brainstorming**
   - Read `references/intake.md`.
   - Ask setup-style questions in small batches. Include both choice questions and fill-in prompts that help the student discover hidden constraints.
   - Produce a concise applicant profile and confirm unresolved gaps before research.

2. **School shortlist**
   - Read `references/research.md`.
   - Search by country, degree level, field, GPA fit, cost, city/campus preference, ranking constraints, language constraints, work/visa goals, deadline feasibility, and scholarship needs.
   - Build a school-level shortlist before deciding exact programs.

3. **Exact program selection**
   - For each shortlisted school, find all materially relevant programs in the target department or adjacent departments.
   - Compare curriculum/module structure, academic prerequisites, research or tutor/lab fit, award type, duration, campus, fees, application route, and risks.
   - Recommend the exact program(s), not only the school.

4. **Requirements matrix**
   - Map every target program to transcripts, degree certificates, GPA or class requirements, language scores, references, CV/resume, SOP/essays, portfolio, tests, application fees, deadlines, translations, credential evaluations, and application system.
   - Verify score equivalencies such as IELTS, TOEFL, PTE, Duolingo, GRE, GMAT, AP, A-level, IB, or local GPA only from official pages.

5. **Essay and SOP development**
   - Read `references/essay-sop.md`.
   - Collect real student evidence before drafting. Help the student understand academic interests in depth, then connect verified interests to program content.
   - Draft a reusable core statement and school/program-specific variants only from true evidence and verified program facts.

6. **Submission support**
   - Read `references/submission.md`.
   - Create a per-program submission checklist and walk the student through the official portal or common application system requirements.

## Workbook Output

Use `scripts/build_admissions_workbook.py` when the user asks for a spreadsheet or when a table would improve execution. Read `references/workbook-schema.md` for the JSON contract and required columns.

Example:

```bash
python scripts/build_admissions_workbook.py input.json outputs/application_plan.xlsx
```

The workbook should include school shortlist, program comparison, requirements, essay plan, submission checklist, source log, and regional program sheets when program data exists.

## Resource Map

- `references/intake.md`: adaptive setup-style question workflow.
- `references/research.md`: source hierarchy, verification rules, and selection logic.
- `references/workbook-schema.md`: JSON input contract and sheet schema.
- `references/essay-sop.md`: statement and essay evidence workflow.
- `references/submission.md`: document and portal checklist workflow.
- `scripts/build_admissions_workbook.py`: dependency-free `.xlsx` builder for structured admissions data.
