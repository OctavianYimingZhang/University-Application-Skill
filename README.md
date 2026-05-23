# University Application Skill

Open-source Codex Skill for managing international university applications as a source-backed admissions operating ontology.

## What This Skill Does

`study-abroad-advisor` is designed to replace a study-abroad agency workflow with a verifiable AI workflow. It helps a student move from early brainstorming to school selection, exact program selection, requirements tracking, essay planning, submission preparation, offer handling, and visa or residence-permit readiness.

The Skill does not treat admissions advice as a one-time answer. It treats each application as an evolving object graph with evidence, state, blockers, and controlled transitions.

## Core Workflow

```mermaid
flowchart TD
    A["Profile Graph Build"] --> B["Route Resolution"]
    B --> C["Program Discovery"]
    C --> D["Requirement Verification"]
    D --> E["Eligibility & Risk Classification"]
    E --> F["Shortlist Decision"]
    F --> G["Materials Workflow"]
    G --> H["Portal Submission"]
    H --> I["Offer & Deposit"]
    I --> J["Visa / Residence Permit"]
    J --> K["Pre-arrival"]
    K --> L["Monitoring"]
```

Each step is gated. If required information or official evidence is missing, the Skill creates blocking tasks and marks facts as `needs_official_check` instead of guessing.

## Ontology-First Design

The workbook is not the source of truth. It is a view over ontology objects.

```mermaid
flowchart LR
    Sources["Official Sources"] --> Evidence["SourceEvidence"]
    Evidence --> Objects["Ontology Objects"]
    Objects --> Actions["Controlled Actions"]
    Actions --> Gates["Workflow Gates"]
    Gates --> Views["Workbook / Dashboard / Checklist Views"]
```

Minimum object set:

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

Additional objects such as `Deadline`, `OfferDecision`, and `VisaImmigrationCase` are used when the case reaches deadlines, offers, deposits, post-offer documents, visa, residence permit, or pre-arrival planning.

## Why Ontology Matters

International applications are not one linear checklist. A student's citizenship, residence country, education country, passport country, visa application country, document language, funding source country, and prior residence history can trigger different rules.

The Skill keeps these fields separate so it can reason about cases such as:

- a Chinese citizen studying in the UK applying to a UK master's program
- an Indian citizen living in the UAE applying to Canadian undergraduate programs
- a US citizen applying to a Netherlands exchange or master's route
- an EU/EEA citizen applying to Sweden
- a student applying through UCAS, Common App, uni-assist, Studielink, Universityadmissions.se, or a direct university portal

## Workflow Gates

The Skill uses gates to prevent premature outputs.

| Gate | Blocks Until |
| --- | --- |
| `ProfileCompletenessGate` | Degree level, intake, target countries, citizenship, residence, education country, passport country, GPA/scale, budget, language status, and document availability are known enough to research. |
| `RouteResolutionGate` | The application route is verified from an official institution, application-system, or government source. |
| `RequirementVerificationGate` | Each requirement has source evidence, checked date, source type, and verification status. |
| `SubmissionReadinessGate` | Program, campus, intake, deadline timezone, documents, recommender status, payment readiness, and source log are complete. |
| `OfferAndDepositGate` | Offer evidence, conditions, deposit timing, and post-offer document dependencies are recorded. |
| `VisaWorkflowGate` | Destination, citizenship, residence, passport, post-offer document route, and government-source evidence are verified. |

## Evidence Rules

Every material fact must link to `SourceEvidence`:

- deadlines
- tuition, deposits, application fees, and funding requirements
- language requirements and waivers
- GPA, class, credential, or grading equivalencies
- document requirements
- application routes
- visa or residence-permit rules
- work rights or post-study routes
- ranking claims
- program curriculum claims used for fit or essays

If official evidence is missing, the Skill marks the fact as `needs_official_check`.

## Main Skill Resources

- [`SKILL.md`](study-abroad-advisor/SKILL.md): entrypoint and operating rules.
- [`references/intake.md`](study-abroad-advisor/references/intake.md): adaptive intake and brainstorming workflow.
- [`references/research.md`](study-abroad-advisor/references/research.md): source hierarchy and research rules.
- [`references/ontology.md`](study-abroad-advisor/references/ontology.md): ontology operating model.
- [`references/ontology/object_types.yaml`](study-abroad-advisor/references/ontology/object_types.yaml): object schemas.
- [`references/ontology/action_types.yaml`](study-abroad-advisor/references/ontology/action_types.yaml): controlled actions.
- [`references/ontology/workflow_gates.yaml`](study-abroad-advisor/references/ontology/workflow_gates.yaml): state transition gates.
- [`references/ontology/rule_bundles.yaml`](study-abroad-advisor/references/ontology/rule_bundles.yaml): country-route rule bundle templates.
- [`references/workbook-schema.md`](study-abroad-advisor/references/workbook-schema.md): JSON contract for workbook views.
- [`scripts/build_admissions_workbook.py`](study-abroad-advisor/scripts/build_admissions_workbook.py): dependency-free XLSX builder.

## Workbook Builder

The builder accepts ontology-first JSON and legacy array-based JSON.

```bash
python study-abroad-advisor/scripts/build_admissions_workbook.py input.json output.xlsx
```

When ontology data is present, the workbook renders object-state views such as:

- applicant objects
- education credentials
- institutions
- programs
- application cases
- requirement rules
- document artifacts
- tasks
- risk flags
- deadlines
- offer decisions
- visa cases
- source evidence

Legacy views such as school shortlist, program comparison, requirements matrix, essay plan, submission checklist, source log, and regional program sheets remain supported.

## Example Workflow Output

Instead of only saying:

```text
You can apply to A, B, and C. Materials include transcript, CV, SOP, and references.
```

The Skill should produce object state:

```text
ApplicationCase.case_001
status: requirements_verified
route: university_portal
blocking_tasks:
- task_004: verify_ATAS_requirement
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

This makes the workflow auditable and prevents unsupported admissions claims.

## License

MIT License. See [`LICENSE`](LICENSE).
