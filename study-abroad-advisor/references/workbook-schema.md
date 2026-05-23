# Workbook Schema

Use `scripts/build_admissions_workbook.py` to create an `.xlsx` workbook from structured JSON.

## Command

```bash
python scripts/build_admissions_workbook.py input.json output.xlsx
```

The script uses only Python standard library modules.

## Top-Level JSON

Preferred ontology-first input:

```json
{
  "workbook_title": "Student Application Plan",
  "generated_on": "2026-05-23",
  "ontology": {
    "applicants": [],
    "education_credentials": [],
    "institutions": [],
    "programs": [],
    "application_cases": [],
    "requirement_rules": [],
    "document_artifacts": [],
    "source_evidence": [],
    "tasks": [],
    "risk_flags": [],
    "deadlines": [],
    "offer_decisions": [],
    "visa_immigration_cases": [],
    "links": []
  }
}
```

Legacy input is still accepted:

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

When both ontology and legacy arrays exist, the builder renders both. The ontology remains the source of truth; legacy sheets are compatibility views.

## Student Profile

Accepted keys include:

- `applicant_id`
- `student_name`
- `degree_level`
- `target_intake`
- `citizenship_countries`
- `residence_country`
- `education_country`
- `passport_country`
- `visa_application_country`
- `document_language`
- `funding_source_country`
- `prior_residence_history`
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

## Ontology Object Sheets

The builder renders these ontology arrays when present:

- `ontology.applicants` -> `Applicant Objects`
- `ontology.education_credentials` -> `Credentials`
- `ontology.institutions` -> `Institution Objects`
- `ontology.programs` -> `Program Objects`
- `ontology.application_cases` -> `Application Cases`
- `ontology.requirement_rules` -> `Requirement Rules`
- `ontology.document_artifacts` -> `Document Artifacts`
- `ontology.tasks` -> `Tasks`
- `ontology.risk_flags` -> `Risk Flags`
- `ontology.deadlines` -> `Deadlines`
- `ontology.offer_decisions` -> `Offer Decisions`
- `ontology.visa_immigration_cases` -> `Visa Cases`
- `ontology.source_evidence` -> `Source Evidence`

Use IDs consistently:

- `applicant_id`
- `credential_id`
- `institution_id`
- `program_id`
- `application_case_id`
- `requirement_rule_id`
- `document_id`
- `task_id`
- `risk_id`
- `deadline_id`
- `offer_id`
- `visa_case_id`
- `source_evidence_id`

## Application Case Columns

Use these keys where available:

- `application_case_id`
- `applicant_id`
- `program_id`
- `institution_id`
- `school`
- `program`
- `cycle`
- `intake`
- `route`
- `status`
- `fit_category`
- `academic_fit`
- `budget_fit`
- `timing_fit`
- `visa_work_fit`
- `risk_summary`
- `last_verified_at`
- `blocking_tasks`
- `source_evidence_ids`
- `notes`

## Requirement Rule Columns

Use these keys where available:

- `requirement_rule_id`
- `application_case_id`
- `program_id`
- `jurisdiction`
- `rule_category`
- `applies_when`
- `requirement_text`
- `required_document_type`
- `source_evidence_id`
- `checked_at`
- `valid_from`
- `valid_until`
- `stale_after_days`
- `verification_status`
- `notes`

## Document Artifact Columns

Use these keys where available:

- `document_id`
- `applicant_id`
- `application_case_id`
- `document_type`
- `issuing_country`
- `language`
- `translation_required`
- `legalisation_required`
- `version`
- `status`
- `expiry_date`
- `linked_requirement_ids`
- `file_name`
- `notes`

## Task Columns

Use these keys where available:

- `task_id`
- `application_case_id`
- `task_type`
- `owner`
- `due_at`
- `timezone`
- `status`
- `blocking_requirement_ids`
- `evidence_required`
- `source_evidence_id`
- `notes`

## Risk Flag Columns

Use these keys where available:

- `risk_id`
- `application_case_id`
- `category`
- `severity`
- `rationale`
- `evidence_id`
- `status`
- `notes`

## Visa Case Columns

Use these keys where available:

- `visa_case_id`
- `application_case_id`
- `destination_country`
- `visa_or_permit_type`
- `route_status`
- `post_offer_document_id`
- `required_document_ids`
- `source_evidence_ids`
- `notes`

## School Shortlist Columns

Use these keys where available:

- `application_case_id`
- `institution_id`
- `source_evidence_ids`
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
- `institution_id`
- `application_case_id`
- `source_evidence_ids`
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

- `requirement_rule_id`
- `application_case_id`
- `source_evidence_id`
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

- `task_id`
- `application_case_id`
- `blocking_requirement_ids`
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

- `source_evidence_id`
- `source_id`
- `entity`
- `title`
- `url`
- `source_type`
- `facts_supported`
- `checked_date`
- `checked_at`
- `retrieved_at`
- `reliability`
- `stale_after_days`
- `verification_status`
- `quote_or_excerpt`
- `notes`

## Spreadsheet Rules

- First row: sheet title.
- Second row: verification note.
- Third row: headers.
- Later rows: data.
- Use blanks rather than invented values.
- Put official source URLs in source columns.
- Put unresolved issues in notes columns.
- Put object IDs in every view that can be traced back to ontology objects.
- Do not mark a row verified unless the backing object has `SourceEvidence` and `verification_status` is `verified`.
