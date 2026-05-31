# University Application Skill

A Codex Skill for source-backed international university application planning.

## What it does

- Builds program shortlists, requirement tables, document checklists, timelines, essay plans, and application workbooks.
- Prioritizes official university, government, scholarship, and testing-agency sources.
- Separates verified requirements from strategic interpretation.
- Treats missing source evidence as a gap or blocker.

## Entrypoint

Use [`SKILL.md`](SKILL.md). Reference files are loaded only when needed.

## Repository layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Agent-facing workflow. |
| `references/` | Intake, research, essay, submission, and workbook guidance. |
| `references/setup/` | Setup prompts, task gates, and setup schema. |
| `scripts/` | Setup validation, workbook rendering, and programme-table utilities. |
| `tests/fixtures/` | Small public fixtures for local script checks. |

## Local checks

```bash
python3 -m compileall -q scripts
python3 scripts/validate_setup.py tests/fixtures/user_setup_full_shortlist.json
python3 scripts/build_admissions_workbook.py tests/fixtures/admissions_case_mvp.json /tmp/application_plan.xlsx
```

## License

See [`LICENSE`](LICENSE).
