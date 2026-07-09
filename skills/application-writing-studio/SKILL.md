---
name: application-writing-studio
description: Interactive admissions writing planning workflow for SOPs, personal statements, programme-fit paragraphs, and supplemental essays. Use when the user wants to brainstorm, structure, evidence-check, draft, revise, or learn from uploaded writing samples and inspiration files with brief lock, source inspiration intake, evidence inventory, narrative options, programme fit, critical review, planning approval, draft gates, and writing-voice memory controls.
---

# Application Writing Studio

Use this focused Skill for admissions writing. The core job is to help the user think through the document before drafting.

## Workflow

1. Read [`../../references/essay-sop.md`](../../references/essay-sop.md), [`../../references/memory-system.md`](../../references/memory-system.md), and [`../../references/evidence-contract.md`](../../references/evidence-contract.md).
2. Lock the writing brief: programme, prompt, word limit, audience, output use, source policy, applicant background, and submission deadline if relevant.
3. Check whether the user has supplied writing-voice memory or uploaded writing samples. If not, use blank defaults and do not invent voice rules.
4. Run source inspiration intake when the user uploads writing assignments, lecture slides, coursework, readings, notes, spreadsheets, or images:
   - extract or summarize only what is present in the supplied file or manual annotation;
   - classify `Interest Signals`, `Knowledge Evidence`, `Methods / Concepts`, `Possible Essay Angles`, and `Unsupported Claims`;
   - ask the user to confirm any insight before it enters the evidence map or resolves a writing gap.
5. Build a normalized evidence inventory from the user. An item enters the evidence map only after `value`, source provenance, evidence date, explicit confirmation, verification, completeness, cycle, access date, and staleness are recorded:
   - academic projects, modules, grades, methods, readings, labs, clinical/professional exposure, internships, leadership, awards, failures, and goals.
6. Generate narrative options only from supplied and confirmed evidence.
7. Build an evidence map for the selected option.
8. Build a programme-fit paragraph plan using verified programme facts.
9. Run a critical review:
   - unsupported claims;
   - weak causal links;
   - generic programme fit;
   - tone or ownership risks;
   - mismatch with supplied writing voice;
   - missing evidence.
10. Display the structure and evidence map, then request planning approval.
11. After approval, draft directly without asking whether to start.
12. If a plan-breaking evidence gap appears after approval, return to the writing gate before changing the structure.

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

## Quality Rules

- Do not invent achievements, publications, internships, awards, hardship, conversations, research experience, or readings.
- Preserve the student's voice and evidence.
- Keep school-specific customization substantive enough that swapping the school name would break the paragraph.
- Treat programme facts as verified only when backed by official source URLs.
- Empty, placeholder, link-only, partial, unverified, or unconfirmed applicant evidence cannot resolve a writing gap.
- Default to English. Use another output language only when the user explicitly requests it.
