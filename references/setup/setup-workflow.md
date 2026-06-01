# Setup Workflow

1. Set `workflow_mode` and `output_mode`; deprecated `task_type` and `output_format` inputs may be normalized for old setup files.
2. Collect only fields required by the selected gate in `task-gates.yaml`.
3. Store applicant-specific fields under `profile`; keep workflow, privacy, source, and export settings at the top level.
4. Confirm source policy before source-backed or verified output.
5. Build the requested view from the structured setup and case data.
6. Mark blockers and next actions instead of filling missing eligibility facts.

Use `scripts/onboard_admissions.py` to create a blank setup JSON template, then fill required gate fields before running `scripts/validate_setup.py`.
