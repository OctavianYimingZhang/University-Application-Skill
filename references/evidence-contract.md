# Applicant Evidence Contract

Applicant evidence is blank by default. A profile value, uploaded file, link, extracted passage, or model suggestion is not confirmed evidence until it satisfies this record contract.

## Record shape

Each record uses these independent fields:

| Field | Required value |
| --- | --- |
| `evidence_id` | Stable non-placeholder identifier. |
| `value` | Non-empty applicant fact; a URL by itself is not a value. |
| `fact_class` | Optional explicit class: `mutable_official_fact` or `applicant_personal_fact`; legacy records remain accepted, but plainly official deadline, fee, requirement, policy, cycle, or supervisor-contact claims remain official when the field is omitted. |
| `evidence_use` | Optional purpose override: `writing`, `applicant_comparison`, `official_requirement`, `material_document`, or `submission`. |
| `source` | Provenance object. Existing records default to `public_url`; new records use `type: public_url`, `local_document`, or `user_confirmation`. |
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

### Source types

- `public_url` requires a real URL, title, and publisher. It is the only source type that can verify mutable official programme, fee, deadline, policy, or eligibility facts.
- `local_document` requires an opaque local reference and title. It may support an applicant fact or document-presence check without publishing the private file.
- `user_confirmation` requires the current user's explicit confirmation and a title identifying the confirmation context. It may support the applicant's own writing narrative, but cannot satisfy an official requirement, document-completion, or submission gate by itself.

## Passing invariant

An evidence record passes only when all of the following are true:

- `value` is substantive and is not empty, a placeholder, or a link by itself;
- the source fields required by its provenance type are complete;
- `evidence_date` is present;
- `confirmation_status` is `explicitly_confirmed` and `confirmed_at` is present;
- `fact_verification` is `verified`;
- `completeness` is `complete`;
- every normalized field above is present and valid.

The fact class and use-case gate are separate from record validity. Plainly mutable official semantics take precedence over a conflicting `fact_class` or `evidence_use`, and a caller-supplied validation purpose cannot be downgraded by the record:

- an `applicant_personal_fact` used for `writing` or `applicant_comparison` accepts complete `public_url`, `local_document`, or `user_confirmation` provenance;
- a `material_document` item accepts only an `applicant_personal_fact` backed by a currently available `local_document`; an official page saying that a CV is required does not prove that the applicant has a CV;
- a `submission` item preserves its broader source-aware gate: current official records may use fresh, cycle-matched `public_url` provenance and applicant documents may use currently available `public_url` or `local_document` provenance, while user confirmation alone remains insufficient;
- a `mutable_official_fact` or `official_requirement` accepts only an available, fresh public URL whose application cycle equals the current target cycle;
- stale, unavailable, or wrong-cycle official records never pass `official_requirement`, even when their underlying record is otherwise complete.

`source_availability`, `application_cycle`, `accessed_at`, and `staleness` remain visible even when the confirmation predicate passes. A stale or unavailable source can still block a current-cycle recommendation under the quality rules.

Run [`../scripts/validate_evidence.py`](../scripts/validate_evidence.py) with the relevant `--purpose`; pass `--current-cycle` whenever mutable official facts are evaluated. In `AcademicTaskContext`, keep proposed decisions at `suggested`; only a user selection may set a decision to `explicitly_confirmed`.
