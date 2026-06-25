---
name: programme-table-cleaning
description: Clean and verify official university programme tables or workbooks for University Application Skill. Use when the user supplies programme workbook files, scraped tables, CSV/XLSX exports, or source tables that need normalization, lineage, and quality checks.
---

# Programme Table Cleaning

Use this focused Skill for programme table/workbook cleaning.

## Workflow

1. Read `references/programme-table-cleaning.md`.
2. Use `scripts/clean_programme_workbooks.py` to normalize official programme tables when files are supplied.
3. Use `scripts/verify_programme_workbooks.py` to check cleaned outputs.
4. Preserve source lineage, URLs, source dates, and raw values.
5. Mark fields that cannot be verified as missing evidence.

## Output

Produce cleaned workbooks/tables plus verification notes. Do not rewrite official requirements from memory.
