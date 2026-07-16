# Programme and Requirement Research

## Scope

Use this workflow for programme discovery, shortlists, named-programme checks, supervisor and programme fit, catalogue maintenance, programme tables, and admissions workbooks.

Start with the scope already stated by the user. Ask only for a missing field that changes the search, such as degree level, exact research-degree type, subject, geography, intake, or whether eligibility, cost, or supervisor fit must be compared.

## Source order

1. Current official programme page.
2. Official department, admissions, fee, scholarship, English-language, and application pages.
3. Official supervisor profiles and representative publications when supervisor fit is requested.
4. Official government or regulator pages for jurisdiction-specific administration.
5. The curated catalogue as an identity index, followed by current-page verification.

## Research workflow

1. Confirm the exact programme identity, award, degree level, mode, location, and application cycle.
2. For research degrees, verify the published award and thesis or research structure. Keep `MPhil`, `MRes`, `MSc by Research`, taught master's degrees, and doctoral routes distinct.
3. Extract the fields needed for the user's result: duration, structure, modules, research groups, supervisor-contact status, academic and subject requirements, English scores, documents, writing prompts and limits, references, fees, scholarships, deadlines, and pre-application steps.
4. Classify each published requirement as required, recommended, optional, not required, or unknown.
5. Compare programmes by the requested factors. Keep requirement evidence separate from strategic fit.
6. Compare supervisor or programme fit against confirmed applicant interests and experience. Treat a relevant topic or supervisor as fit evidence and verify place availability separately.
7. Mark unpublished, inaccessible, stale, or conflicting fields plainly.

## Tables, catalogues, and workbooks

Use `scripts/clean_programme_workbooks.py` and `scripts/verify_programme_workbooks.py` for supplied programme tables. Use the institution-specific catalogue builder when an official source structure requires it, then run `scripts/validate_catalogues.py`.

Preserve programme names, official URLs, raw source values, application cycle, access date, and verification status. Use `scripts/build_admissions_workbook.py` when the user asks for a structured workbook.

## Output

Return the requested shortlist, comparison table, direct requirement explanation, source log, cleaned table, or workbook. Include only factors relevant to the user's decision and keep unknowns visible.
