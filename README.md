# University Application Skill

University Application Skill helps applicants research programmes, prepare admissions writing, and reach submission with current, source-backed information.

## Structure

The Plugin exposes four Skills:

| Skill | Responsibility |
| --- | --- |
| `university-application` | Route an explicit request to the matching workflow. |
| `application-research` | Discover and compare programmes, verify requirements, assess programme or supervisor fit, and maintain programme tables. |
| `application-writing` | Plan, draft, and revise SOPs, personal statements, supplements, and programme-fit writing from confirmed evidence. |
| `application-readiness` | Check materials, portal steps, references, tests, fees, deadlines, submission blockers, and administrative visa preparation. |

The router acts directly on a clear request. It asks only when a missing input would materially change the result.

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

This installs the router and three focused Skills into `~/.codex/skills` and removes the retired entrypoints owned by this Plugin.

## Validation

```bash
python3 -m compileall -q scripts
python3 scripts/validate_catalogues.py
python3 -m unittest tests.test_catalogues -v
python3 scripts/validate_evidence.py --self-test
python3 scripts/publish_skill.py --self-test
python3 scripts/validate_skill_contracts.py
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" .
python3 scripts/publish_skill.py --check-installed
git diff --check
```

## Repository map

| Path | Responsibility |
| --- | --- |
| `SKILL.md` | Shared router and operating rules. |
| `skills/` | Four public Skill entrypoints. |
| `references/` | Evidence, Research, Writing, and Readiness guidance. |
| `catalogues/` | Curated programme identities and their validators. |
| `scripts/` | Evidence, catalogue, workbook, extraction, validation, and installation tools. |
| `.codex-plugin/plugin.json` | Plugin metadata. |

## Licence

MIT. See `LICENSE`.
