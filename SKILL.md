---
name: university-application-index
description: Canonical source-backed university application controller. Use for international admissions research, programme shortlists, exact programme selection, requirement audits, materials readiness checks, SOP or personal-statement planning, submission readiness, student visa readiness, admissions workbooks, explicit programme-catalogue maintenance, and application-memory orchestration, including requests expressed in languages other than English.
---

# University Application Skill

Use this Skill when the user asks for university admissions planning, study-abroad programme research, application strategy, requirement checking, essay/SOP planning, document readiness, scholarship or visa-readiness notes, application workbooks, or source-backed university/application memory management.

## Core Rules

- Use official university, government, testing-agency, and scholarship sources when requirements, deadlines, fees, visa rules, or programme availability may change.
- Record source URLs and access dates for every hard requirement used in an output.
- Separate verified requirements from interpretation, fit advice, or planning suggestions.
- Do not invent rankings, deadlines, entry requirements, language rules, visa rules, scholarships, outcomes, or acceptance probabilities.
- Do not produce chance scores, safe/match/reach labels, or admission-probability predictions.
- Mark missing evidence as a gap or blocker.
- Ask only for missing inputs that materially change the plan.
- Use route-specific intake. Do not ask for GPA, language, citizenship, budget, or document status unless the selected workflow depends on that field.
- Treat `matched`, `needs_confirmation`, and `out_of_scope` as router dispositions, not focused routes. Only `matched` may enter a focused Skill; never default an unknown request to programme research.
- Keep the public package memory blank. Do not ship populated user memory, private writing samples, lecture notes, credentials, or application facts in the GitHub version.
- Default every output to English. Use another output language only when the user explicitly requests it.
- Treat raw profile values, uploads, links, and extracted text as unconfirmed until they satisfy [`references/evidence-contract.md`](references/evidence-contract.md).
- Use `public_url` evidence for mutable official facts. A private `local_document` or explicit `user_confirmation` may support the applicant's writing narrative, but user confirmation alone cannot satisfy official-requirement, materials-completion, or submission gates.
- Keep source availability, fact verification, completeness, application cycle, access date, and staleness as separate fields.
- Explain application-document requirements directly or with a compact table by default. Produce a checklist only when the user explicitly asks for one or invokes a materials/readiness workflow whose function is a checklist.

## Multiple Skill System

This root Skill is the canonical workflow contract. Load `university-application-index` first when the route is not already confirmed. It recognizes semantic intent in any language, distinguishes requirement discovery from writing and materials review, asks only route-specific questions in batches of at most three, and routes only matched application requests. `study-abroad-advisor` is a compatibility alias only.

| User request | Focused Skill |
| --- | --- |
| broad admissions help, shortlist, route unclear | [`university-application-index`](skills/university-application-index/SKILL.md) |
| programme discovery or official-source research | [`program-research`](skills/program-research/SKILL.md) |
| audit hard requirements for named programmes | [`requirement-audit`](skills/requirement-audit/SKILL.md) |
| simulate application-material readiness | [`materials-check`](skills/materials-check/SKILL.md) |
| brainstorm SOP, personal statement, supplement, or programme-fit writing | [`application-writing-studio`](skills/application-writing-studio/SKILL.md) |
| final submission checklist and blockers | [`submission-readiness`](skills/submission-readiness/SKILL.md) |
| student visa preparation and document gaps | [`visa-readiness`](skills/visa-readiness/SKILL.md) |
| explicitly requested catalogue/workbook maintenance | [`programme-table-cleaning`](skills/programme-table-cleaning/SKILL.md) |

If a focused Skill is installed as a sibling local Skill, prefer that installed focused Skill. If not, follow the linked source entrypoint and shared references in this package.

## Long-Memory Contract

This Skill coordinates several memory systems without assuming that any one context window can hold the whole user history.

