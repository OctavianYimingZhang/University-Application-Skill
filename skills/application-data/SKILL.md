---
name: application-data
description: Maintain university programme catalogues, source tables, CSV or XLSX files, and admissions workbooks with provenance and validation. Use when the user explicitly asks to clean, normalise, merge, verify, rebuild, or quality-check programme data rather than research an applicant shortlist.
---

# Application Programme Data

Read `references/evidence-contract.md`, `references/research.md`, and `catalogues/README.md`.

## Workflow

1. Identify the supplied data files, intended schema, institutions, application cycle, and output destination.
2. Preserve raw values, source URLs, access dates, programme identity, requirements status, and transformation lineage as separate fields.
3. Use `scripts/clean_programme_workbooks.py` and `scripts/verify_programme_workbooks.py` for supplied workbook maintenance.
4. Use the relevant official-source catalogue builder and `scripts/validate_catalogues.py` for Plugin-owned catalogue maintenance.
5. Mark missing, stale, conflicting, or unverified values explicitly and verify the finished workbook, table, or catalogue.

Treat catalogue rows as programme identities. Add current requirements only after independent official-page verification.

Use the user's requested output language; otherwise use English.
