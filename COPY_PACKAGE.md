# Copy-Safe Plugin Package Guide

This repository is designed to be copied as a complete, independently installable Plugin without carrying populated user memory or the source of its separate companion Site.

## Copy the complete Plugin boundary

Keep these paths together:

```text
.codex-plugin/
.github/workflows/skill-health.yml
.gitignore
agents/
catalogues/
contracts/
memory/README.md
memory/blank-memory.json
references/
schemas/
scripts/
skills/
tests/
COPY_PACKAGE.md
LICENSE
README.md
SKILL.md
plugin-capability-manifest.v2.json
skill_manifest.json
```

Preserve relative paths. The router and focused Skills reference shared contracts, schemas, catalogue files, setup resources, and validators by their package-relative locations.

The copy must not add a public website directory, a Pages deployment workflow, or a browser authentication bridge. [Soleil Admissions](https://soleil-admissions.ready-loach-3659.chatgpt.site) is an owner-only companion Site maintained outside this public Plugin repository.

## Keep public memory blank

The distributable package may contain only:

- `memory/README.md`;
- `memory/blank-memory.json`;
- `references/setup/blank-memory.schema.json`;
- generic memory instructions and schemas;
- blank applicant-evidence scaffolds and synthetic test fixtures.

Do not copy populated local memory, applicant records, writing samples, transcripts, credentials, visa identifiers, or raw source files into public history. The repository ignores these private patterns:

```text
memory/local-*
memory/private-*
memory/*.local.json
memory/*.private.json
*.memory.local.json
*.memory.private.json
```

## Private setup after copying

1. Copy `memory/blank-memory.json` to `memory/local-user-memory.json`.
2. Add only user-supplied information and retain its source, date, confirmation, and freshness states.
3. Keep the populated file outside public Git history.
4. Use `scripts/extract_inspiration_file.py` locally when a runtime writing task needs provisional text blocks from an uploaded source.
5. Review every extracted fact before it can enter evidence memory or a Site case.
6. Retrieve only the smallest relevant memory pack for each task.

## Data boundaries

| System | Intended state | Excluded state |
| --- | --- | --- |
| Public Plugin repository | Workflow code, contracts, schemas, catalogue identities, blank templates | Populated personal memory and Site source |
| Local private memory | Full user-supplied structured memory and opaque source references | Credentials and public commits |
| Soleil Admissions Site | Confirmed structured cases, tasks, facts, approvals, and freshness | Raw documents, audio, full extracts, and local execution |
| ChatGPT memory | Compact durable preferences | Full source archives |
| Codex workspace | Current task state, private paths, and local execution | Unrelated long-term personal data |

## Copy validation

Before publishing or sharing a copy:

- confirm `memory/blank-memory.json` remains empty;
- search for real names, emails, phone numbers, grades, transcripts, visa identifiers, private writing, and tokens;
- confirm the shared contracts and Plugin capability manifest are present;
- confirm every indexed institution catalogue and both catalogue schemas are present;
- confirm catalogue requirements remain `not_collected`;
- confirm no retired public web or authentication surface exists;
- run the complete validation inventory in [`README.md`](README.md).