- The public repository contains only blank memory templates, schemas, and generic instructions.
- The local canonical memory file should be private, for example `memory/local-user-memory.json` or another user-chosen path ignored by git.
- The owner-only Soleil Admissions Site stores confirmed structured case state; it is separate from this Plugin repository and never replaces local sensitive source storage.
- ChatGPT memory should store compact durable preferences only.
- Codex/local project memory should store task-specific working state and paths to larger local files.
- `scripts/extract_inspiration_file.py` creates provisional local text blocks from runtime files; extracted text remains unconfirmed until the user reviews it.
- Factual memory conflicts use the latest explicit correction and verified provenance. Conflicting writing instructions remain separate ledger items and must be resolved with the user; do not silently apply newest-wins to revision feedback.

Memory categories:

| Category | Purpose |
| --- | --- |
| `course_memory` | Course/module coverage, lecture sequence, formulas, examples, and assessed skills. |
| `lecture_delta_memory` | What the teacher said that was not on slides, slide corrections, skipped content, verbal examples, exam hints. |
| `writing_voice` | User-uploaded writing samples, inferred style rules, revision constraints, and phrasing preferences. |
| `source_inspiration` | Runtime-uploaded assignments, slides, readings, notes, and manual annotations used for writing ideas after user confirmation. |
| `notes_preferences` | Preferred notes density, bilingual layout, formula formatting, diagrams, tables, and explanation style. |
| `exam_preparation_preferences` | Past-paper priority, mark-scheme style, common weak points, and answer format. |
| `application_preferences` | Programme-fit writing rules, admissions priorities, document conventions, and source policy. |

Before using memory, identify the category needed, retrieve only the smallest relevant pack, and mark missing or stale memory explicitly. Do not infer private facts from writing samples unless the user asks.

## Workflow

1. Setup: capture `workflow_mode`, `output_mode`, source policy, privacy/export settings, and only the applicant or programme fields required by that route; validate setup JSON when available.
2. Memory resolution: check whether the task needs course memory, slide-delta memory, writing voice, notes preferences, application preferences, or no memory. Use blank defaults if no user memory has been supplied.
3. Intake: request only the selected route's missing fields. Applicant-fit comparison may add qualification and language evidence; requirements-only research does not.
4. Route review: use `scripts/plan_workflow.py` and `scripts/build_review_questions.py`. Continue paged batches until every material gap or writing decision is resolved. When the review payload sets `request_user_input_required: false` and returns an empty `questions` list, skip `request_user_input` and continue directly with the matched route. Keep an `AcademicTaskContext` route or decision at `suggested` until the user explicitly confirms it.
5. Programme research: verify the exact award type, including `MPhil`, `MRes`, `MSc by Research`, or another explicitly thesis-led research degree; keep taught research-themed degrees separate. Retrieve current official programme pages and verify supervisor-contact status, supervisor research and representative publications, research-area fit, modules, and programme structure when relevant.
6. Structured case file: keep one `ApplicationCase` per programme with requirements, documents, deadlines, supervisor/programme fit, writing tasks, risks, actions, workstream states, and source log. Separate shared applicant narrative from programme-specific adaptation across multiple cases.
7. Hard-requirement audit: extract application fields, document types, prompts, word or character limits, AI-use rules, fees, deadlines, references, and mandatory pre-application steps. Separate required, recommended, optional, not-required, and unknown items.
8. Materials and submission: compare the applicant's current inventory with verified current-cycle requirements. User confirmation can support writing truth but cannot by itself mark a required document or submission step complete.
9. Writing Studio: maintain its own admissions-specific `RevisionDecisionLedger`, resolve every historical feedback item and conflict, approve the structure, draft directly after approval, and run coverage review before delivery. This workflow remains independent and does not call Coursework Killer.
10. Output: return the matched route's requested artifact or structured `ApplicationCase` update. Default requirement outputs to direct explanation or a compact table, not a checklist.
11. Quality check: verify every hard requirement against a current official source and block any unresolved writing-ledger or submission item.

## Writing Studio Contract

Admissions writing is a planning and evidence task before it is a drafting task.

