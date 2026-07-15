# Setup Workflow

1. Set `workflow_mode` and `output_mode`; deprecated `task_type` and `output_format` inputs may be normalized for old setup files. Do not collect the entire applicant profile by default: load the route gate and ask only for inputs that materially control that workflow.
2. Collect only fields required by the selected gate in `task-gates.yaml`.
3. Store applicant intake hints under `profile`; keep normalized confirmation records under `evidence_records` using [`../evidence-contract.md`](../evidence-contract.md). Profile values alone do not pass an evidence gate.
4. Initialize `memory` from `memory/blank-memory.json` unless the user supplies a private local memory file.
5. Confirm source policy before source-backed or verified output.
6. For writing, notes, or exam-preparation tasks, check whether a relevant memory pack exists: `writing_voice`, `course_memory`, `lecture_delta_memory`, `notes_preferences`, or `exam_preparation_preferences`.
7. Build the requested view from the structured setup, case data, and the smallest relevant memory pack.
8. Mark blockers and next actions instead of filling missing eligibility facts or missing memory facts. Default outputs to English unless the user explicitly requests another language.

Use `scripts/onboard_admissions.py` to create a blank setup JSON template, then fill required gate fields before running `scripts/validate_setup.py`.

Copy `memory/blank-memory.json` to an ignored private path to create local memory. Use `scripts/extract_inspiration_file.py` only for provisional local extraction, then require user review before promoting extracted content into evidence memory. The separate owner-only Soleil Admissions Site may store confirmed structured case state; sensitive originals and full extracts remain local. Do not commit populated memory to the public repository.
