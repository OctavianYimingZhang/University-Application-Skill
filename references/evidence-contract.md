# Applicant Evidence Contract

Applicant evidence is blank by default. A profile value, uploaded file, link, extracted passage, or model suggestion is not confirmed evidence until it satisfies this record contract.

## Record shape

Each record uses these independent fields:

| Field | Required value |
| --- | --- |
| `evidence_id` | Stable non-placeholder identifier. |
| `value` | Non-empty applicant fact; a URL by itself is not a value. |
| `source` | Object containing non-placeholder `url`, `title`, and `publisher`. |
| `evidence_date` | ISO date or date-time for the underlying evidence. |
| `confirmation_status` | `unconfirmed` or `explicitly_confirmed`. |
| `confirmed_at` | ISO date-time when explicitly confirmed; otherwise empty or null. |
| `source_availability` | `available`, `unavailable`, or `unknown`. |
| `fact_verification` | `unverified`, `verified`, or `conflicted`. |
| `completeness` | `placeholder`, `partial`, or `complete`. |
| `application_cycle` | The cycle to which the evidence applies. |
| `accessed_at` | ISO date or date-time when the source was accessed. |
| `staleness` | `fresh`, `stale`, or `unknown`. |

Keep these dimensions separate. Source availability describes whether the source can be accessed, fact verification describes whether the value was checked, completeness describes whether the record contains the required substance, the application cycle scopes the fact, the access date records retrieval time, and staleness records currency.

## Passing invariant

An evidence record passes only when all of the following are true:

- `value` is substantive and is not empty, a placeholder, or a link by itself;
- `source.url` is a real non-placeholder URL;
- `evidence_date` is present;
- `confirmation_status` is `explicitly_confirmed` and `confirmed_at` is present;
- `fact_verification` is `verified`;
- `completeness` is `complete`;
- every normalized field above is present and valid.

`source_availability`, `application_cycle`, `accessed_at`, and `staleness` remain visible even when the confirmation predicate passes. A stale or unavailable source can still block a current-cycle recommendation under the quality rules.

Run [`../scripts/validate_evidence.py`](../scripts/validate_evidence.py) before treating applicant evidence as confirmed. In `AcademicTaskContext`, keep proposed decisions at `suggested`; only a user selection may set a decision to `explicitly_confirmed`.
