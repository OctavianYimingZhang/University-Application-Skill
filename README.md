# University Application Skill

A multiple-skill Codex package for source-backed university application planning. `university-application-index` is the canonical controller; `study-abroad-advisor` is a compatibility alias.

It supports official programme research, hard requirement audits, confirmed-evidence application-material checks, interactive SOP/personal-statement planning, submission readiness, student visa readiness, explicit programme-table maintenance, workbook exports, and blank-by-default long-memory orchestration. It recognizes non-English intent, defaults outputs to English unless the user explicitly requests otherwise, and does not produce admission-probability predictions.

## Programme Identity Catalogue

The canonical curated catalogue is Plugin-owned data under [`catalogues/`](catalogues/), independent of the website. [`catalogues/index.json`](catalogues/index.json) provides a lazy-load index across 43 institutions; institution files preserve official-source programme identity coverage, stable IDs, HTTPS URLs, access dates, and source notes.

Catalogue coverage is identity-only. Every row is `official_source_listed` with `requirements_status: not_collected`; it does not verify entry requirements, deadlines, fees, availability, or applicant fit. Illustrative examples remain `illustrative_only`, and placeholders or link-only records cannot be treated as verified.

## Web App

The interactive prototype lives in [`web/`](web/). It is a React + Vite + TypeScript app designed as a dark, data-product style admissions workspace.

Main surfaces:

- Program Explorer: filter UK Core, U.S. News Top 30 cutoff, NUS, and NTU catalogue coverage; click official UG/PG programme options and inspect available source-backed detail pages.
- Application Checklist: identify material-readiness gaps without treating clicks, placeholders, or links as passing evidence.
- Writing Studio: lock the writing brief, upload runtime inspiration files, choose unseeded narrative structures, and block unsupported claims before drafting.
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

Use [`SKILL.md`](SKILL.md) as the canonical `university-application-index` package root.

Focused Skills live under [`skills/`](skills/):

| Skill | Purpose |
| --- | --- |
| `university-application-index` | Canonical controller for all admissions routes. |
| `study-abroad-advisor` | Thin compatibility alias for the canonical index. |
| `program-research` | Collect and compare official programme pages. |
| `requirement-audit` | Check hard academic, language, fee, deadline, and document requirements. |
| `materials-check` | Simulate application-material readiness. |
| `application-writing-studio` | Plan SOPs, personal statements, and programme-fit writing from evidence, confirmed file-derived inspiration, and optional writing-voice memory. |
| `submission-readiness` | Run final pre-submission blocker checks. |
| `visa-readiness` | Review student visa preparation from current official government sources without legal advice. |
| `programme-table-cleaning` | Explicit maintenance route for official programme tables/workbooks. |

## Repository Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Root workflow and memory contract. |
| `skills/` | Plugin router and focused Skill entrypoints. |
| `references/` | Intake, research, essay/SOP, memory, submission, workbook, and quality guidance. |
| `contracts/` | Shared Soleil interoperability schemas; byte-identical across Plugins. |
| `schemas/application-case-v1.schema.json` | Admissions-specific Site contract for a source-state-aware application case. |
| `catalogues/` | Plugin-owned lazy-load programme identity index, institution JSON files, and catalogue schemas. |
| `memory/` | Blank memory templates only; private populated files are ignored by git. |
| `scripts/` | Route planning, review-question payloads, validation, publishing, workbook rendering, and programme-table utilities. |
| `plugin-capability-manifest.v2.json` | Route ownership, gates, outputs, adapters, and supported context versions. |
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
- populated applicant-evidence records or invented test applicants;
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
python3 scripts/validate_catalogues.py
python3 -m unittest tests.test_catalogues -v
python3 scripts/check_setup_contract.py
python3 scripts/validate_skill_contracts.py
python3 scripts/plan_workflow.py --self-test
python3 scripts/build_review_questions.py --self-test
python3 scripts/validate_evidence.py --self-test
python3 scripts/publish_skill.py --dry-run --sync-local-skill
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

The bridge exposes `GET /codex/status`, `POST /codex/start-oauth`, `POST /codex/refresh`, `POST /codex/logout`, and `POST /writing/inspiration/extract`. OAuth calls proxy to `codex app-server --stdio`; inspiration extraction stays local and uses `scripts/extract_inspiration_file.py`.

## Source Policy

- Use official university, government, testing-agency, and scholarship pages for hard requirements.
- Store source URLs and access dates with extracted facts.
- Keep source availability, fact verification, completeness, application cycle, access date, and staleness separate.
- Require substantive value, real source provenance, evidence date, explicit confirmation, verified fact status, and complete content before applicant evidence passes.
- Mark missing source evidence as a gap.
- Do not invent deadlines, fees, requirements, scholarships, visa rules, or programme facts.
- Do not use acceptance-rate or probability-style prediction UI.
- Catalogue builders use normal TLS certificate verification and fail explicitly when verified requests fail.
- Curated catalogue identities use stable globally unique IDs, HTTPS official URLs, explicit source/access provenance, and `requirements_status: not_collected`.

## License

See [`LICENSE`](LICENSE).
