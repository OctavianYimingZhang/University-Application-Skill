# Setup Prompt Templates

Use these templates when the user wants a guided entry point instead of a full ontology discussion.

## Full Shortlist

```text
Use study-abroad-advisor.
workflow_mode: full_shortlist
output_mode: draft first, verified later
Target degree:
Target intake:
Target countries:
Current education:
Major:
GPA and scale:
Annual budget:
Career or research goal:
Risk preference:
Ask only the first compact batch of necessary questions. Do not recommend schools yet.
```

## Requirement Audit

```text
Use study-abroad-advisor.
workflow_mode: requirement_audit
output_mode: source_backed
Target program:
Official URL:
Target intake:
Citizenship / residence country / education country / passport country:
Use official sources only. Output RequirementRule objects, SourceEvidence, stale_after_days, verification_status, and blocking tasks.
```

## Essay SOP

```text
Use study-abroad-advisor.
workflow_mode: essay_sop
output_mode: draft
Target program:
Essay prompt:
Word limit:
Real student evidence:
Build StudentEvidence, ProgramFitFact, and EssayClaim first. Do not draft the full essay yet.
```

## Workbook Build

```text
Use study-abroad-advisor.
workflow_mode: workbook_build
output_mode: verified
Input: ontology JSON or structured case data
Render an admissions workbook only after validator checks pass. If validation fails, output the blocker report instead.
```

## Submission Readiness

```text
Use study-abroad-advisor.
workflow_mode: submission_readiness
output_mode: verified
Target application cases:
Document status:
Portal status:
Deadlines:
Run readiness gates before marking anything submitted.
```
