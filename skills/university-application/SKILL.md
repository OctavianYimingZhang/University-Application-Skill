---
name: university-application
description: Router for university application requests covering programme and requirement Research, admissions Writing, application Readiness, student-visa administration, and programme-data maintenance.
---

# University Application Router

Use the package workflow in [`../../SKILL.md`](../../SKILL.md).

Route explicit requests directly:

- Programme discovery, comparisons, requirements, supervisor fit, costs, deadlines, or applicant-facing comparison tables and workbooks → `application-research`
- SOPs, personal statements, supplements, programme-fit paragraphs, drafting, or revision → `application-writing`
- Materials, portal status, tests, references, fees, deadlines, or submission blockers → `application-readiness`
- Student-visa rules, sponsorship evidence, immigration steps, or visa timelines → `application-visa`
- Catalogue, CSV, XLSX, source-table, or programme-workbook maintenance → `application-data`

Ask once only when a missing input would materially change the requested result.
