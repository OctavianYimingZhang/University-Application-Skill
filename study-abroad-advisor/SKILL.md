---
name: study-abroad-advisor
description: End-to-end study-abroad admissions advising for school shortlisting, exact program selection, admissions requirement mapping, essay/SOP planning, submission preparation, and official programme table cleaning. Use when a student asks for help choosing universities or programs, comparing majors, finding official admission requirements, preparing application materials, writing or adapting statements, building or cleaning application spreadsheets, or replacing a study-abroad agency workflow.
---

# Study Abroad Advisor

## Overview

Use this skill as a zero-hallucination admissions operating ontology. The job is to turn international admissions work into source-backed objects, links, state transitions, actions, and views so the agent can reason over complex multi-country application cases without inventing facts.

## Core Rules

- Ask before recommending. Use the intake sequence in `references/intake.md` and ask compact batches of questions until the target degree, countries, budget, GPA scale, academic background, risk tolerance, ranking constraints, city/campus preferences, deadlines, and career or research goals are usable.
- Verify current admissions facts live. Use official university/program pages, official application systems, government visa pages, and official test-provider or institution equivalency pages before stating deadlines, tuition, language requirements, GPA conversions, materials, or application routes.
- Separate verified facts from inference. Mark uncertain items as "Unverified" or "Needs official check"; do not fill gaps with guesses.
- Treat the ontology objects as the source of truth. Workbooks, dashboards, checklists, and written advice are views over objects, not the primary data model.
- Every material fact must attach to `SourceEvidence` or remain blocked. This includes deadlines, fees, test scores, language waivers, visa rules, work rights, GPA equivalencies, document rules, and application-system routes.
- Do not produce final recommendations directly from raw web pages. Use the data lifecycle: `SourceSnapshot -> ExtractedFact -> verified RequirementRule / ProgramFitFact -> ApplicationCase / RiskFlag / View`.
- Every rendered workbook row, essay claim, risk flag, recommendation, and checklist item must be traceable through `LineageEdge` records to upstream evidence.
- Run ontology quality checks before producing verified outputs. A failed blocker check must create a task or risk and prevent the state transition or verified workbook.
- Support two explicit output tracks. Draft track is allowed for brainstorming, scoping, missing-field reports, and research plans, but must label unverified facts and cannot be called final. Verified track requires `SourceEvidence`, lineage, freshness policy, and quality checks before final recommendations, verified workbooks, final checklists, submission state transitions, or visa-ready status.
- Start with setup mode when the user's request is broad or ambiguous. Use `UserSetup`, `PreferenceWeight`, and `InteractionState` to capture the current workflow mode, output reliability, privacy/export preference, preference weights, missing fields, blockers, and next questions before exposing ontology internals.
- Use task-scoped gates. Do not force full intake for requirement audits, essay planning, workbook rendering, source refresh, or visa-route research when a smaller task gate is sufficient.
- Advance workflow state only through gates and actions. Do not mark an `ApplicationCase` submitted, visa-ready, or complete until required objects, verified rules, source logs, and document states satisfy the gate.
- Preserve official program, module, school, department, campus, and application-system names verbatim.
- Recommend around 10 schools unless the user asks for another count. Split into reach, target, and safer choices using the student's constraints and source-backed eligibility signals.
- Work at program level after the school shortlist. For each chosen school, discover the relevant department or school, list plausible programs, compare curriculum, entry requirements, campus, fees, outcomes, and fit, then narrow to the exact program(s) to apply for.
- When cleaning programme-list workbooks for publication, use the objective 11-column official-information format in `references/programme-table-cleaning.md`; remove ranking, geography, department, subjective fit/risk, and internal QA columns from that export.

## Workflow

