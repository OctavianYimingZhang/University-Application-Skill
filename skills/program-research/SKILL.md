---
name: program-research
description: Source-backed programme discovery and shortlist research for University Application Skill. Use when the user needs official university programme pages collected, compared, cleaned into tables, or narrowed into a programme list without admission-probability prediction.
---

# Program Research

Use this focused Skill for official-source programme discovery and shortlist building.

## Workflow

1. Read [`../../references/intake.md`](../../references/intake.md) and [`../../references/research.md`](../../references/research.md).
2. Confirm target degree level, country/region, subject area, intake, budget, and source policy when missing fields change the research scope.
3. Lazy-load [`../../catalogues/index.json`](../../catalogues/index.json) by institution and degree level when curated coverage applies. Treat these rows only as official-source-listed programme identities with `requirements_status: not_collected`.
4. Retrieve the selected official programme pages and related admissions, fee, scholarship, and visa pages before presenting current requirements or availability as verified facts.
5. Extract programme name, award, level, duration, mode, location, codes, hard requirements, English requirements, fees, deadlines, and documents. Record source availability, fact verification, completeness, application cycle, access date, and staleness separately.
6. Mark missing or unpublished fields as gaps.
7. Compare eligibility, cost, timing, and fit without probability scores.
8. Route named programmes to `requirement-audit` when the user needs a hard-requirement check.

## Output

Produce a table, shortlist, workbook case JSON, or source-backed programme list with a source log.

Default to English. Use another output language only when the user explicitly requests it.
