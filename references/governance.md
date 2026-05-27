# Governance

Admissions data contains private applicant information. Keep public program knowledge separate from private applicant cases.

## Private Applicant Data

Treat these as private by default:

- legal name on passport
- date of birth
- passport number or passport scan
- applicant email, phone, address
- transcript and grade documents
- bank statements and funding proof
- recommender names and email addresses
- visa refusal history
- medical, TB, police, or biometrics records
- essays that reveal private history

## Public Program Knowledge

Public or shareable only when no applicant-specific private field is included:

- institution names
- program names
- official requirements
- official fees and deadlines
- official visa/government rules
- ranking-provider facts
- source URLs and source metadata

## Output Rules

- Redact private fields in public-facing workbooks, GitHub examples, screenshots, or shared fixtures.
- Use placeholder names and official-public facts in repository fixtures.
- Do not store real passports, transcripts, bank statements, or recommender emails in the Skill repository.
- When exporting a workbook for sharing, remove or mask private applicant fields unless the user explicitly requests a private working copy.

The machine-readable policy lives in `ontology/access_policies.yaml`.
