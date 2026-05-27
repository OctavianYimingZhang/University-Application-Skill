# Quality Checks

Quality checks turn ontology rules from prose into executable constraints.

## Required Behavior

- Run `scripts/validate_ontology.py` before producing a verified workbook, final shortlist, final submission checklist, or visa-ready status from structured ontology JSON.
- Treat `blocker` and `error` findings as failed output gates.
- Create or report `Task` and `RiskFlag` objects for failed checks.
- Do not downgrade unsupported facts into softer prose. Mark them `needs_official_check`, `unsupported`, `stale`, or `conflict`.

## Core Checks

- `no_verified_requirement_without_source`
- `no_deadline_without_timezone`
- `no_submitted_case_with_open_blockers`
- `no_verified_program_fit_without_source`
- `no_approved_essay_claim_without_evidence`
- `source_staleness_check`
- `no_verified_output_from_raw_source`
- `route_rules_are_conditional`

The machine-readable definitions live in `ontology/quality_checks.yaml`.

## Output Policy

When checks fail:

- `info`: include in report only.
- `warning`: continue, but show the warning and stale state.
- `error`: block verified output until fixed.
- `blocker`: block state transition and final output.
