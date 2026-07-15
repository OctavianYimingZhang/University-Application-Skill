# Intake

Collect only fields needed for the requested output. Intake values are hints, not confirmed evidence; normalize any value used to pass a gate under [`evidence-contract.md`](evidence-contract.md).

## Route-specific fields

- Programme discovery: target country or region, degree level or exact research award, subject area, intended intake, and relevant scope constraints.
- Requirement audit: named programme or official URL and application cycle. Add applicant qualification or language evidence only for an eligibility comparison.
- Materials check: named programme, current application cycle, and current document inventory.
- Admissions writing: programme, prompt, word or character limit, audience, intended use, applicant evidence, shared versus programme-specific narrative, canonical revision decision ledger, output location, and overwrite choice.
- Submission readiness: programme, cycle, current document/portal status, and deadline-sensitive blockers.
- Visa readiness: citizenship, destination, application location, intake, and funding basis.

Do not collect GPA, language, citizenship, budget, or unrelated profile fields merely because they exist in the setup schema. If a field affects the selected output, mark it required and keep it unresolved until its evidence record passes.

Treat values explicitly supplied in the prompt as present, including a named programme, an institution list that fixes discovery scope, a stated field, cycle, writing use, current document inventory, and an explicitly confirmed applicant fact. Do not ask the user to repeat them. When no unresolved route-specific input or scope choice remains, `build_review_questions.py` returns `questions: []` with `request_user_input_required: false`; the caller must skip `request_user_input` and continue with the matched route.
