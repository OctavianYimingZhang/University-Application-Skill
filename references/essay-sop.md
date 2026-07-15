# Essay and SOP Workflow

Do not draft claims before collecting evidence. Admissions writing must be truthful, specific, and tied to the target program.

## Evidence Collection

Collect:

- Academic timeline and turning points.
- Courses, grades, projects, papers, labs, fieldwork, clinical exposure, studio work, or technical artifacts.
- Research questions, methods, tools, datasets, instruments, protocols, or theory learned.
- Internships, jobs, volunteering, leadership, entrepreneurship, competitions, teaching, or service.
- Skills with proof: programming languages, lab techniques, statistics, writing, design, languages, clinical or professional skills.
- Failures, weak grades, gaps, or changes of direction that require explanation.
- Career or research goal and why the program is necessary for it.
- Personal context only when it is relevant, true, and appropriate for the prompt.

Reject unsupported claims such as "passionate", "excellent leadership", or "strong research ability" unless the student provides evidence.

## Source Inspiration Intake

Runtime uploads can include writing assignments, lecture slides, coursework, reading notes, spreadsheets, HTML pages, JSON notes, or images with manual annotations. Use them to extract:

- interest signals: questions, problems, concepts, modules, or readings the user may genuinely care about;
- knowledge evidence: course content, papers, theories, cases, methods, tools, datasets, or terminology;
- possible essay angles: specific bridges between the file content, the target prompt, and the target programme;
- unsupported claims: broad statements that need proof or should be removed.

Keep these categories separate:

- `Confirmed personal evidence`: the user says they did the project, wrote the assignment, used the method, earned the result, or had the experience.
- `Learning or interest evidence`: the user read, studied, watched, or is curious about the material.
- `Style evidence`: the file shows how the user writes, but not what personal facts are true.

Only confirmed insights may enter the evidence map. Never turn a lecture slide, reading, or assignment topic into a personal achievement unless the user confirms ownership. Write `passion` as a precise, source-backed curiosity or question, not as a generic feeling.

## Revision Decision Ledger

Before planning a new draft or revising an existing one, atomize every historical instruction into a `RevisionDecisionLedger` stored under `revision_decision_ledger`. Accept `writing_revision_items` only as a legacy input alias. Each item records:

- stable decision ID and every conversation, file, comment, or draft locator that supports it;
- target document, section, paragraph, experience, source, or phrase;
- action: preserve, delete, condense, add, or rewrite;
- whether the content is a central argument or an example, and the exact function of the experience or material;
- whether a source is fact-check-only or may contribute content to the final prose;
- voice, tone, factual boundaries, and capabilities that must not be exaggerated;
- shared narrative across applications or programme-specific variation;
- length, format, output destination, and overwrite decision;
- conflicts, supersession links, user confirmation, implementation locations, and final coverage state.

Merge only instructions that are exact duplicates and preserve all their locators. Keep conflicting instructions separate and ask the user to confirm, adjust, reject, or replace each one. Do not use chronology as an automatic tie-breaker.

Use `scripts/build_review_questions.py --stage writing-revision` until every item is resolved. Pass every ID from `continuation.next_reviewed_question_ids` back with repeated `--reviewed-question-id` arguments so normalization or setup updates cannot skip a decision; positional `--batch-start` remains a compatibility fallback only for an unchanged question set. After drafting, use the same stable cursor with `--stage writing-coverage` until each confirmed item maps to final text or an explicitly confirmed rejected, superseded, or not-applicable outcome. `pending`, `missing`, `conflicted`, or unlocated items block delivery.

## Tutor Mode for Academic Interests

When the student names an interest, help them understand it deeply enough to write with precision:

- Define the process or concept using reliable academic sources.
- Break it into mechanisms, components, methods, debates, and applications.
- Ask what part the student actually cares about.
- Connect the interest to coursework, projects, papers, labs, or program modules.
- Explain adjacent subfields and methods the student may not know.

For example, if the student says "transcription regulation", explore promoter/enhancer logic, transcription factors, chromatin accessibility, epigenetic marks, RNA polymerase recruitment, regulatory networks, assay methods, model systems, and disease or development links, using peer-reviewed or textbook evidence where needed.

## Drafting Structure

Build:

- One core narrative: background, academic interest, evidence, goal, and why graduate or undergraduate study is the correct next step.
- One program-specific paragraph per target program: supervisor research and representative publications, research-area fit, modules, research groups, facilities, teaching or thesis structure, capstone, placement, accreditation, or faculty fit verified from official sources.
- One constraints paragraph only when needed: grade issue, field switch, gap, or unusual background.
- Supplemental essays by prompt, not by generic reuse.

## Quality Rules

- Never invent achievements, readings, lab experience, publications, internships, awards, hardships, or conversations.
- Use official program facts only after verification.
- Do not overstate certainty about career outcomes.
- Keep school-specific customization substantial enough that swapping the school name would not preserve the paragraph.
- Preserve the student's voice and evidence. Improve structure, specificity, and logic.
- For multiple applications, preserve the explicitly confirmed shared narrative and evidence while making each programme's prompt response, supervisor/course fit, and emphasis genuinely distinct.

## Output Options

Depending on the user's request, produce:

- Evidence inventory.
- Source inspiration map.
- Essay outline.
- Core SOP draft.
- School-specific adaptation map.
- Prompt-by-prompt supplemental essay plan.
- Revision comments.
- Final version with an evidence check table.
