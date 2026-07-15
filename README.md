# University Application Skill

University Application Skill is an evidence-first Codex Plugin for international admissions research, application planning, writing, visa preparation, and submission quality assurance. It is a multiple-Skill system: one canonical router coordinates focused Skills while versioned contracts keep every route independently testable and interoperable with the wider Soleil system.

The Plugin never fills gaps with plausible applicant facts, treats catalogue identities as verified requirements, or predicts admission probability. Missing information stays visible until it is supported by a source and explicitly confirmed.

## What it does

The workflow follows the actual dependency order of a defensible application:

```text
request -> matched / needs confirmation / out of scope
        -> programme identity and exact degree type -> official-source verification
        -> requirements, supervisor/programme fit, and applicant evidence
        -> materials and deadlines -> writing ledger and plan approval
        -> writing coverage -> visa readiness -> submission QA
```

Core capabilities include:

- source-backed programme discovery with exact research-degree filtering and supervisor/programme-fit review;
- exact academic, language, application-field, writing-prompt, AI-policy, fee, deadline, document, and pre-application requirement audits;
- evidence-gated application materials checks;
- independent personal-statement and statement-of-purpose planning with an empty-by-default evidence inventory and complete revision-decision coverage;
- administrative visa-readiness review from official government sources, with a non-legal-advice boundary;
- final application-cycle and submission checks;
- explicit maintenance of curated programme catalogues and admissions workbooks.

All shipped prompts, plans, questions, errors, tests, metadata, documentation, and generated outputs default to English. The router can understand requests in other languages, but changes output language only when the user explicitly requests a task-level override.

## Multiple-Skill architecture

[`university-application-index`](SKILL.md) owns intake, route review, memory selection, Ask User gates, and cross-route coordination. `study-abroad-advisor` is retained only as a thin compatibility alias.

| Skill | Responsibility |
| --- | --- |
| `university-application-index` | Canonical routing, task context, user decisions, and workflow coordination. |
| `program-research` | Discover exact degree types and compare programmes, supervisors, research, publications, structure, and modules using current official sources. |
| `requirement-audit` | Verify programme, document, prompt, policy, deadline, and pre-application requirements and compare them with confirmed evidence. |
| `materials-check` | Identify document, evidence, and readiness gaps. |
| `application-writing-studio` | Independently lock the brief, resolve every revision decision, map evidence, approve the plan, draft, and audit coverage. |
| `submission-readiness` | Run final cycle, evidence, document, deadline, and blocker checks. |
| `visa-readiness` | Review administrative visa preparation using official government provenance. |
| `programme-table-cleaning` | Maintain programme tables, workbooks, catalogue lineage, and validation reports. |
| `study-abroad-advisor` | Delegate legacy invocations to the canonical router. |

Direct invocation of a focused Skill is supported. Its declared inputs, permissions, and gates still apply.

## Evidence and control model

Applicant evidence can satisfy a gate only when it has all of the following:

- a non-empty evidence value;
- a source;
- an evidence date;
- an explicit user confirmation;
- separate availability, verification, completeness, application-cycle, access-date, and staleness states.

Links, placeholders, partial extracts, inferred profile details, and suggested answers remain unconfirmed. The main agent owns route or brief locking, applicant-evidence confirmation, permissions, and planning approval. A recommendation remains `suggested` until the user selects it.

Evidence provenance is purpose-specific. Mutable official facts require `public_url`; applicant writing facts may use a confirmed `local_document` or `user_confirmation`; materials and submission may use local-document evidence but cannot pass from user confirmation alone.

Writing Studio begins with no applicant evidence. It locks the programme, prompt, audience, limit, intended use, source policy, evidence IDs, output and overwrite decisions, and visible structure before drafting. Its admissions-specific `RevisionDecisionLedger` preserves every instruction, conflict, source locator, multi-document invariant, programme-specific variation, implementation location, and coverage result. A plan-breaking change returns to the approval gate.

## Versioned contracts

[`plugin-capability-manifest.v2.json`](plugin-capability-manifest.v2.json) is the executable route registry. Each route declares its owning Skill, semantic triggers, required inputs, gates, outputs, adapter entrypoint, and supported context versions.

The schemas in [`contracts/`](contracts/) are shared with the independently installable Soleil Plugins:

| Contract | Purpose |
| --- | --- |
| `PluginCapabilityManifest v2` | Route ownership and executable capability metadata. |
| `AcademicTaskContext v1` | Original request, application case, sources, memory, permissions, and decisions. |
| `TaskRunState v1` | One `run_id` from source readiness through QA or failure. |
| `SourceRecord v1` | Stable source identity, checksum, provenance, locators, parser version, and opaque local reference. |
| `LocalBridgeProtocol v1` | Authenticated loopback handshake, origin control, consent, and request envelopes. |

Admissions state uses [`ApplicationCase v1`](schemas/application-case-v1.schema.json). Version 1 remains backward compatible while optionally recording requirements, documents, deadlines, supervisor/programme fit, writing tasks, risks, actions, source log, lifecycle state, and per-workstream readiness.

The Plugin release version is `0.5.0`; public route IDs and shared Soleil contract versions remain unchanged.

## Programme catalogue

The Plugin owns an identity-only catalogue under [`catalogues/`](catalogues/). [`catalogues/index.json`](catalogues/index.json) lazy-loads 43 institution files containing 13,986 stable programme identities.