1. **Setup and task routing**
   - Read `references/setup/setup-workflow.md`, `references/setup/onboarding-flow.yaml`, and `references/setup/task-gates.yaml`.
   - If the user has not chosen a mode, ask the smallest setup batch: workflow mode, output mode, target degree/field/country shape, and whether the desired output is draft or verified.
   - Create or update `UserSetup`, `PreferenceWeight`, and `InteractionState` objects. Keep them separate from applicant facts.
   - Run `scripts/validate_setup.py` when setup JSON exists. Run `scripts/doctor_admissions_case.py` when ontology JSON exists and the user needs a blocker report or next-question list.

2. **Intake and brainstorming**
   - Read `references/intake.md`.
   - Create or update `Applicant` and `EducationCredential` objects from the profile. Keep citizenship, residence country, education country, passport country, document language, and funding source country as separate fields.
   - Ask setup-style questions in small batches. Include both choice questions and fill-in prompts that help the student discover hidden constraints.
   - Produce a concise applicant profile and confirm unresolved gaps before research.

3. **Profile graph and route resolution**
   - Read `references/ontology.md`, `references/data-lifecycle.md`, and `references/ontology/workflow_gates.yaml`.
   - Resolve destination-country and degree-level routes before final checklists: for example UCAS, Common App, university portal, uni-assist, Studielink, Universityadmissions.se, DLI/LOA/study permit, CoE/subclass 500, or other official routes.
   - If route evidence is missing, create a blocking `Task` and mark the route as `needs_official_check`.

4. **School shortlist**
   - Read `references/research.md`.
   - Search by country, degree level, field, GPA fit, cost, city/campus preference, ranking constraints, language constraints, work/visa goals, deadline feasibility, and scholarship needs.
   - Build a school-level shortlist before deciding exact programs.

5. **Exact program selection**
   - For each shortlisted school, find all materially relevant programs in the target department or adjacent departments.
   - Compare curriculum/module structure, academic prerequisites, research or tutor/lab fit, award type, duration, campus, fees, application route, and risks.
   - Create or update `Institution`, `Program`, and `ApplicationCase` objects. Recommend the exact program(s), not only the school.

6. **Requirement rules and risk**
   - Map every target program to transcripts, degree certificates, GPA or class requirements, language scores, references, CV/resume, SOP/essays, portfolio, tests, application fees, deadlines, translations, credential evaluations, and application system.
   - Verify score equivalencies such as IELTS, TOEFL, PTE, Duolingo, GRE, GMAT, AP, A-level, IB, or local GPA only from official pages.
   - Store requirements as `RequirementRule` objects linked to `SourceEvidence`, not as free-text notes. Use `RiskFlag` objects for academic, budget, deadline, visa, document, source-conflict, and fit risks; never fabricate admission-probability percentages.
   - Run `scripts/validate_ontology.py` against structured ontology JSON when available, especially before rendering a verified workbook or final checklist.

7. **Essay and SOP development**
   - Read `references/essay-sop.md`.
   - Collect real student evidence before drafting. Help the student understand academic interests in depth, then connect verified interests to program content.
   - Draft a reusable core statement and school/program-specific variants only from true evidence and verified program facts. Every school-specific claim should map to `StudentEvidence`, `ProgramFitFact`, and `EssayClaim` objects.

8. **Materials, submission, and monitoring**
   - Read `references/submission.md`.
   - Create `DocumentArtifact` and `Task` objects for missing, expired, untranslated, unverified, uploaded, and submitted documents.
   - Walk the student through the official portal or common application system requirements.
   - After offer objects are created, trigger visa/residence-permit workflow only when official post-offer documents and route rules are verified.

## Workbook Output

Use `scripts/build_admissions_workbook.py` when the user asks for a spreadsheet or when a table would improve execution. Read `references/workbook-schema.md` for the JSON contract and required columns.

Example:

```bash
python scripts/build_admissions_workbook.py input.json outputs/application_plan.xlsx
```

The builder runs ontology quality checks before rendering when ontology data exists. Use `--skip-validation` only for explicitly draft, non-verified workbooks. The workbook should include object-state views, application cases, school shortlist, program comparison, requirement rules, document gaps, tasks, risk flags, visa route status, essay plan, submission checklist, source log, and regional program sheets when program data exists.

