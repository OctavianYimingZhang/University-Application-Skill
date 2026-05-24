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
5. `课程/训练/毕业要求`
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
```

## Field Mapping

`学校`: school name only. Do not include country, region, ranking group, G5, QS, Times, or Top 100 labels.

`Program`: official full programme name. Preserve terms that distinguish programme nature, such as `by thesis`, `by research`, `advanced study`, `MSc by Research`, `MRes`, `conversion`, `online`, `part-time`, and `professional`.

`Award`: award type only, such as `MPhil`, `MSc`, `MRes`, `MA`, `MBA`, `LLM`, `MPH`, or `MEng`.

`项目类型/学习方式`: taught/research/professional/conversion, full-time/part-time/online/hybrid/campus-based, duration, credits/units, and start term. Do not include course content, entry requirements, language requirements, deadlines, fees, fit, or application advice.

`课程/训练/毕业要求`: official curriculum, training, research, project, and graduation structure only. This can include core modules, electives, research project, dissertation, thesis, lab work, fieldwork, placement, internship, seminars, workshops, capstone, assessment, oral presentation, portfolio, or viva. Do not repeat school, programme, award, duration, deadline, fee, source, or date.

`学术背景/限制条件`: objective eligibility only. This includes degree requirement, GPA/honours/classification, required subject background, prerequisites, required skills, language requirements, IELTS/TOEFL/PTE, GRE/GMAT, work experience, professional registration, licence, internal/external restrictions, supervisor requirement, visa-related eligibility restriction, or ATAS when framed as eligibility/compliance.

`申请材料/研究要求`: application documents and research-specific documents. This includes CV, personal statement, SOP, references, transcripts, writing sample, portfolio, research proposal, supervisor contact, interview, essay questions, sample work, and professional certificates. Do not put language scores, degree requirements, deadlines, fees, course content, or subjective preparation advice here.

`申请时间/状态`: application opening, deadline, round, rolling admission, priority deadline, funding deadline, start date, and open/closed/not-yet-open status only.

`费用/资金/特殊事项`: tuition, currency, fee year, home/international fee split, application fee, deposit, reservation fee, scholarship/funding, living cost, insurance, visa cost, fieldwork/lab cost, clinical clearance, DBS/background check, and health check. Do not duplicate a fact already placed in `学术背景/限制条件`.

`官方来源`: official URLs only. Prefer programme, admissions, requirements, fees, and funding pages. Do not use QS, Times, FindAMasters, Studyportals, agency sites, forums, unofficial PDFs, or AI-generated sources.

`核对日期`: `YYYY-MM-DD` only.

## Empty Values

Use short factual placeholders only:

```text
官网未列明。
当前项目页未列出。
Requirements page 未列出。
Fees page 未列出。
Application portal 信息未公开。
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
```

If an official source explicitly says `designed for`, `intended for`, `suitable for`, `recommended`, `preferred`, or `required`, rewrite it as an official-source fact, not advisor judgment.

## Suggested Cell Lengths

| Field | Suggested limit |
| --- | ---: |
| `项目类型/学习方式` | 80 Chinese characters |
| `课程/训练/毕业要求` | 220 Chinese characters |
| `学术背景/限制条件` | 260 Chinese characters |
| `申请材料/研究要求` | 200 Chinese characters |
| `申请时间/状态` | 300 Chinese characters |
| `费用/资金/特殊事项` | 220 Chinese characters |
| `官方来源` | unlimited, but official URLs only |
| `核对日期` | 10 characters |

When a cell is too long, delete process language and duplicated facts before shortening factual content. Do not compensate by shrinking font size.

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
