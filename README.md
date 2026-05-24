# Study Abroad Advisor Codex Skill

`study-abroad-advisor` is an open-source Codex Skill for running international university applications as a guided, source-backed workflow.

It is built to replace the opaque parts of a study-abroad agency workflow: profile intake, school shortlisting, exact program selection, official requirement mapping, essay/SOP planning, submission readiness, offer tracking, and visa or residence-permit preparation.

The core design rule is simple: recommendations are not treated as casual chat output. Admissions facts become structured objects with official evidence, state, blockers, freshness, and lineage.

## At A Glance

| Area | What the Skill provides |
| --- | --- |
| Guided intake | Setup-style questions that collect only the fields needed for the current task. |
| School selection | Around 10 schools split into reach, target, and safer choices when enough verified context exists. |
| Program selection | Program-level comparison inside each school, including curriculum, route, fees, campus, requirements, and fit. |
| Requirements | A source-backed matrix for transcripts, language scores, references, essays, fees, deadlines, routes, and documents. |
| Essays/SOPs | Evidence collection, academic-interest exploration, reusable core statement planning, and school-specific variants. |
| Submission | Portal/common-system checklist, document state tracking, recommender tasks, deadline checks, and final blockers. |
| Outputs | Chat summaries, tables, ontology JSON, and `.xlsx` workbooks generated from structured case data. |
| Programme table cleaning | Cleans programme-list workbooks into an objective 11-column official-information export. |

## Why This Exists

International admissions work fails when facts are mixed with guesses. A student's citizenship, residence country, education country, passport country, document language, funding source, GPA scale, target intake, and visa route can all change the correct answer.

This Skill keeps those facts separate and forces material claims to be either:

- verified from official or high-quality sources
- labeled as draft or unverified
- blocked until evidence is available

That makes the workflow auditable. It also makes it possible to refresh stale sources, detect unresolved blockers, and explain why a school or program is recommended.

## Boundaries

The Skill does not guarantee admission, invent acceptance probabilities, replace official university instructions, or provide legal immigration advice. For verified outputs, it requires current official sources or marks the item as unresolved.

## Quick Start

Install the Skill into Codex:

```bash
mkdir -p ~/.codex/skills
rsync -a study-abroad-advisor/ ~/.codex/skills/University-Application-Skill/
```

Use it in Codex:

```text
$study-abroad-advisor
Help me plan a master's application cycle. Start with guided setup questions before recommending schools.
```

Run local validation:

```bash
python study-abroad-advisor/scripts/validate_setup.py study-abroad-advisor/tests/fixtures/user_setup_full_shortlist.json
python study-abroad-advisor/scripts/validate_ontology.py study-abroad-advisor/tests/fixtures/ontology_mvp.json
python study-abroad-advisor/scripts/build_admissions_workbook.py study-abroad-advisor/tests/fixtures/ontology_mvp.json /tmp/application_plan.xlsx
```

Clean official programme-list workbooks:

```bash
python study-abroad-advisor/scripts/clean_programme_workbooks.py --source-dir input_workbooks --out-dir cleaned_workbooks
python study-abroad-advisor/scripts/verify_programme_workbooks.py --dir cleaned_workbooks
```

## Workflow Modes

The user-facing entry point is a guided setup layer. The Skill first asks for the current task, reliability level, and minimum required facts. It supports these modes without forcing every request through full intake:

| Mode | Use when |
| --- | --- |
| `quick_triage` | The student is still exploring countries, fields, or feasibility. |
| `full_shortlist` | The student wants a school shortlist and reach/target/safer split. |
| `exact_program_selection` | Schools are known and exact programs need comparison. |
| `requirement_audit` | Official requirements need verification for known programs. |
| `essay_sop` | The student needs SOP/essay evidence, structure, or variants. |
| `workbook_build` | Structured case data should be rendered into an `.xlsx` workbook. |
| `programme_table_cleaning` | Programme-list workbooks need the objective 11-column official-information export. |
| `submission_readiness` | The student needs a pre-submit blocker and checklist review. |
| `source_refresh` | Existing admissions sources need freshness checks or diffs. |
| `visa_route` | Offer or post-offer documents trigger visa/residence route research. |

Output tracks are explicit:

| Track | Meaning |
| --- | --- |
| `brainstorm` / `draft` | Useful for exploration; unverified facts must be labeled. |
| `source_backed` | Uses cited sources but may still have unresolved checks. |
| `verified` | Requires official evidence, lineage, freshness policy, and quality gates before final outputs. |

## Core Workflow

