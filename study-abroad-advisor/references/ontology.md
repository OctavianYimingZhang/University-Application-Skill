# Admissions Operating Ontology

Use this reference when the task involves multi-country applications, changing admissions facts, document tracking, route selection, visa/residence steps, or any case where a plain checklist would lose state.

## Operating Model

Treat the application cycle as an object graph:

```text
Raw official sources
-> SourceSnapshot
-> ExtractedFact
-> SourceEvidence
-> Applicant, EducationCredential, Institution, Program, ApplicationCase
-> RequirementRule, ProgramFitFact, StudentEvidence, EssayClaim, DocumentArtifact, Task, RiskFlag, Deadline, OfferDecision, VisaImmigrationCase
-> FactVersion, LineageEdge, QualityCheck, PipelineRun, ActionEvent
-> controlled actions, quality checks, and workflow gates
-> workbook, dashboard, checklist, essay plan, and source-log views
```

The ontology is the source of truth. A workbook is only a rendered view.

## Minimum Object Set

For an MVP, create at least:

- `Applicant`
- `EducationCredential`
- `Institution`
- `Program`
- `ApplicationCase`
- `RequirementRule`
- `DocumentArtifact`
- `SourceEvidence`
- `Task`
- `RiskFlag`

Add `Deadline`, `OfferDecision`, and `VisaImmigrationCase` when deadlines, offers, deposits, CAS/I-20/CoE/LOA/PAL/TAL/CAQ/VPD, visa, or residence-permit steps become relevant.

Add data-processing objects when official sources are researched or outputs are rendered:

- `SourceSnapshot`
- `ExtractedFact`
- `FactVersion`
- `LineageEdge`
- `QualityCheck`
- `PipelineRun`
- `ActionEvent`
- `StudentEvidence`
- `ProgramFitFact`
- `EssayClaim`

## Required Separation

Do not collapse these fields:

- citizenship country or countries
- residence country
- education country
- passport country
- visa application country
- document language
- funding source country
- prior residence history

Different countries use these fields for different rules. A Chinese citizen studying in the UK, an Indian citizen studying in the UAE, and a US citizen applying to the Netherlands can trigger different language-waiver, document, visa, fee, and residence-permit paths even if their target degree looks similar.

## State-Machine Workflow

Use this progression:

```text
Profile Graph Build
-> Route Resolution
-> Program Discovery
-> Requirement Verification
-> Eligibility & Risk Classification
-> Shortlist Decision
-> Materials Workflow
-> Portal Submission
-> Offer & Deposit
-> Visa / Residence Permit
-> Pre-arrival
-> Monitoring
```

Each step has a gate in `ontology/workflow_gates.yaml`. If the gate fails, create blocking `Task` and `RiskFlag` objects instead of advancing state.

## Evidence Discipline

Every material fact must link to `SourceEvidence`:

- deadline
- tuition, deposit, fee, or funding requirement
- language score or waiver
- GPA/class/credential equivalency
- document requirement
- application route
- portal/common-application rule
- visa or residence rule
- work right or post-study route
- ranking claim
- program curriculum claim used for fit or essays

If evidence is missing, set `verification_status: needs_official_check`.

## Data Lifecycle

Use four layers:

- Bronze: raw official page, portal, visa, ranking, or test-provider snapshots as `SourceSnapshot`.
- Silver: candidate facts extracted from snapshots as `ExtractedFact`.
- Gold: verified facts used for decisions as `RequirementRule`, `Deadline`, `ProgramFitFact`, `RiskFlag`, and `Task`.
- Platinum: user-facing views such as workbook, shortlist, essay plan, and checklist.

No final recommendation may be produced from Bronze or Silver objects directly.

## Quality Checks

Before rendering a verified workbook or final recommendation, run checks equivalent to `ontology/quality_checks.yaml`. Blocker failures must prevent verified output and create a task or risk.

Core checks:

- No verified requirement without source evidence.
- No deadline with due time but missing timezone.
- No submitted case with open mandatory blockers.
- No verified program-fit fact without source evidence.
- No approved essay claim without student evidence and program-fit evidence.
- No stale source silently treated as verified.

## Lineage

Every final output should be traceable:

```text
SourceSnapshot -> ExtractedFact -> RequirementRule -> ApplicationCase -> RiskFlag / Task / Deadline -> WorkbookCell
SourceEvidence(program module page) -> ProgramFitFact -> EssayClaim -> SOPParagraph
```

If lineage cannot be established, label the output as `needs_official_check` or `unsupported`.

## Output Pattern

Prefer object-state output over generic advice:

```text
ApplicationCase.case_001
status: requirements_verified
blocking_tasks:
- task_004: verify_atas_requirement
- task_007: request_official_transcript
verified_requirements:
- req_001: transcript
- req_002: SOP
unverified_requirements:
- req_009: language waiver
risk_flags:
- risk_002: deadline timezone not confirmed
- risk_004: visa document dependency unresolved
```

This prevents unsupported recommendations because every requirement, task, and risk must have identity, status, and evidence.

## Reference Files

- `ontology/object_types.yaml`: semantic object schemas.
- `ontology/link_types.yaml`: required relationships.
- `ontology/action_types.yaml`: controlled updates.
- `ontology/rule_bundles.yaml`: country-route rule bundle templates.
- `ontology/workflow_gates.yaml`: state transition gates.
- `ontology/views.yaml`: workbook and dashboard views.
- `ontology/quality_checks.yaml`: check definitions for validator and output gates.
- `ontology/lineage_rules.yaml`: required traceability paths.
- `ontology/access_policies.yaml`: privacy, redaction, and public/private sharing rules.
- `ontology/view_definitions.yaml`: declarative materialized-view definitions.
- `ontology/ontology.schema.json`: JSON shape for structured ontology data.
