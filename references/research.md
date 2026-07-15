# Research

Prefer these sources in order:

1. Official program page.
2. Official admissions requirement page.
3. Official fee and scholarship page.
4. Official government or visa page.
5. Official testing-agency page.
6. Reputable ranking or labor-market source, only when the user asks for that dimension.

Record URL, title, publisher, access date, application cycle, and extracted requirement. If official pages conflict, report the conflict and avoid resolving it without evidence.

For research-degree discovery, verify the formal award and delivery structure rather than inferring degree type from the title or subject. Record `MPhil`, `MRes`, `MSc by Research`, another thesis-led research award, or taught degree explicitly. If the official page does not establish the research format, keep it `unknown`.

For supervisor and programme fit, separate:

- whether pre-application supervisor contact is `required`, `recommended`, `optional`, `not_required`, or `unknown`;
- the supervisor's current official research description and representative publications;
- the applicant's confirmed research interests and methods;
- modules, thesis structure, facilities, groups, and other programme-specific fit facts.

Do not treat a plausible thematic match as verified supervisor availability or willingness to supervise.

Keep these statuses independent:

| Field | Meaning |
| --- | --- |
| `source_availability` | Whether the source is currently `available`, `unavailable`, or `unknown`; availability does not verify a claim. |
| `fact_verification` | Whether the extracted fact is `unverified`, `verified`, or `conflicted`. |
| `completeness` | Whether the record is a `placeholder`, `partial`, or `complete`. |
| `application_cycle` | The admissions or visa cycle to which the fact applies. |
| `accessed_at` | When the source was retrieved. |
| `staleness` | Whether the fact is `fresh`, `stale`, or `unknown` for the intended use. |

Never collapse these fields into a single `verified` or `source status` label. A reachable page can contain an unverified, incomplete, stale, or wrong-cycle fact.

## Curated Identity Catalogue

Use [`../catalogues/index.json`](../catalogues/index.json) as the Plugin-owned discovery index when the target institution is covered. Load only the selected institution file and degree level. A catalogue row confirms only that an identity appeared in an official source at the recorded access date:

- `identity_status` stays `official_source_listed`;
- `requirements_status` stays `not_collected`;
- illustrative examples stay `illustrative_only`;
- placeholders and link-only records never become verified facts.

Retrieve the current official programme and admissions pages before verifying availability, entry requirements, fees, deadlines, documents, or application-cycle facts.