For cleaned official programme exports, read `references/programme-table-cleaning.md` and use:

```bash
python scripts/clean_programme_workbooks.py --source-dir input_workbooks --out-dir cleaned_workbooks
python scripts/verify_programme_workbooks.py --dir cleaned_workbooks
```

These scripts assume row 3 contains headers and data starts on row 4. Write to a separate output directory first; use `--copy-back` only when the user explicitly asks to overwrite source workbooks.

The cleaned export must keep `项目类型/学习方式` in `Type/Delivery/Mode/Duration` form, split `课程/训练内容` into knowledge topics, methods/tools, practical training, and outputs, and split `学术背景/限制条件` into degree/grade, subject background, prerequisites/skills, language, standardized tests, and work/qualification restrictions.

## Resource Map

- `references/intake.md`: adaptive setup-style question workflow.
- `references/research.md`: source hierarchy, verification rules, and selection logic.
- `references/ontology.md`: ontology-first operating model and state-machine rules.
- `references/setup/setup-workflow.md`: guided setup workflow, draft/verified tracks, and task-scoped intake rules.
- `references/setup/onboarding-flow.yaml`: setup cards and routing from workflow mode to gate.
- `references/setup/task-gates.yaml`: minimum required fields and allowed/blocked outputs by task.
- `references/setup/user-setup.schema.json`: schema for user-facing setup JSON.
- `references/setup/prompt-templates.md`: user-facing setup prompt templates.
- `references/data-lifecycle.md`: bronze/silver/gold/platinum admissions data pipeline.
- `references/quality-checks.md`: executable quality-check intent and failure policy.
- `references/lineage.md`: source-to-output traceability rules.
- `references/governance.md`: privacy, redaction, and public/private data separation.
- `references/refresh-policy.md`: source staleness, source diff, and fact-version policy.
- `references/release-process.md`: versioning and review rules for route/rule bundles.
- `references/ontology/object_types.yaml`: object schemas for applicant, program, case, rules, documents, evidence, tasks, risk, deadlines, offers, and visa cases.
- `references/ontology/link_types.yaml`: required relationships between objects.
- `references/ontology/action_types.yaml`: controlled actions that update object state.
- `references/ontology/rule_bundles.yaml`: versioned country-route rule bundle templates.
- `references/ontology/workflow_gates.yaml`: gates for profile completeness, route resolution, requirement verification, submission, offer, visa, and monitoring.
- `references/ontology/views.yaml`: workbook/dashboard views derived from ontology objects.
- `references/ontology/quality_checks.yaml`: machine-readable quality checks used by the validator.
- `references/ontology/lineage_rules.yaml`: lineage expectations from sources to views and essays.
- `references/ontology/access_policies.yaml`: privacy and redaction policy.
- `references/ontology/view_definitions.yaml`: declarative view definitions with dependencies and freshness.
- `references/workbook-schema.md`: JSON input contract and sheet schema.
- `references/programme-table-cleaning.md`: objective 11-column official programme table export rules.
- `references/essay-sop.md`: statement and essay evidence workflow.
- `references/submission.md`: document and portal checklist workflow.
- `scripts/build_admissions_workbook.py`: dependency-free `.xlsx` builder for structured admissions data.
- `scripts/clean_programme_workbooks.py`: `.xlsx` cleaner for objective 11-column official programme exports.
- `scripts/verify_programme_workbooks.py`: verifier for cleaned programme workbook headers, banned phrases, official URLs, dates, filters, and freeze panes.
- `scripts/validate_ontology.py`: dependency-free ontology validator that emits JSON reports and fails on blocker/error checks.
- `scripts/validate_setup.py`: dependency-free setup validator for workflow mode, output mode, and task-gate missing fields.
- `scripts/doctor_admissions_case.py`: dependency-free diagnostic report for allowed outputs, blocked outputs, blockers, warnings, and next questions.
- `scripts/onboard_admissions.py`: dependency-free setup packet generator for guided onboarding.