```mermaid
flowchart TD
    A["Setup Mode Selection"] --> B["Output Reliability Selection"]
    B --> C["Task-Scoped Gate"]
    C --> D["Minimum Intake Batch"]
    D --> E["Profile Graph Build"]
    E --> F["Route Resolution"]
    F --> G["Program Discovery"]
    G --> H["Requirement Verification"]
    H --> I["Eligibility & Risk Classification"]
    I --> J["Shortlist Decision"]
    J --> K["Materials Workflow"]
    K --> L["Portal Submission"]
    L --> M["Offer & Deposit"]
    M --> N["Visa / Residence Permit"]
    N --> O["Pre-arrival"]
    O --> P["Monitoring"]
```

Each step is gated. If required information or official evidence is missing, the Skill creates blocking tasks and marks facts as `needs_official_check` instead of guessing.

## Setup Objects

The setup layer keeps user interaction separate from admissions facts:

- `UserSetup`: selected workflow mode, output track, depth, source policy, privacy mode, and export target.
- `PreferenceWeight`: ranking, admission safety, budget, city, career, research fit, visa/work, and deadline-feasibility weights.
- `InteractionState`: completed setup cards, missing fields, blockers, warnings, and next questions.

Admissions facts remain in `Applicant`, `EducationCredential`, `Program`, `ApplicationCase`, `RequirementRule`, `DocumentArtifact`, `SourceEvidence`, `Task`, and `RiskFlag` objects.

## Official Programme Table Cleaning

The repository includes the former `official-programme-table-cleaner` workflow as part of this Skill. It converts programme comparison workbooks into an objective export with exactly 11 columns:

```text
学校
Program
Award
项目类型/学习方式
课程/训练/毕业要求
学术背景/限制条件
申请材料/研究要求
申请时间/状态
费用/资金/特殊事项
官方来源
核对日期
```

This export removes country/region, rankings, direction groups, department fields, subjective feasibility, fit/risk advice, and internal QA fields. It is intended for clean official-information tables, not for preserving the full internal admissions ontology.

## Ontology-First Design

The workbook is not the source of truth. It is a view over ontology objects.

```mermaid
flowchart LR
    Sources["Official Sources"] --> Snapshots["SourceSnapshot"]
    Snapshots --> Facts["ExtractedFact"]
    Facts --> Evidence["SourceEvidence"]
    Evidence --> Objects["Verified Ontology Objects"]
    Objects --> Checks["Quality Checks"]
    Checks --> Actions["Controlled Actions"]
    Actions --> Gates["Workflow Gates"]
    Gates --> Views["Workbook / Dashboard / Checklist Views"]
```

Minimum object set:

- `UserSetup`
- `PreferenceWeight`
- `InteractionState`
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

Data-processing and governance objects are used when sources are researched or final outputs are rendered:

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

## Data Lifecycle

The Skill follows a layered admissions data workflow:

| Layer | Objects | Purpose |
| --- | --- | --- |
| Bronze | `SourceSnapshot` | Preserve raw official source snapshots, retrieval time, URL, status, and hash. |
| Silver | `ExtractedFact` | Store candidate facts extracted from snapshots without treating them as verified. |
| Gold | `RequirementRule`, `Deadline`, `ProgramFitFact`, `RiskFlag`, `Task` | Use only source-backed facts for decisions, risk, checklists, and essay planning. |
| Platinum | Workbook views, shortlist, essay plan, submission checklist | Render user-facing outputs from verified ontology objects. |

Final recommendations must not come directly from raw web pages or extracted candidate facts. They must pass through quality checks and preserve lineage.

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

## Quality And Lineage

The repository includes a dependency-free validator:

```bash
python study-abroad-advisor/scripts/validate_ontology.py study-abroad-advisor/tests/fixtures/ontology_mvp.json
```

Setup can be generated and checked before exposing the full ontology:

```bash
python study-abroad-advisor/scripts/onboard_admissions.py --mode full_shortlist --output-mode draft
python study-abroad-advisor/scripts/validate_setup.py study-abroad-advisor/tests/fixtures/user_setup_full_shortlist.json
python study-abroad-advisor/scripts/doctor_admissions_case.py study-abroad-advisor/tests/fixtures/ontology_mvp.json
```

Core checks include:

- no verified requirement without source evidence
- no deadline with due time but missing timezone
- no submitted case with open blockers
- no verified program-fit fact without source evidence
- no approved essay claim without student evidence and program-fit evidence
- stale source warnings
- valid setup mode and output mode
- task-gate required fields before gated output

Every final output should be traceable through `LineageEdge`, for example:

```text
SourceSnapshot -> ExtractedFact -> RequirementRule -> ApplicationCase -> WorkbookCell
StudentEvidence + ProgramFitFact -> EssayClaim -> SOPParagraph
```

## Main Skill Resources

