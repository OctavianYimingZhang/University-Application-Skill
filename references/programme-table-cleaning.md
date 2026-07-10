# Programme Table Cleaning

Use this reference when the user asks to clean, simplify, or publish programme-list Excel workbooks as objective official-information tables.

## Purpose

Convert programme comparison workbooks into a compact official-source format. This is a presentation/export workflow over researched programme data, not a replacement for source verification.

Use it for workbook sheets that contain university programmes, awards, curriculum/training notes, entry requirements, application materials, deadlines, fees, and official URLs.

## Final Columns

Every cleaned worksheet must use exactly these 11 columns in this order:

1. `Institution`
2. `Programme`
3. `Award`
4. `Type / Delivery / Mode`
5. `Course and Training Content`
6. `Academic Requirements and Restrictions`
7. `Application and Research Materials`
8. `Application Timing and Status`
9. `Fees, Funding, and Special Notes`
10. `Official Source`
11. `Accessed Date`

Do not include country, region, ranking, direction group, department, subjective application feasibility, risk, applicant-fit advice, or internal QA fields in this cleaned export.

## Required Deletions

Delete these columns if they exist:

```text
国家/地区
排名组
排名/学校范围
标准方向组
开设单位/院系
申请状态/可行性
零基础/跨申风险
跨申补证据
适合申请者
Source_sections_checked
Verification_status
Missing_fields
Next_action
Program介绍 + 课程/训练
申请要求
学制/学习方式
费用/资金/重要信息
课程/训练/毕业要求
```

## Field Mapping

`Institution`: institution name only. Do not include country, region, ranking group, G5, QS, Times, or Top 100 labels.

`Programme`: official full programme name. Preserve terms that distinguish programme nature, such as `by thesis`, `by research`, `advanced study`, `MSc by Research`, `MRes`, `conversion`, `online`, `part-time`, and `professional`.

`Award`: award type only, such as `MPhil`, `MSc`, `MRes`, `MA`, `MBA`, `LLM`, `MPH`, or `MEng`.

`Type / Delivery / Mode`: use this exact structure:

```text
Type=...; Delivery=...; Mode=...; Duration=...; Credits=...
```

`Credits` is optional and may appear only when the official source lists credits, units, ECTS, CATS, or equivalent credit volume. Allowed `Type` values are `Taught`, `Research`, `Taught+Research`, `Professional`, `Executive/Professional`, `Conversion`, and `Directory/Listing`; use `Type=Not stated on the official source` only when no objective source signal exists. Allowed `Delivery` values are `On-campus`, `Online`, `Hybrid`, `Distance`, `Block/Residential`, `Clinical/Placement-based`, `Field-based`, and `Not stated on the official source`. Allowed `Mode` values are `FT`, `PT`, `FT/PT`, `Flexible`, and `Not stated on the official source`. Do not include subject area, academic topics, city, institution location, start date, deadline, application status, funding, fees, `uncertain`, or informal category labels.

`Course and Training Content`: official curriculum, training, research, project, and learning-activity content only. Structure the cell as:

```text
Knowledge topics: ... Methods and tools: ... Practical training: ... Programme outputs: ...
```

Use official module lists, curriculum pages, course structures, learning outcomes, programme specifications, assessment descriptions, dissertation/project pages, placement pages, and lab/fieldwork pages. Do not write generic encyclopedia summaries. Do not focus on graduation administration. Do not repeat institution, programme, award, duration, deadline, fee, source, or date. If the official source does not provide detailed syllabus information, state that explicitly inside the structured labels, for example `Knowledge topics: Not stated on the official source; detailed syllabus unavailable.`

`Academic Requirements and Restrictions`: objective eligibility only. Structure the cell as:

```text
Degree and grades: ... Subject background: ... Prerequisites and skills: ... Language: ... Standardised tests: ... Experience, qualifications, and restrictions: ...
```

Extract degree class, GPA/honours/classification, required or preferred subject background, prerequisites, required skills, IELTS/TOEFL/PTE/Duolingo exact scores and subscores, GRE/GMAT status, work experience, professional registration, licence, internal/external restrictions, supervisor requirement, visa-related eligibility restriction, and ATAS when framed as eligibility/compliance. GRE/GMAT must be stated as required, optional, not required, not accepted, or `Not stated on the official source`; do not use vague wording.

`Application and Research Materials`: application documents and research-specific documents. This includes CV, personal statement, SOP, references, transcripts, writing sample, portfolio, research proposal, supervisor contact, interview, essay questions, sample work, and professional certificates. Do not put language scores, degree requirements, deadlines, fees, course content, or subjective preparation advice here.

`Application Timing and Status`: application opening, deadline, round, rolling admission, priority deadline, funding deadline, start date, and open/closed/not-yet-open status only.