Every normal catalogue record preserves an official HTTPS URL, provenance, access metadata, and these deliberately narrow states:

```text
identity_status: official_source_listed
requirements_status: not_collected
```

Catalogue inclusion does not verify entry requirements, deadlines, fees, availability, applicant fit, or visa rules. Those facts must be retrieved from current official sources. Custom cases start from an official programme URL and use the same `ApplicationCase` contract.

## Private Site boundary

[Soleil Admissions](https://soleil-admissions.ready-loach-3659.chatgpt.site) is the separate, owner-only structured workspace for:

```text
Profile -> Programme Discovery -> Compare -> Cases -> Evidence
        -> Deadlines/Costs -> Writing Studio -> Visa Readiness -> Submission QA
```

The Site stores confirmed structured cases, tasks, facts, approvals, and freshness metadata in D1. Sensitive originals, raw uploads, full extracted text, and local execution stay on the owner's machine. This repository intentionally contains Plugin code only: it does not ship the Site source, a public-site deployment workflow, or a browser authentication bridge.

## Private memory and local extraction

The public package contains blank schemas and [`memory/blank-memory.json`](memory/blank-memory.json), never populated applicant memory. A recommended private path is:

```text
memory/local-user-memory.json
```

That path is ignored by Git. Keep full local memory outside public history and retrieve only the smallest relevant pack for a task.

[`scripts/extract_inspiration_file.py`](scripts/extract_inspiration_file.py) provides local, runtime-only extraction for writing inspiration. It accepts a JSON request on standard input with base64 file bytes and emits structured blocks plus warnings. PDF, DOCX, PPTX, XLSX, text, Markdown, CSV, TSV, HTML, and JSON extraction is supported when the corresponding optional Python libraries are installed. Images are registered locally for manual review; the script does not upload source bytes or silently promote extracted text into confirmed evidence.

## Installation

Clone the repository and synchronise the canonical router plus focused sibling Skills into `~/.codex/skills`:

```bash
git clone https://github.com/OctavianYimingZhang/University-Application-Skill.git
cd University-Application-Skill
python3 scripts/publish_skill.py --sync-local-skill
```

After an update:

```bash
git pull --ff-only
python3 scripts/publish_skill.py --sync-local-skill
```

The synchroniser preserves the shared references, contracts, schemas, scripts, and catalogue resources needed by each installed Skill.

## Example invocations

```text
$university-application-index
Build a source-backed shortlist for postgraduate neuroscience programmes and show unresolved profile decisions before planning.
```

```text
$requirement-audit
Audit this official programme URL against my explicitly confirmed academic and language evidence.
```

```text
$application-writing-studio
Lock the brief and evidence inventory for this personal statement, then show the structure for Planning Approval before drafting.
```

```text
$visa-readiness
Review my administrative student-visa readiness using current official government guidance. Do not provide legal advice.
```

## Validation

Run the complete Plugin validation inventory from the repository root:

```bash
python3 -m compileall -q scripts
python3 scripts/validate_catalogues.py
python3 -m unittest tests.test_catalogues -v
python3 scripts/check_setup_contract.py
python3 scripts/validate_skill_contracts.py
python3 scripts/plan_workflow.py --self-test
python3 scripts/build_review_questions.py --self-test
python3 scripts/validate_evidence.py --self-test
python3 scripts/publish_skill.py --self-test
python3 scripts/publish_skill.py --dry-run --sync-local-skill
python3 scripts/build_admissions_workbook.py \
  tests/fixtures/admissions_case_mvp.json \
  /tmp/application_plan.xlsx
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" .
git diff --check
```

The contract validator also rejects any return of the retired public web directory, Pages workflow, or browser authentication bridge.

## Repository map

| Path | Responsibility |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Canonical routing and workflow contract. |
| [`skills/`](skills/) | Focused Skills and the compatibility alias. |
| [`plugin-capability-manifest.v2.json`](plugin-capability-manifest.v2.json) | Versioned route and gate registry. |
| [`contracts/`](contracts/) | Shared Soleil interoperability schemas. |
| [`schemas/`](schemas/) | Admissions-specific structured-state schemas. |
| [`catalogues/`](catalogues/) | Curated programme identities, provenance, and catalogue schemas. |
| [`references/`](references/) | Evidence, research, writing, memory, governance, refresh, and submission protocols. |
| [`scripts/`](scripts/) | Planning, Ask User payloads, validators, extraction, catalogue maintenance, workbooks, and local installation. |
| [`memory/`](memory/) | Blank public memory scaffold only. |
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) | Plugin metadata and Codex interface declaration. |

## Security principles

- Use official provenance for mutable requirements and government provenance for visa-readiness claims.
- Keep TLS certificate verification enabled and surface retrieval failures explicitly.
- Keep raw sources, sensitive applicant files, and full extracts local.
- Require explicit consent before any local data transfer.
- Accept bridge traffic only through the versioned loopback protocol with a random session token, strict origin allowlists, and rate limiting.
- Never invent applicant facts, requirements, deadlines, fees, scholarships, visa rules, or outcomes.
- Never produce chance scores or safe/match/reach labels.
- Invalidate writing or submission approvals when their underlying case or evidence revision changes.

## Licence

MIT. See [`LICENSE`](LICENSE).
