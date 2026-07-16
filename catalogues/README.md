# Programme Identity Catalogues

`index.json` is the lazy-load index. Each `institutions/<id>.json` file contains programme identities and provenance from official university sources. The schemas under `schemas/` define the index and institution records.

Catalogue records establish only that a programme identity appeared on an official source at the recorded access date. They do not verify current entry requirements, fees, deadlines, availability, applicant fit, or visa rules. Reopen the current programme and admissions pages before relying on those facts.

Every programme preserves:

- `identity_status: official_source_listed`
- `requirements_status: not_collected`
- an official HTTPS URL
- source and access-date provenance

Run the catalogue validator after maintenance:

```bash
python3 scripts/validate_catalogues.py
```

The institution-specific builders remain separate because each official catalogue has a distinct source structure.
