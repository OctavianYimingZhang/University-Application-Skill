# University Application Skill

A multiple-skill Codex package for source-backed university application planning.

It supports official programme research, hard requirement audits, application-material readiness checks, interactive SOP/personal-statement planning, submission readiness, visa-sensitive notes, programme table cleaning, and workbook exports. It explicitly does not produce admission-probability predictions.

## Web App

The interactive prototype lives in [`web/`](web/). It is a React + Vite + TypeScript app designed as a dark, data-product style admissions workspace.

Main surfaces:

- Program Explorer: filter UK Core, U.S. News Top 30 cutoff, NUS, and NTU catalogue coverage; click official UG/PG programme options and inspect source-backed hard requirements where detail pages are seeded.
- Application Checklist: simulate material readiness against a selected programme.
- Writing Studio: lock the writing brief, choose narrative options, map evidence, and block unsupported claims before drafting.
- Codex OAuth Bridge: a static-safe integration panel that mirrors explicit Codex/Hermes-style status, start, refresh, and reset actions without storing tokens in the browser.

GitHub Pages deployment is configured through `.github/workflows/pages.yml`.

Expected Pages URL:

```text
https://octavianyimingzhang.github.io/University-Application-Skill/
```

## Skill Entrypoints

Use [`SKILL.md`](SKILL.md) as the package root.

Focused Skills live under [`skills/`](skills/):

| Skill | Purpose |
| --- | --- |
| `study-abroad-advisor` | Plugin/root router. |
| `university-application-index` | Route broad admissions requests. |
| `program-research` | Collect and compare official programme pages. |
| `requirement-audit` | Check hard academic, language, fee, deadline, and document requirements. |
| `materials-check` | Simulate application-material readiness. |
| `application-writing-studio` | Plan SOPs, personal statements, and programme-fit writing from evidence. |
| `submission-readiness` | Run final pre-submission blocker checks. |
| `programme-table-cleaning` | Clean and verify official programme tables/workbooks. |

## Repository Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Root workflow contract. |
| `skills/` | Plugin router and focused Skill entrypoints. |
| `references/` | Intake, research, essay/SOP, submission, workbook, and quality guidance. |
| `scripts/` | Route planning, review-question payloads, validation, publishing, workbook rendering, and programme-table utilities. |
| `web/` | Interactive admissions website prototype. |
| `.codex-plugin/` | Plugin metadata. |
| `.github/workflows/` | Skill health and GitHub Pages workflows. |

## Local Checks

```bash
python3 -m compileall -q scripts
python3 scripts/check_setup_contract.py
python3 scripts/validate_skill_contracts.py
python3 scripts/plan_workflow.py --self-test
python3 scripts/build_review_questions.py --self-test
python3 scripts/publish_skill.py --dry-run --sync-local-skill
python3 scripts/validate_setup.py tests/fixtures/user_setup_full_shortlist.json
python3 scripts/build_admissions_workbook.py tests/fixtures/admissions_case_mvp.json /tmp/application_plan.xlsx
cd web && npm ci && npm run build
```

If the global npm cache has local permission issues, use the repository-local cache:

```bash
cd web && npm ci --cache .npm-cache && npm run build
```

## Web Development

```bash
cd web
npm install
npm run dev
npm run build
```

The GitHub Pages build is static. The Codex OAuth tab does not perform token exchange in the browser. Real Codex auth must run through Codex CLI/Desktop or a trusted bridge endpoint supplied as `?codex_bridge=https://...`.

## Source Policy

- Use official university, government, testing-agency, and scholarship pages for hard requirements.
- Store source URLs and access dates with extracted facts.
- Mark missing source evidence as a gap.
- Do not invent deadlines, fees, requirements, scholarships, visa rules, or programme facts.
- Do not use acceptance-rate or probability-style prediction UI.

## License

See [`LICENSE`](LICENSE).
