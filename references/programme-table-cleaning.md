# Programme Table Cleaning

Use this reference when the user asks to clean, simplify, or publish programme-list Excel workbooks as objective official-information tables.

## Purpose

Convert programme comparison workbooks into a compact official-source format. This is a presentation/export workflow over researched programme data, not a replacement for source verification.

Use it for workbook sheets that contain university programmes, awards, curriculum/training notes, entry requirements, application materials, deadlines, fees, and official URLs.

## Final Columns

Every cleaned worksheet must use exactly these 11 columns in this order:

1. `学校`
2. `Program`
3. `Award`
4. `项目类型/学习方式`
5. `课程/训练内容`
6. `学术背景/限制条件`
7. `申请材料/研究要求`
8. `申请时间/状态`
9. `费用/资金/特殊事项`
10. `官方来源`
11. `核对日期`

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

`学校`: school name only. Do not include country, region, ranking group, G5, QS, Times, or Top 100 labels.

`Program`: official full programme name. Preserve terms that distinguish programme nature, such as `by thesis`, `by research`, `advanced study`, `MSc by Research`, `MRes`, `conversion`, `online`, `part-time`, and `professional`.

`Award`: award type only, such as `MPhil`, `MSc`, `MRes`, `MA`, `MBA`, `LLM`, `MPH`, or `MEng`.

`项目类型/学习方式`: use this exact structure:

```text
Type=...；Delivery=...；Mode=...；Duration=...；Credits=...
```

`Credits` is optional and may appear only when the official source lists credits, units, ECTS, CATS, or equivalent credit volume. Allowed `Type` values are `Taught`, `Research`, `Taught+Research`, `Professional`, `Executive/Professional`, `Conversion`, and `Directory/Listing`; use `Type=官网未列明` only when no objective source signal exists. Allowed `Delivery` values are `On-campus`, `Online`, `Hybrid`, `Distance`, `Block/Residential`, `Clinical/Placement-based`, `Field-based`, and `官网未列明`. Allowed `Mode` values are `FT`, `PT`, `FT/PT`, `Flexible`, and `官网未列明`. Do not include subject area, academic topics, city, school location, start date, deadline, application status, funding, fees, `需核对`, `uncertain`, or informal labels such as `工程/交叉`.

`课程/训练内容`: official curriculum, training, research, project, and learning-activity content only. Structure the cell as:

```text
知识主题：...。方法/工具：...。实践训练：...。项目输出：...。
```

Use official module lists, curriculum pages, course structures, learning outcomes, programme specifications, assessment descriptions, dissertation/project pages, placement pages, and lab/fieldwork pages. Do not write generic encyclopedia summaries. Do not focus on graduation administration. Do not repeat school, programme, award, duration, deadline, fee, source, or date. If the official source does not provide detailed syllabus information, state that explicitly inside the structured labels, for example `知识主题：官网未列明 detailed syllabus。`

`学术背景/限制条件`: objective eligibility only. Structure the cell as:

```text
学位/成绩：...。专业背景：...。先修/技能：...。语言：...。标化：...。工作/资格/限制：...。
```

Extract degree class, GPA/honours/classification, required or preferred subject background, prerequisites, required skills, IELTS/TOEFL/PTE/Duolingo exact scores and subscores, GRE/GMAT status, work experience, professional registration, licence, internal/external restrictions, supervisor requirement, visa-related eligibility restriction, and ATAS when framed as eligibility/compliance. GRE/GMAT must be stated as required, optional, not required, not accepted, or `官网未列明`; do not use vague wording such as `视情况`.

`申请材料/研究要求`: application documents and research-specific documents. This includes CV, personal statement, SOP, references, transcripts, writing sample, portfolio, research proposal, supervisor contact, interview, essay questions, sample work, and professional certificates. Do not put language scores, degree requirements, deadlines, fees, course content, or subjective preparation advice here.

`申请时间/状态`: application opening, deadline, round, rolling admission, priority deadline, funding deadline, start date, and open/closed/not-yet-open status only.

`费用/资金/特殊事项`: tuition, currency, fee year, home/international fee split, application fee, deposit, reservation fee, scholarship/funding, living cost, insurance, visa cost, fieldwork/lab cost, clinical clearance, DBS/background check, and health check. Do not duplicate a fact already placed in `学术背景/限制条件`.

`官方来源`: official URLs only. Prefer programme, admissions, requirements, fees, and funding pages. Do not use QS, Times, FindAMasters, Studyportals, agency sites, forums, unofficial PDFs, or AI-generated sources.

`核对日期`: `YYYY-MM-DD` only.

## Empty Values

Use short factual placeholders only, and keep structured fields structured:

```text
官网未列明。
当前项目页未列出。
Requirements page 未列出。
Fees page 未列出。
Application portal 信息未公开。
知识主题：官网未列明 detailed syllabus。方法/工具：官网未列明。实践训练：官网未列明。项目输出：官网未列明。
学位/成绩：官网未列明。专业背景：官网未列明。先修/技能：官网未列明。语言：官网未列明。标化：GRE/GMAT 官网未列明。工作/资格/限制：官网未列明。
```

Do not use long process notes such as `源表未保留`, `需官网复核`, `以项目页为准`, or `费用、资金或重要信息需进一步核对`.

## Banned Content

Remove or rewrite subjective, advisory, ranking, and internal-process language:

```text
为 XX 项目
开设院校为
开设单位为
官网信息显示
项目页或源表记录
官网或源表记录
源表未保留
官方来源列保留
未添加源表外内容
以官网为准
需官网复核
申请者应
需核验
核验
建议
适合
风险
可行性
匹配
优先
不建议
可作为
冲刺
保底
竞争激烈
Duration/mode uncertain
uncertain from gathered evidence
需核对
工程/交叉
```

If an official source explicitly says `designed for`, `intended for`, `suitable for`, `recommended`, `preferred`, or `required`, rewrite it as an official-source fact, not advisor judgment.

## Suggested Cell Lengths

| Field | Suggested limit |
| --- | ---: |
| `项目类型/学习方式` | 80 Chinese characters |
| `课程/训练内容` | 220 Chinese characters |
| `学术背景/限制条件` | 260 Chinese characters |
| `申请材料/研究要求` | 200 Chinese characters |
| `申请时间/状态` | 300 Chinese characters |
| `费用/资金/特殊事项` | 220 Chinese characters |
| `官方来源` | unlimited, but official URLs only |
| `核对日期` | 10 characters |

When a cell is too long, delete process language and duplicated facts before shortening factual content. Do not compensate by shrinking font size.

## QA Rules

- `项目类型/学习方式` must contain `Type=`, `Delivery=`, `Mode=`, and `Duration=`. It fails if it contains subject words, application status, deadlines, fees, cities used as location claims, `需核对`, `uncertain`, or informal category labels.
- `课程/训练内容` must include at least two of `知识主题：`, `方法/工具：`, `实践训练：`, and `项目输出：`. It fails if it is only `官网未列明`, repeats school/programme/award identifiers, or mixes in duration, deadline, fee, language, GPA, or application-material facts.
- `学术背景/限制条件` must keep the six required labels. It fails if it is only `官网未列明`, contains subjective fit/risk language, uses vague GRE/GMAT language, or hides exact language subscores when the official source provides them.

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