- [`SKILL.md`](study-abroad-advisor/SKILL.md): entrypoint and operating rules.
- [`references/intake.md`](study-abroad-advisor/references/intake.md): adaptive intake and brainstorming workflow.
- [`references/research.md`](study-abroad-advisor/references/research.md): source hierarchy and research rules.
- [`references/ontology.md`](study-abroad-advisor/references/ontology.md): ontology operating model.
- [`references/setup/setup-workflow.md`](study-abroad-advisor/references/setup/setup-workflow.md): setup modes, output tracks, and task-scoped gates.
- [`references/setup/onboarding-flow.yaml`](study-abroad-advisor/references/setup/onboarding-flow.yaml): setup cards and workflow routing.
- [`references/setup/task-gates.yaml`](study-abroad-advisor/references/setup/task-gates.yaml): required fields by task.
- [`references/setup/user-setup.schema.json`](study-abroad-advisor/references/setup/user-setup.schema.json): user setup JSON schema.
- [`references/setup/prompt-templates.md`](study-abroad-advisor/references/setup/prompt-templates.md): guided prompt templates.
- [`references/data-lifecycle.md`](study-abroad-advisor/references/data-lifecycle.md): Bronze/Silver/Gold/Platinum pipeline.
- [`references/quality-checks.md`](study-abroad-advisor/references/quality-checks.md): quality gates and failure policy.
- [`references/lineage.md`](study-abroad-advisor/references/lineage.md): source-to-output traceability.
- [`references/governance.md`](study-abroad-advisor/references/governance.md): privacy and public/private data separation.
- [`references/refresh-policy.md`](study-abroad-advisor/references/refresh-policy.md): source staleness and fact-diff policy.
- [`references/release-process.md`](study-abroad-advisor/references/release-process.md): controlled release process for rule bundles.
- [`references/ontology/object_types.yaml`](study-abroad-advisor/references/ontology/object_types.yaml): object schemas.
- [`references/ontology/action_types.yaml`](study-abroad-advisor/references/ontology/action_types.yaml): controlled actions.
- [`references/ontology/workflow_gates.yaml`](study-abroad-advisor/references/ontology/workflow_gates.yaml): state transition gates.
- [`references/ontology/rule_bundles.yaml`](study-abroad-advisor/references/ontology/rule_bundles.yaml): country-route rule bundle templates.
- [`references/ontology/quality_checks.yaml`](study-abroad-advisor/references/ontology/quality_checks.yaml): machine-readable validation checks.
- [`references/ontology/lineage_rules.yaml`](study-abroad-advisor/references/ontology/lineage_rules.yaml): required lineage paths.
- [`references/ontology/access_policies.yaml`](study-abroad-advisor/references/ontology/access_policies.yaml): data access and redaction policy.
- [`references/ontology/view_definitions.yaml`](study-abroad-advisor/references/ontology/view_definitions.yaml): declarative view dependencies and freshness rules.
- [`references/workbook-schema.md`](study-abroad-advisor/references/workbook-schema.md): JSON contract for workbook views.
- [`references/programme-table-cleaning.md`](study-abroad-advisor/references/programme-table-cleaning.md): 11-column official programme table cleaning rules.
- [`scripts/build_admissions_workbook.py`](study-abroad-advisor/scripts/build_admissions_workbook.py): dependency-free XLSX builder.
- [`scripts/clean_programme_workbooks.py`](study-abroad-advisor/scripts/clean_programme_workbooks.py): programme workbook cleaner.
- [`scripts/verify_programme_workbooks.py`](study-abroad-advisor/scripts/verify_programme_workbooks.py): cleaned programme workbook verifier.
- [`scripts/validate_ontology.py`](study-abroad-advisor/scripts/validate_ontology.py): dependency-free ontology validator.
- [`scripts/validate_setup.py`](study-abroad-advisor/scripts/validate_setup.py): dependency-free setup and task-gate validator.
- [`scripts/doctor_admissions_case.py`](study-abroad-advisor/scripts/doctor_admissions_case.py): blocker, warning, allowed-output, and next-question diagnostic.
- [`scripts/onboard_admissions.py`](study-abroad-advisor/scripts/onboard_admissions.py): setup packet generator for guided onboarding.

## Workbook Builder

The builder accepts ontology-first JSON and legacy array-based JSON.

```bash
python study-abroad-advisor/scripts/build_admissions_workbook.py input.json output.xlsx
```

When ontology data is present, the builder validates quality gates before rendering. `--skip-validation` exists only for draft output and must not be used for verified recommendations.

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
- source snapshots
- extracted facts
- fact versions
- lineage edges
- quality checks
- pipeline runs
- action events
- user setup
- preference weights
- interaction state
- student evidence
- program fit facts
- essay claims

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
