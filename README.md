# University Application Skill

A multiple-skill Codex package for source-backed university application planning.

It supports official programme research, hard requirement audits, application-material readiness checks, interactive SOP/personal-statement planning, submission readiness, visa-sensitive notes, programme table cleaning, workbook exports, and blank-by-default long-memory orchestration for writing voice, course coverage, slide-delta notes, and user preferences. It explicitly does not produce admission-probability predictions.

## Web App

The interactive prototype lives in [`web/`](web/). It is a React + Vite + TypeScript app designed as a dark, data-product style admissions workspace.

Main surfaces:

- Program Explorer: filter UK Core, U.S. News Top 30 cutoff, NUS, and NTU catalogue coverage; click official UG/PG programme options and inspect source-backed hard requirements where detail pages are seeded.
- Application Checklist: simulate material readiness against a selected programme.
- Writing Studio: lock the writing brief, choose narrative options, map evidence, and block unsupported claims before drafting.
- Codex OAuth Runtime: a Hermes-style panel that calls Codex account/OAuth actions through Codex app-server or the included local HTTP bridge without storing bearer tokens in the browser.
- Memory Studio: a static browser page at [`web/public/memory.html`](web/public/memory.html) for uploading writing samples, adding lecture/slide-delta notes, and exporting private memory JSON or compact ChatGPT/Codex memory packs.

GitHub Pages deployment is configured through `.github/workflows/pages.yml`.

Expected Pages URL:

```text
https://octavianyimingzhang.github.io/University-Application-Skill/
```

Expected Memory Studio URL after Pages deployment:

```text
https://octavianyimingzhang.github.io/University-Application-Skill/memory.html
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
| `application-writing-studio` | Plan SOPs, personal statements, and programme-fit writing from evidence and optional writing-voice memory. |
| `submission-readiness` | Run final pre-submission blocker checks. |
| `programme-table-cleaning` | Clean and verify official programme tables/workbooks. |

## Repository Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Root workflow and memory contract. |
| `skills/` | Plugin router and focused Skill entrypoints. |
| `references/` | Intake, research, essay/SOP, memory, submission, workbook, and quality guidance. |
| `memory/` | Blank memory templates only; private populated files are ignored by git. |
| `scripts/` | Route planning, review-question payloads, validation, publishing, workbook rendering, and programme-table utilities. |
| `web/` | Interactive admissions website prototype plus static Memory Studio page. |
| `.codex-plugin/` | Plugin metadata. |
| `.github/workflows/` | Skill health and GitHub Pages workflows. |
| `COPY_PACKAGE.md` | Copy-safe installation and distribution notes for the website, Skill, scripts, and blank memory templates. |

## Blank Memory Policy

The public GitHub version must not contain populated user memory.

Allowed in the repository:

- blank schemas;
- empty JSON templates;
- generic memory category names;
- UI code that lets a user create a private export.

Not allowed in the repository:

- real writing samples;
- real lecture notes or slide annotations;
- private applicant facts;
- credentials, tokens, emails, visa data, or local account details;
- filled `memory/local-*` files.

The recommended local path for a private copy is:

```text
memory/local-user-memory.json
```

That path is ignored by git.

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

The GitHub Pages build is static. Browser pages cannot safely perform Codex token exchange or read local Codex auth files. Use the included local bridge when testing the OAuth tab:

```bash
node scripts/codex_oauth_bridge.mjs --port 8787
```

Then open the site with:

```text
?codex_bridge=http://127.0.0.1:8787
```

The bridge exposes only `GET /codex/status`, `POST /codex/start-oauth`, `POST /codex/refresh`, and `POST /codex/logout`, and it proxies those calls to `codex app-server --stdio`.

## Source Policy

- Use official university, government, testing-agency, and scholarship pages for hard requirements.
- Store source URLs and access dates with extracted facts.
- Mark missing source evidence as a gap.
- Do not invent deadlines, fees, requirements, scholarships, visa rules, or programme facts.
- Do not use acceptance-rate or probability-style prediction UI.

## License

See [`LICENSE`](LICENSE).