- Lock the writing brief before planning: programme, prompt, word or character limit, audience, submission use, applicant background, source policy, output location, and overwrite decision.
- Build an admissions-specific `RevisionDecisionLedger` from all conversation feedback before planning. Record each stable decision ID, source locator, target document or passage, action, core-argument or example role, experience function, source-use permission, voice and fact boundary, prohibited exaggeration, multi-document invariant or programme-specific variation, length/format/output/overwrite instruction, conflicts, confirmation state, implementation location, and coverage state.
- Merge only exact duplicate instructions while preserving every source locator. Ask the user to resolve conflicts; never silently prefer the newest feedback.
- Build an evidence inventory from the applicant before making claims.
- Load writing-voice memory only from user-supplied writing samples, explicit user preferences, or private local memory supplied in the current task.
- Treat runtime-uploaded assignments, slides, readings, notes, and images as source inspiration until the user confirms an insight for the evidence map.
- Distinguish what the user studied or found interesting from what the user personally did or achieved.
- Generate multiple narrative options only from supplied evidence.
- Block unsupported claims about achievements, hardship, leadership, research, publications, awards, internships, or conversations.
- Use programme-specific facts only after source verification.
- Build the programme-fit paragraph from verified modules, research groups, facilities, teaching structure, placement, accreditation, or faculty fit.
- Ask for planning approval after the structure and evidence map are visible. Once approved, draft without asking a redundant start-writing question.
- Before delivery, map every confirmed ledger decision to final text or to an explicitly confirmed rejected, superseded, or not-applicable outcome. Pending, missing, conflicted, or unlocated decisions block delivery.
- If a plan-breaking issue appears after approval, return to the writing gate instead of silently changing the structure.

## Reference Files

- `references/intake.md`: applicant intake and missing-field handling.
- `references/research.md`: official-source collection and citation rules.
- `references/programme-table-cleaning.md`: cleaning official programme tables.
- `references/workbook-schema.md`: workbook sheet structure.
- `references/essay-sop.md`: SOP and essay planning.
- `references/submission.md`: submission checklist.
- `references/quality-checks.md`: blocker and source checks.
- `references/evidence-contract.md`: normalized applicant-evidence fields and the confirmation predicate.
- `references/memory-system.md`: blank-by-default memory architecture, category schema, update rules, and multi-memory synchronization.
- `references/setup/setup-workflow.md`: interactive setup flow.
- `references/setup/task-gates.yaml`: minimum fields by workflow mode.
- `references/setup/user-setup.schema.json`: setup JSON shape.
- `references/setup/blank-memory.schema.json`: blank local memory schema.
- `schemas/application-case-v1.schema.json`: admissions-specific Site contract for an `ApplicationCase`.
- `catalogues/index.json`: Plugin-owned lazy-load index for official-source-listed programme identities; requirements remain uncollected.
- `catalogues/schemas/`: JSON Schemas for the catalogue index and institution files.

## Local Scripts

- `scripts/plan_workflow.py`: detect and describe a route from a prompt or setup JSON.
- `scripts/build_review_questions.py`: build route/source/profile/writing review payloads.
- `scripts/validate_skill_contracts.py`: check the Plugin-only package, manifests, focused Skills, route scripts, schemas, and retired-surface guards.
- `scripts/validate_evidence.py`: validate applicant-evidence records and confirmation invariants.
- `scripts/publish_skill.py`: push and/or sync this multi-skill package into local Codex Skills.
- `scripts/validate_setup.py <setup.json>`: check setup completeness for `workflow_mode` and `output_mode`.
- `scripts/build_admissions_workbook.py <case.json> <output.xlsx>`: render a source-backed workbook.
- `scripts/onboard_admissions.py`: create a blank setup JSON template with an empty memory scaffold.
- `scripts/check_setup_contract.py`: check setup schema, gates, fixtures, and template drift.
- `scripts/extract_inspiration_file.py`: parse runtime-uploaded inspiration files for text blocks with page, slide, or sheet references.
- `scripts/clean_programme_workbooks.py`: clean official programme tables.
- `scripts/verify_programme_workbooks.py`: verify cleaned programme workbooks.
- `scripts/validate_catalogues.py`: validate catalogue schemas, stable IDs, HTTPS official URLs, provenance, counts, and identity-only status.
