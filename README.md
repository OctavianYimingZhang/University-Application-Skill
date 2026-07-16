# University Application Skill

University Application Skill helps applicants research programmes, prepare admissions writing, reach submission, handle administrative visa steps, and maintain programme data with current, source-backed information.

## Structure

The current manifest exposes these Skills:

| Skill | Responsibility |
| --- | --- |
| `university-application` | Route an explicit request to the matching workflow. |
| `application-research` | Discover and compare programmes, verify requirements, and assess programme or supervisor fit. |
| `application-writing` | Plan, draft, and revise SOPs, personal statements, supplements, and programme-fit writing from confirmed evidence. |
| `application-readiness` | Check materials, portal steps, references, tests, fees, deadlines, and submission blockers. |
| `application-visa` | Check jurisdiction-specific student-visa requirements, evidence, timelines, and actions. |
| `application-data` | Maintain and validate programme catalogues, tables, CSV/XLSX files, and workbooks. |

The router acts directly on a clear request. It asks only when a missing input would materially change the result.

The number of focused Skills is manifest-driven. Add or split a Skill when intent, evidence authority, workflow, toolchain, or output is materially independent; merge or remove it when those boundaries are shared.

## Evidence model

- Use current official university pages for programme availability, requirements, fees, deadlines, and application instructions.
- Use official government sources for student-visa rules and record the jurisdiction and access date.
- Keep catalogue identities separate from current requirements.
- Use applicant facts that the applicant supplied or confirmed.
- Keep verified facts, strategic interpretation, and unresolved gaps distinct.
- Report eligibility and fit factors without converting them into admission-probability scores.

The catalogue under `catalogues/` contains official-source programme identities. Each selected programme still requires current-page verification.

## Installation

```bash
git clone https://github.com/OctavianYimingZhang/University-Application-Skill.git
cd University-Application-Skill
python3 scripts/publish_skill.py --sync-local-skill
python3 scripts/publish_skill.py --check-installed
```

This installs every Skill declared by `skill_manifest.json` into `~/.codex/skills` and removes retired entrypoints owned by this Plugin.

## Validation

```bash
python3 -m compileall -q scripts
python3 scripts/validate_catalogues.py
python3 -m unittest tests.test_catalogues -v
python3 scripts/validate_evidence.py --self-test
python3 scripts/publish_skill.py --self-test
python3 scripts/validate_skill_contracts.py
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
for skill in skills/*; do
  test -f "$skill/SKILL.md" && python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" "$skill"
done
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" .
python3 scripts/publish_skill.py --check-installed
git diff --check
```

## Repository map

| Path | Responsibility |
| --- | --- |
| `SKILL.md` | Shared router and operating rules. |
| `skills/` | Manifest-declared Router and focused Skill entrypoints. |
| `references/` | Shared evidence, Research, Writing, Readiness, and Visa guidance. |
| `catalogues/` | Curated programme identities and their validators. |
| `scripts/` | Evidence, catalogue, workbook, extraction, validation, and installation tools. |
| `.codex-plugin/plugin.json` | Plugin metadata. |

## Licence

MIT. See `LICENSE`.