`Fees, Funding, and Special Notes`: tuition, currency, fee year, home/international fee split, application fee, deposit, reservation fee, scholarship/funding, living cost, insurance, visa cost, fieldwork/lab cost, clinical clearance, DBS/background check, and health check. Do not duplicate a fact already placed in `Academic Requirements and Restrictions`.

`Official Source`: official URLs only. Prefer programme, admissions, requirements, fees, and funding pages. Do not use QS, Times, FindAMasters, Studyportals, agency sites, forums, unofficial PDFs, or AI-generated sources.

`Accessed Date`: `YYYY-MM-DD` only.

## Empty Values

Use short factual placeholders only, and keep structured fields structured:

```text
Not stated on the official source.
Not listed on the current programme page.
Not listed on the requirements page.
Not listed on the fees page.
Not published in the application portal.
Knowledge topics: Not stated on the official source; detailed syllabus unavailable. Methods and tools: Not stated on the official source. Practical training: Not stated on the official source. Programme outputs: Not stated on the official source.
Degree and grades: Not stated on the official source. Subject background: Not stated on the official source. Prerequisites and skills: Not stated on the official source. Language: Not stated on the official source. Standardised tests: GRE/GMAT not stated on the official source. Experience, qualifications, and restrictions: Not stated on the official source.
```

Do not use long process notes such as `not retained in the source table`, `requires website verification`, `refer to the programme page`, or `fees and funding require further checking`.

## Banned Content

Remove or rewrite subjective, advisory, ranking, and internal-process language:

```text
the programme is offered by
the source table did not retain
the official source column retains
no facts were added beyond the source table
refer to the official website
requires website verification
the applicant should
recommended
suitable
risk
feasibility
fit
priority
not recommended
reach option
safety option
highly competitive
Duration/mode uncertain
uncertain from gathered evidence
requires checking
engineering/interdisciplinary
```

If an official source explicitly says `designed for`, `intended for`, `suitable for`, `recommended`, `preferred`, or `required`, rewrite it as an official-source fact, not advisor judgment.

## Suggested Cell Lengths

| Field | Suggested limit |
| --- | ---: |
| `Type / Delivery / Mode` | 120 characters |
| `Course and Training Content` | 320 characters |
| `Academic Requirements and Restrictions` | 420 characters |
| `Application and Research Materials` | 280 characters |
| `Application Timing and Status` | 360 characters |
| `Fees, Funding, and Special Notes` | 300 characters |
| `Official Source` | unlimited, but official URLs only |
| `Accessed Date` | 10 characters |

When a cell is too long, delete process language and duplicated facts before shortening factual content. Do not compensate by shrinking font size.

## QA Rules

- `Type / Delivery / Mode` must contain `Type=`, `Delivery=`, `Mode=`, and `Duration=`. It fails if it contains subject words, application status, deadlines, fees, cities used as location claims, `requires checking`, `uncertain`, or informal category labels.
- `Course and Training Content` must include at least two of `Knowledge topics:`, `Methods and tools:`, `Practical training:`, and `Programme outputs:`. It fails if it only says `Not stated on the official source`, repeats institution/programme/award identifiers, or mixes in duration, deadline, fee, language, GPA, or application-material facts.
- `Academic Requirements and Restrictions` must keep the six required labels. It fails if it only says `Not stated on the official source`, contains subjective fit/risk language, uses vague GRE/GMAT language, or hides exact language subscores when the official source provides them.

## Workflow

1. Inspect the workbook and confirm row 3 contains headers and data starts at row 4. The bundled scripts assume this shape.
2. Run `scripts/clean_programme_workbooks.py` into a separate output directory.
3. Run `scripts/verify_programme_workbooks.py` on the cleaned directory.
4. Visually inspect representative sheets for wrapping, row heights, filters, and freeze panes.
5. Copy cleaned files back only when the user explicitly asks to overwrite originals.

## Commands

The scripts require `openpyxl`; use the Codex bundled Python runtime when available.

```bash
python scripts/clean_programme_workbooks.py --source-dir "/path/to/source/workbooks" --out-dir "/path/to/cleaned/workbooks"
python scripts/verify_programme_workbooks.py --dir "/path/to/cleaned/workbooks"
```

Use `--copy-back` only when the user explicitly wants same-name source files overwritten.

## Plugin Identity-Catalogue Maintenance

The canonical curated identity catalogue is under `catalogues/`, not a website source directory. The ten official-source builders write institution JSON through `scripts/catalogue_io.py`; the Oxford builder applies the same JSON contract directly. London Business School remains an explicit reviewed static conversion because no builder existed for that legacy source.

After a catalogue refresh, run:

```bash
python3 scripts/validate_catalogues.py
python3 -m unittest tests.test_catalogues -v
```

The validator requires globally unique stable IDs, HTTPS URLs on reviewed official-host allowlists, record-level source/access provenance, English metadata, `identity_status: official_source_listed`, and `requirements_status: not_collected`. Programme requirements must be collected through a separate official-source research or requirement-audit task.
