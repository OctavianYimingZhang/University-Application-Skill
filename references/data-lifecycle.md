# Data Lifecycle

1. Classify the request as `matched`, `needs_confirmation`, or `out_of_scope`; collect only the matched route's missing inputs.
2. Collect official sources.
3. Extract structured requirements with source provenance, application cycle, access date, and independent availability, verification, completeness, and staleness fields.
4. Collect applicant values as unconfirmed evidence records with `public_url`, `local_document`, or `user_confirmation` provenance; never seed them from examples or programme data.
5. Maintain one backward-compatible `ApplicationCase v1` per programme with optional requirement, document, deadline, supervisor/fit, writing, risk, action, source-log, lifecycle, and workstream state.
6. Build programme comparison, task, deadline, document, and multi-programme adaptation views only after the relevant evidence gate.
7. Mark missing, partial, unverified, conflicted, wrong-cycle, or stale evidence as a blocker. For writing, also block unresolved or unlocated revision decisions.
8. Refresh requirements before final submission, payment, or visa-readiness decisions.
