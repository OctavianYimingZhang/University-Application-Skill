---
name: application-writing-studio
description: Interactive admissions writing planning workflow for SOPs, personal statements, programme-fit paragraphs, and supplemental essays. Use when the user wants to brainstorm, structure, evidence-check, draft, revise, or learn from uploaded writing samples and inspiration files with brief lock, source inspiration intake, evidence inventory, narrative options, programme fit, critical review, planning approval, draft gates, and writing-voice memory controls.
---

# Application Writing Studio

Use this focused Skill for admissions writing. The core job is to help the user think through the document before drafting.

## Workflow

1. Read [`../../references/essay-sop.md`](../../references/essay-sop.md), [`../../references/memory-system.md`](../../references/memory-system.md), and [`../../references/evidence-contract.md`](../../references/evidence-contract.md).
2. Lock the writing brief: programme, prompt, word or character limit, audience, output use, source policy, applicant background, submission deadline, output location, and whether an existing file may be overwritten.
3. Check whether the user has supplied writing-voice memory or uploaded writing samples. If not, use blank defaults and do not invent voice rules.
4. Run source inspiration intake when the user uploads writing assignments, lecture slides, coursework, readings, notes, spreadsheets, or images:
   - extract or summarize only what is present in the supplied file or manual annotation;
   - classify `Interest Signals`, `Knowledge Evidence`, `Methods / Concepts`, `Possible Essay Angles`, and `Unsupported Claims`;
   - ask the user to confirm any insight before it enters the evidence map or resolves a writing gap.
5. Build a normalized evidence inventory from the user. Use `public_url` for official programme facts; use `local_document` or `user_confirmation` for an applicant fact only when the corresponding writing claim is explicit and confirmed. An item enters the evidence map only after `value`, source provenance, evidence date, explicit confirmation, verification, completeness, cycle, access date, and staleness are recorded:
   - academic projects, modules, grades, methods, readings, labs, clinical/professional exposure, internships, leadership, awards, failures, and goals.
6. Build an internal `RevisionDecisionLedger` under the canonical `revision_decision_ledger` key from every historical instruction, draft comment, sample-derived preference, and requested change. Treat `writing_revision_items` only as a legacy input alias. Each item records a stable ID, all source locators, document and passage target, category, exact instruction, conflict or supersession links, confirmation status, implementation locations, and coverage status.
7. Confirm every ledger item through paged `writing-revision` questions before planning. Merge only exact duplicates while preserving every source locator. Conflicts must be shown to the user; do not silently apply newest-wins.
8. Generate narrative options only from supplied and confirmed evidence.
9. Build an evidence map for the selected option.
10. Build a programme-fit paragraph plan using verified programme facts, including supervisor research and representative publications, research-area fit, programme structure, and modules when relevant.
11. For multiple applications, lock the shared narrative and evidence that must remain invariant, then confirm each programme's distinct emphasis, supervisor/course fit, prompt response, and length allocation.
12. Run a critical review:
   - unsupported claims;
   - weak causal links;
   - generic programme fit;
   - tone or ownership risks;
   - mismatch with supplied writing voice;
   - missing evidence.
13. Display the structure, evidence map, and resolved revision ledger, then request planning approval.
14. After approval, draft directly without asking whether to start.
15. If a plan-breaking evidence gap appears after approval, return to the writing gate before changing the structure.
16. Before delivery, run paged `writing-coverage` review. Every confirmed decision must map to final text or be explicitly rejected, superseded, or not applicable with a reason. Pending, missing, conflicted, or unlocated items block delivery.

## Source Inspiration Rules

- Runtime uploaded files are private session sources. They are not application materials, do not mark checklist items complete, and must not be committed to the public repository.
- Treat writing assignments, slides, notes, readings, and coursework as inspiration or knowledge evidence until the user confirms ownership and relevance.
- Distinguish `the user did this` from `the user read, studied, or is interested in this`.
- Express passion only as source-backed curiosity, a specific question, a method the user wants to learn, or a confirmed experience. Do not write empty passion claims.
- Do not use an unconfirmed file-derived insight to resolve an evidence gap, justify a personal achievement, or draft a factual applicant claim.

## Writing-Voice Memory Rules

- Treat uploaded writing samples as style evidence, not as a source of personal facts unless the user explicitly asks.
- Store only derived style rules unless the user asks to preserve a specific phrase.
- Separate `preserve` rules from `revise` rules.
- Mark sample-derived rules as provisional until the user confirms them.
- When revising a draft, preserve the user's evidence and intellectual ownership while improving structure, specificity, logic, and discipline fit.

## Revision Decision Categories

The ledger must distinguish:

- preserve, delete, condense, add, or rewrite;
- central argument versus supporting example;
- the argumentative function of every experience or source;
- fact-check-only material versus content permitted in the final prose;
- voice, tone, factual boundaries, and capabilities that must not be exaggerated;
- shared narrative across documents versus programme-specific emphasis;
- length, format, output destination, and overwrite decisions.

The Skill owns this application-writing interaction independently. It does not call Coursework Killer or delegate application facts to it.

## Quality Rules

- Do not invent achievements, publications, internships, awards, hardship, conversations, research experience, or readings.
- Preserve the student's voice and evidence.
- Keep school-specific customization substantive enough that swapping the school name would break the paragraph.
- Treat programme facts as verified only when backed by available, fresh official source URLs for the current application cycle.
- Empty, placeholder, link-only, partial, unverified, or unconfirmed applicant evidence cannot resolve a writing gap. A complete user confirmation may support the applicant's own writing fact, but never verifies a mutable programme requirement or completes a submission item.
- Default to English. Use another output language only when the user explicitly requests it.
