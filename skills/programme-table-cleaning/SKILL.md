---
name: programme-table-cleaning
description: Explicit maintenance workflow for cleaning and verifying official university programme catalogues, tables, or workbooks. Use only when the user asks to maintain supplied programme workbook files, scraped tables, CSV/XLSX exports, or source tables that need normalization, lineage, and quality checks; do not route ordinary applicant planning here.
---

# Programme Table Cleaning

Use this focused Skill only for explicitly requested programme-data maintenance. It is not an applicant-planning or shortlist route.

## Workflow

1. Confirm the user explicitly requested catalogue, table, or workbook maintenance and identify the supplied source files and output destination.
2. Read [`../../references/programme-table-cleaning.md`](../../references/programme-table-cleaning.md).
3. Use [`../../scripts/clean_programme_workbooks.py`](../../scripts/clean_programme_workbooks.py) to normalize official programme tables when files are supplied.
4. Use [`../../scripts/verify_programme_workbooks.py`](../../scripts/verify_programme_workbooks.py) to check cleaned outputs.
5. For curated identity-catalogue maintenance, write Plugin-owned JSON under [`../../catalogues/`](../../catalogues/README.md) through the relevant official-source builder and run [`../../scripts/validate_catalogues.py`](../../scripts/validate_catalogues.py). Do not write catalogue data into a website source tree.
6. Preserve source lineage, URLs, application cycles, access dates, source availability, fact verification, completeness, staleness, and raw values as separate fields.
7. Keep catalogue identity status separate from requirements: an official listing row remains `official_source_listed` with `requirements_status: not_collected` until requirements are independently retrieved and verified.
8. Mark fields that cannot be verified as missing evidence.

## Output

Produce cleaned workbooks/tables or validated identity-catalogue JSON plus verification notes. Do not rewrite official requirements from memory.

Default to English. Use another output language only when the user explicitly requests it.
