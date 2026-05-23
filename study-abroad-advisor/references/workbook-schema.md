# Workbook Schema

Use `scripts/build_admissions_workbook.py` to create an `.xlsx` workbook from structured JSON.

## Command

```bash
python scripts/build_admissions_workbook.py input.json output.xlsx
```

The script uses only Python standard library modules. If `ontology` data exists, the builder runs `scripts/validate_ontology.py` quality gates before rendering. Use `--skip-validation` only for a draft workbook that must not be treated as verified output.

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
    "source_snapshots": [],
    "extracted_facts": [],
    "fact_versions": [],
    "lineage_edges": [],
    "quality_checks": [],
    "pipeline_runs": [],
    "action_events": [],
    "tasks": [],
    "risk_flags": [],
    "deadlines": [],
    "offer_decisions": [],
    "visa_immigration_cases": [],
    "student_evidence": [],
    "program_fit_facts": [],
    "essay_claims": [],
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

When both ontology and legacy arrays exist, core views are derived from ontology objects first. Legacy arrays are used only when the equivalent ontology objects are absent, and should be treated as draft compatibility input.

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
- `ontology.source_snapshots` -> `Source Snapshots`
- `ontology.extracted_facts` -> `Extracted Facts`
- `ontology.fact_versions` -> `Fact Versions`
- `ontology.lineage_edges` -> `Lineage Edges`
- `ontology.quality_checks` -> `Quality Checks`
- `ontology.pipeline_runs` -> `Pipeline Runs`
- `ontology.action_events` -> `Action Events`
- `ontology.student_evidence` -> `Student Evidence`
- `ontology.program_fit_facts` -> `Program Fit Facts`
- `ontology.essay_claims` -> `Essay Claims`

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
- `source_snapshot_id`
- `extracted_fact_id`
- `fact_version_id`
- `lineage_edge_id`
- `quality_check_id`
- `pipeline_run_id`
- `action_event_id`
- `student_evidence_id`
- `program_fit_fact_id`
- `essay_claim_id`

## Source Snapshot Columns

Use these keys where available:

- `source_snapshot_id`
- `source_evidence_id`
- `url`
- `retrieved_at`
- `content_hash`
- `raw_title`
- `raw_excerpt`
- `http_status`
- `cycle_hint`
- `snapshot_status`
- `notes`

## Extracted Fact Columns

Use these keys where available:

- `extracted_fact_id`
- `source_snapshot_id`
- `entity_type`
- `entity_id`
- `fact_text`
- `normalized_key`
- `extraction_confidence`
- `extraction_method`
- `verification_status`
- `notes`

## Fact Version Columns

Use these keys where available:

- `fact_version_id`
- `extracted_fact_id`
- `previous_value`
- `current_value`
- `changed_at`
- `change_type`
- `impact_scope`
- `notes`

## Lineage Edge Columns

Use these keys where available:

- `lineage_edge_id`
- `from_object_id`
- `from_object_type`
- `to_object_id`
- `to_object_type`
- `transformation`
- `evidence_required`
- `notes`

## Quality Check Columns

Use these keys where available:

- `quality_check_id`
- `check_name`
- `target_object_type`
- `severity`
- `logic`
- `on_fail`
- `status`
- `notes`

## Pipeline Run Columns

Use these keys where available:

- `pipeline_run_id`
- `workflow_name`
- `started_at`
- `finished_at`
- `input_object_ids`
- `output_object_ids`
- `quality_check_ids`
- `status`
- `notes`

## Action Event Columns

Use these keys where available:

- `action_event_id`
- `action_type`
- `actor`
- `target_object_id`
- `before_state`
- `after_state`
- `validation_results`
- `source_evidence_ids`
- `created_at`
- `notes`

## Student Evidence Columns

Use these keys where available:

- `student_evidence_id`
- `applicant_id`
- `evidence_type`
- `description`
- `document_id`
- `verification_status`
- `notes`

## Program Fit Fact Columns

Use these keys where available:

- `program_fit_fact_id`
- `program_id`
- `fact_type`
- `fact_text`
- `source_evidence_id`
- `verification_status`
- `notes`

## Essay Claim Columns

Use these keys where available:

- `essay_claim_id`
- `application_case_id`
- `claim_type`
- `claim_text`
- `student_evidence_ids`
- `program_fit_fact_ids`
- `status`
- `notes`

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
