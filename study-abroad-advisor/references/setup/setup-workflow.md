# Setup Workflow

Use this reference when the user needs a guided entry point, asks how to start, or gives a task that does not require full intake.

## Operating Rule

Separate the user's current task from the applicant facts.

- `UserSetup` stores what the user wants to do now.
- `PreferenceWeight` stores ranking, safety, budget, city, career, research, visa/work, and deadline weights.
- `InteractionState` stores setup progress, missing fields, blocker count, warnings, and the next recommended action.
- `Applicant`, `EducationCredential`, `Program`, and `ApplicationCase` remain the source of admissions facts.

## Output Tracks

Use two explicit output tracks:

- Draft track: allowed for brainstorming, scoping, missing-field reports, first-pass country comparison, and research plans. Label unverified facts. Do not call the output final.
- Verified track: requires source evidence, lineage, freshness policy, and quality checks before final recommendations, verified workbooks, final checklists, submission state transitions, or visa-ready status.

## Task-Scoped Intake

Do not force every task through full intake.

- Use `QuickTriageGate` for early exploration.
- Use `FullShortlistGate` only when the user wants a school shortlist or final recommendation.
- Use `RequirementAuditGate` when the user only wants official requirements for known programs.
- Use `EssaySOPGate` when the user wants statement planning or drafting.
- Use `WorkbookBuildGate` when structured case data already exists.
- Use `SubmissionReadinessGate` only for pre-submit review.
- Use `SourceRefreshGate` when old sources need refresh or diff.
- Use `VisaRouteGate` only when offer/post-offer document or government-route logic is relevant.

## Setup Cards

Ask in setup cards rather than exposing ontology internals:

1. Current workflow mode.
2. Output reliability.
3. Target degree, intake, countries, and field.
4. Citizenship, residence country, passport country, and education country.
5. Academic background, GPA scale, language status, and evidence documents.
6. Preference weights and budget.
7. Privacy/export mode.
8. Doctor status: allowed outputs, blocked outputs, blockers, warnings, and next questions.

Use compact batches by default. Ask only the minimum questions needed for the selected task gate.

## Diagnostics

Run `scripts/validate_setup.py` when a setup JSON is available. Run `scripts/doctor_admissions_case.py` when ontology JSON is available and the user needs to know what can be done next.
