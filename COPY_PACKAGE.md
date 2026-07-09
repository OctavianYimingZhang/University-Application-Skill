# Copy-Safe Package Guide

This repository is intended to be copied as a complete Skill + website package without carrying any populated user memory.

## Copy all functional parts

Copy these paths together:

```text
SKILL.md
skills/
references/
scripts/
contracts/
schemas/
tests/
web/
.codex-plugin/
memory/README.md
memory/blank-memory.json
COPY_PACKAGE.md
plugin-capability-manifest.v2.json
skill_manifest.json
README.md
LICENSE
```

The copied package should preserve relative paths because the root Skill links to focused Skills, reference files, setup schemas, scripts, and the web prototype.

## Keep memory blank in public copies

The GitHub version should contain only:

- `memory/README.md`
- `memory/blank-memory.json`
- `references/setup/blank-memory.schema.json`
- generic memory documentation
- UI code that creates private exports in the user's browser
- blank applicant-evidence scaffolds

Do not commit populated memory files. Private local memory paths are ignored by `.gitignore`, including:

```text
memory/local-*
memory/private-*
memory/*.local.json
memory/*.private.json
*.memory.local.json
*.memory.private.json
```

## Recommended private setup after download

1. Copy `memory/blank-memory.json` to `memory/local-user-memory.json`.
2. Fill `memory/local-user-memory.json` locally or generate it from `web/public/memory.html`.
3. Keep that file private.
4. When using ChatGPT or Codex, paste only the relevant compact memory pack rather than the whole memory archive.

## Multi-memory operating model

Use the systems together:

| System | What to store | What not to store |
| --- | --- | --- |
| Public Skill repo | Generic workflow rules, schemas, blank templates | Populated personal memory |
| Local memory JSON | Full course, writing, notes, exam, and application memory | Credentials/tokens |
| ChatGPT memory | Compact durable preferences | Full lecture archives |
| Codex workspace | Current project memory and file paths | Unrelated long-term personal data |
| Browser Memory Studio | Draft memory export and writing-style extraction | Unreviewed facts treated as final |

## Memory packs to copy into small context windows

Generate only the pack needed for the current task:

- `course_pack`: lecture coverage, slide deltas, formulas, examples, exam hints;
- `writing_pack`: writing voice, preserve/avoid rules, revision rules;
- `notes_pack`: bilingual layout, density, formula formatting, diagram preferences;
- `application_pack`: applicant profile, target programmes, source-backed requirements, document state.

This avoids overloading ChatGPT/Codex context windows while preserving a larger local source of truth.

## Safe copy checklist

Before publishing or sharing a copy:

- Search for real names, emails, phone numbers, transcripts, visa identifiers, grades, private lecture notes, writing samples, and account tokens.
- Confirm `memory/local-*` and `memory/private-*` files are not tracked.
- Confirm `memory/blank-memory.json` contains empty arrays and empty strings only.
- Confirm test fixtures and web narrative options contain no seeded applicant evidence.
- Confirm the shared `contracts/` files and `plugin-capability-manifest.v2.json` are included.
- Run local checks from `README.md` if the runtime is available.
