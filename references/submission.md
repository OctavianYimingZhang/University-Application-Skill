# Submission Workflow

Use this workflow after target programs are chosen.

Submission is a state transition on `ApplicationCase`, not just a checklist. Do not mark a case submitted unless the submission readiness gate in `references/ontology/workflow_gates.yaml` passes.

## Per-Program Checklist

For each program, verify and record:

- Application system or portal.
- Account/email used.
- Deadline and time zone.
- Application fee and accepted payment method.
- Transcript requirements, including official, unofficial, translated, notarized, sealed, uploaded, mailed, or credential-evaluated versions.
- Degree certificate or enrollment certificate requirements.
- GPA conversion, class rank, grading scale, or credential evaluation evidence.
- Language requirement, accepted tests, minimum total and component scores, waiver rules, and score-reporting method.
- References: count, academic/professional type, form or letter, submission method, deadline, and recommender email.
- CV/resume requirements.
- SOP, personal statement, research proposal, writing sample, portfolio, sample work, or scholarship essay.
- Standardized tests and score reporting.
- Passport, identity, residency, fee status, or visa-related documents.
- Scholarship, funding, assistantship, lab contact, supervisor approval, or interview steps.
- Route-specific post-offer dependency, such as I-20, CAS, CoE, LOA, PAL/TAL, CAQ, VPD, residence-permit sponsorship, or another official document where applicable.
- Source evidence ID for every material requirement.

## File Naming

Use consistent file names:

`YYYYMMDD_School_Program_DocumentType_StudentName_v01.pdf`

Examples:

- `20260523_Manchester_BScBiology_Transcript_AlexChen_v01.pdf`
- `20260523_UCL_MScBioinformatics_SOP_AlexChen_v03.pdf`

Use version numbers for essays and final PDFs. Keep editable drafts separate from submitted PDFs.

## Portal Guidance

When guiding a student through a portal:

- Use official instructions and screenshots only if available from the institution or application system.
- Explain field-by-field choices when the form asks for degree, fee status, residency, education history, grade scale, recommender type, or program route.
- Do not submit anything without explicit student instruction.
- Before final submission, compare portal entries against the requirements matrix.

## Final Pre-Submit Check

Confirm:

- Program name, campus, award, intake, and study mode are correct.
- Every upload opens and is the intended final version.
- Names, dates, passport details, grades, and scores match documents.
- Essays answer the exact prompt and respect word or character limits.
- Recommenders have submitted or received the correct links.
- Payment and deadline are handled.
- Source log contains official evidence for all requirements.

If any requirement is unclear, mark it "Needs official check" and do not infer.

## Object Updates

Update ontology objects during submission work:

- `RequirementRule`: set `verification_status` only when official source evidence exists.
- `DocumentArtifact`: move through `missing`, `requested`, `received`, `verified`, `uploaded`, `submitted`, or `expired`.
- `Task`: set owner, due time, timezone, blockers, and status.
- `ApplicationCase`: advance only through gate-approved states.
- `RiskFlag`: create or update blocker risks when deadline, document, source, visa, funding, or identity evidence is incomplete.
- `VisaImmigrationCase`: create only after the offer or post-offer document path is known enough to identify the official route.
