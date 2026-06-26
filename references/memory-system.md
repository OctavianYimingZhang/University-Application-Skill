# Memory System Contract

This package ships with memory schemas, blank templates, and UI helpers only. Repository files must not contain populated user memory, private applicant facts, private writing samples, transcript details, lecture notes from a named user, or account credentials.

## Purpose

The default ChatGPT/Codex memory surface is too small for serious university-admissions and exam-preparation work. This Skill therefore treats memory as a structured local knowledge base that can be summarized into smaller AI memory systems when needed.

The memory layer is designed to remember, after the user explicitly supplies or imports the information:

- what a teacher covered in class;
- what was on the slides;
- what was said in class but was not present on the slides;
- which examples, derivations, caveats, or exam hints were emphasized verbally;
- how the user writes;
- how the user prefers notes, bilingual explanations, exam answers, citations, tables, and revision plans;
- previous feedback, corrections, and accepted output styles.

## Blank-by-default rule

The public GitHub version must remain blank. It may include:

- schemas;
- blank JSON templates;
- empty arrays and empty strings;
- generic placeholder keys;
- documentation explaining how to fill memory locally.

It must not include:

- a real user profile;
- real writing samples;
- real supervisor names, grades, emails, visa data, application plans, or institution-specific personal choices;
- extracted lecture notes from a private course unless the user intentionally commits them to their own private fork.

## Multi-memory architecture

Use these layers together rather than relying on one context window.

| Layer | Storage | Function | Size policy |
| --- | --- | --- | --- |
| Runtime context | Current chat/Codex session | Active task reasoning | Ephemeral |
| Skill package | `SKILL.md`, `skills/`, `references/` | Generic workflow rules | Public, blank |
| Local canonical memory | `memory/local-user-memory.json` or user-chosen private path | Full structured memory | Private, large |
| Browser memory draft | Memory Studio export/localStorage | User-edited import/export buffer | Private to browser |
| ChatGPT memory | User-controlled ChatGPT memory | Stable compact preferences only | Small summary |
| Codex memory | Local repo files, AGENTS/Skill notes, or user setup JSON | Project-specific operating memory | Chunked |
| External notes vault | Obsidian/Drive/local markdown, if connected by user | Long source archive | Indexed by source |

The local canonical memory is the preferred source of truth. ChatGPT memory and Codex memory should store compact summaries or pointers, not the whole archive.

## Memory categories

### 1. Course memory

Stores course/module identity, lecture sequence, topic coverage, formulas, methods, examples, assessed skills, and known weak points.

Suggested fields:

```json
{
  "course_id": "",
  "course_title": "",
  "institution": "",
  "lectures": []
}
```

### 2. Slide-delta memory

Stores the difference between slides and live teaching.

Use this whenever a user says a lecturer emphasized something, added an example verbally, skipped a slide, corrected the slides, or said a detail is examinable.

Suggested fields:

```json
{
  "lecture_id": "",
  "slide_reference": "",
  "slide_content_summary": "",
  "teacher_spoken_addition": "",
  "not_on_slides": true,
  "exam_relevance": "unknown",
  "evidence_source": "user_uploaded_notes_or_user_statement",
  "confidence": "user_supplied"
}
```

### 3. Writing-voice memory

Stores writing style only when the user uploads or pastes their own writing. Do not infer personal facts from writing samples unless the user asks.

Store:

- sentence length tendency;
- paragraph density;
- citation style;
- first-person preference;
- preferred register;
- common phrasing to preserve;
- common problems to correct;
- discipline-specific conventions.

### 4. Notes-preference memory

Stores output preferences such as bilingual layout, paragraph-vs-sentence translation, exam-ready density, table use, formula formatting, or whether examples should be included.

### 5. Evidence memory

Stores source-backed facts used in applications or exam prep. Every factual claim should have a source, date, and status.

### 6. Conflict memory

Stores contradictions between memory systems. Resolve conflicts by this priority:

1. latest explicit user correction;
2. user-uploaded source file;
3. official source for requirements/deadlines/fees;
4. canonical local memory;
5. compact ChatGPT/Codex summary.

Never silently merge conflicting facts.

## Retrieval protocol

Before answering a complex request:

1. Identify the task route.
2. Load only memory categories relevant to the route.
3. Retrieve the smallest useful set of entries.
4. Prefer entries with source, timestamp, and user confirmation.
5. Surface uncertainty if memory is missing, stale, or contradictory.
6. After the answer, update memory only when the user asks or when the user has provided durable preferences that should affect future outputs.

## Memory distillation protocol

Large memory should be compressed into task-specific packs:

- `course_pack`: module map, high-frequency exam topics, lecture-slide deltas, formulas, common mistakes;
- `writing_pack`: voice rules, revision rules, sample-derived style constraints;
- `application_pack`: applicant profile, target programmes, hard requirements, documents, deadlines, source log;
- `notes_pack`: formatting preferences, bilingual mode, density, diagram requirements.

A pack should be short enough to paste into ChatGPT/Codex, while the full canonical memory remains outside the context window.

## Update protocol

Each memory update should record:

- category;
- title;
- content;
- source type;
- source label;
- confidence;
- created/updated timestamp;
- whether it is user-confirmed;
- whether it can be exported to ChatGPT/Codex compact memory.

## Website Memory Studio

The static Memory Studio page lives at `web/public/memory.html`. It runs in the browser and can:

- accept uploaded writing samples;
- infer a provisional writing-voice profile;
- allow manual lecture/slide-delta memory entries;
- export a blank-compatible JSON memory file;
- export a compact Markdown memory pack for ChatGPT/Codex.

The page does not authenticate to Codex or GitHub and does not write to the repository. The user must explicitly download or copy the result.
