# Programme Identity Catalogues

This directory is the Plugin-owned, non-UI source for curated programme identity coverage. It is independent of the legacy React website.

`index.json` is the lazy-load index. Each `institutions/<id>.json` file contains one institution's official-source programme identities and catalogue provenance. The JSON Schemas in `schemas/` define the index and institution file contracts.

Catalogue records verify only that an identity was listed by an official source at the recorded access date. They do not contain or verify entry requirements, fees, deadlines, applicant fit, or application readiness. Every programme therefore carries:

- `identity_status: official_source_listed`
- `requirements_status: not_collected`
- an HTTPS official URL
- source and access-date provenance

Illustrative examples are marked `illustrative_only`; they are not trusted programme facts. Placeholder and link-only records are never marked verified.

Run the catalogue validator before publishing:

```bash
python3 scripts/validate_catalogues.py
python3 scripts/validate_catalogues.py --json
```

The ten official-source builders update these JSON files directly. London Business School is an explicit static conversion because the legacy source had no builder; refresh it only through reviewed official-source catalogue maintenance.
