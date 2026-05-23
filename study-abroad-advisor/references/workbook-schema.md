# Workbook Schema

Use `scripts/build_admissions_workbook.py` to create an `.xlsx` workbook from structured JSON.

## Command

```bash
python scripts/build_admissions_workbook.py input.json output.xlsx
```

The script uses only Python standard library modules.

## Top-Level JSON

```json
{
  "workbook_title": "Student Application Plan",
  "generated_on": "2026-05-23",
  "student_profile": {},
  "school_shortlist": [],
  "programs": [],
  "requirements": [],
  "essay_plan": [],
  "submission_tasks": [],
  "sources": []
}
```

All arrays are optional. Missing values are written as blanks.

## Student Profile

Accepted keys include:

- `student_name`
- `degree_level`
- `target_intake`
- `current_country`
- `current_institution`
- `current_major`
- `gpa`
- `gpa_scale`
- `budget`
- `target_countries`
- `target_field`
- `ranking_constraints`
- `career_or_research_goal`
- `risk_tolerance`
- `language_scores`
- `tests`
- `fixed_constraints`
- `flexible_preferences`
- `missing_facts`

## School Shortlist Columns

Use these keys where available:

- `country`
- `region`
- `school`
- `city`
- `campus`
- `ranking_range`
- `school_rank`
- `subject_rank`
- `degree_level`
- `fit_category`
- `fit_score`
- `academic_fit`
- `budget_fit`
- `location_fit`
- `career_research_fit`
- `visa_work_notes`
- `scholarship_notes`
- `rationale`
- `official_source`
- `check_date`
- `notes`

## Program Columns

Use these keys where available:

- `program_id`
- `region`
- `country`
- `school`
- `ranking_range`
- `program`
- `award`
- `program_type`
- `direction_group`
- `relevance`
- `application_status`
- `fit_risk`
- `zero_background_risk`
- `coursework_training`
- `entry_requirements`
- `language_requirements`
- `duration_mode`
- `application_time_status`
- `fees_funding`
- `applicant_judgement`
- `same_school_program_count`
- `cross_table_direction_reference`
- `application_system`
- `official_source`
- `check_date`
- `notes`

The builder creates regional sheets by grouping `programs` by `region`, or by `country` when `region` is missing.

## Requirements Columns

Use these keys where available:

- `program_id`
- `school`
- `program`
- `transcript`
- `degree_certificate`
- `gpa_requirement`
- `language_test`
- `language_minimum`
- `references`
- `cv_resume`
- `essay_sop`
- `portfolio`
- `test_scores`
- `application_fee`
- `deadline`
- `application_system`
- `source`
- `check_date`
- `notes`

## Essay Plan Columns

Use these keys where available:

- `school`
- `program`
- `essay_type`
- `prompt`
- `word_limit`
- `evidence_needed`
- `program_specific_angle`
- `academic_depth_notes`
- `status`
- `source`
- `notes`

## Submission Checklist Columns

Use these keys where available:

- `school`
- `program`
- `system`
- `account`
- `task`
- `owner`
- `deadline`
- `status`
- `source`
- `notes`

## Source Log Columns

Use these keys where available:

- `source_id`
- `entity`
- `title`
- `url`
- `source_type`
- `facts_supported`
- `checked_date`
- `reliability`
- `notes`

## Spreadsheet Rules

- First row: sheet title.
- Second row: verification note.
- Third row: headers.
- Later rows: data.
- Use blanks rather than invented values.
- Put official source URLs in source columns.
- Put unresolved issues in notes columns.
