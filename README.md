# University Application Skill

[University Application Skill](https://github.com/OctavianYimingZhang/University-Application-Skill) is an evidence-first, multiple-Skill Plugin for planning international university applications. It turns an applicant request into a source-backed application case without inventing applicant facts, promoting catalogue placeholders into verified requirements, or estimating admission probability.

`university-application-index` is the canonical router. `study-abroad-advisor` remains a thin compatibility alias; all substantive routing is owned by the canonical index and the focused Skills below.

## Why this Plugin exists

An application is ready only when four things are separately true:

1. The exact programme and application cycle are identified.
2. Current requirements are verified from official sources.
3. Applicant evidence is substantive, dated, sourced, complete, and explicitly confirmed.
4. Every writing, document, deadline, cost, visa, and submission decision is traceable to that verified state.

The Plugin therefore follows this first-principles workflow:

```text
request -> route review -> programme identity -> official-source verification
        -> confirmed applicant evidence -> requirements and materials gaps
        -> deadlines/costs -> writing brief and plan approval
        -> visa readiness -> submission QA
```

Missing information remains a gap. A link, placeholder, inferred profile detail, or unconfirmed extraction never becomes verified evidence merely because it is present.

## Router and focused Skills

| Skill | Responsibility |
| --- | --- |
| `university-application-index` | Canonical router, intake, route review, memory selection, and cross-route coordination. |
| `study-abroad-advisor` | Compatibility alias that delegates to the canonical router. |
| `program-research` | Discover and compare programmes using curated identities and current official pages. |
| `requirement-audit` | Verify academic, language, subject, document, fee, and deadline requirements. |
| `materials-check` | Compare source-backed requirements with explicitly confirmed applicant evidence. |
| `application-writing-studio` | Lock the writing brief, build the evidence inventory, plan narrative structure, and draft only after approval. |
| `submission-readiness` | Run final cycle, document, evidence, deadline, and submission-blocker checks. |
| `visa-readiness` | Review administrative student-visa preparation from official government sources, without legal advice. |
| `programme-table-cleaning` | Maintain official programme tables and workbooks with preserved lineage. |

Use [`SKILL.md`](SKILL.md) when the route is not already confirmed. Direct invocation of a focused Skill is supported, but its declared inputs and gates still apply.

## Versioned Plugin boundary

[`plugin-capability-manifest.v2.json`](plugin-capability-manifest.v2.json) is the executable route registry. It declares each route ID, owning Skill, semantic triggers, required inputs, gates, outputs, adapter entrypoint, and supported context versions.

The shared schemas under [`contracts/`](contracts/) are byte-identical across the independently installable Soleil Plugins:

| Contract | Purpose |
| --- | --- |
| `PluginCapabilityManifest v2` | Route ownership and executable capability metadata. |
| `AcademicTaskContext v1` | Original request, application case, source references, relevant memory, permissions, and decisions. |
| `TaskRunState v1` | One `run_id` across source readiness, route/brief lock, permissions, plan approval, execution, and QA/failure. |
| `SourceRecord v1` | Stable source identity, checksum, provenance, locators, parser version, and opaque local reference. |
| `LocalBridgeProtocol v1` | Versioned loopback handshake, session token, origin controls, consent, and request envelope. |

A recommendation remains `suggested` until the user selects it. Only `explicitly_confirmed` decisions can satisfy a user gate.

Admissions-specific structured state uses [`ApplicationCase v1`](schemas/application-case-v1.schema.json), which keeps source availability, fact verification, completeness, application cycle, access date, and staleness separate.

## Routes and gates

| Route | Required control points | Primary outputs |
| --- | --- | --- |
| `program_research` | Route confirmation; official-source verification | Programme list, application case, source log |
| `requirement_audit` | Route confirmation; official sources; confirmed applicant evidence | Requirement table, gaps, source log |
| `materials_check` | Route confirmation; confirmed applicant evidence | Materials checklist and blockers |
| `application_writing_studio` | Locked brief; confirmed evidence; planning approval | Writing plan and approved draft |
| `submission_readiness` | Route confirmation; confirmed evidence; current-cycle verification | Readiness checklist and blockers |
| `visa_readiness` | Route confirmation; official government provenance; confirmed evidence; non-legal-advice boundary | Visa-readiness notes, document gaps, source log |
| `programme_table_cleaning` | Explicit maintenance authorisation; lineage preservation | Cleaned workbook, identity catalogue, verification report |

The main agent owns Ask User, route or brief locking, applicant-evidence confirmation, permissions, and planning approval. It asks only questions that can change the plan, displays the relevant brief or route before the question batch, and does not treat a recommended answer as selected. Bounded non-interactive work may be delegated only after its dependencies are locked.

Writing Studio begins with an empty evidence inventory. Before drafting it must confirm the programme, prompt, audience, word limit, intended use, source policy, exact evidence IDs, and visible structure. A plan-breaking change returns to the writing gate instead of silently changing the approved plan.

## Programme catalogue and provenance

The Plugin-owned [`catalogues/index.json`](catalogues/index.json) lazy-loads institution files under [`catalogues/institutions/`](catalogues/institutions/). The current index contains 43 institutions and 13,986 stable programme identities.

Catalogue scope is deliberately narrow:

- `identity_status` is `official_source_listed`;
- `requirements_status` is `not_collected`;
- official HTTPS identity URLs, stable IDs, source notes, and update metadata are retained;
- requirements, deadlines, fees, availability, applicant fit, and visa rules must still be verified live;
- placeholders, illustrative rows, and link-only records cannot pass as verified facts.

For custom cases, start from an official programme URL and build a new `ApplicationCase`; do not infer the programme identity from marketing summaries or aggregators.

Hard requirements should come from official university, government, testing-agency, or scholarship sources. Record the source URL and access date, preserve uncertainty, and fail explicitly when TLS certificate verification or source retrieval fails.

## Private Soleil Admissions Site

The owner-only [Soleil Admissions Site](https://soleil-admissions.ready-loach-3659.chatgpt.site) is the private structured workspace for:

```text
Profile -> Programme Discovery -> Compare -> Cases -> Evidence
        -> Deadlines/Costs -> Writing Studio -> Visa Readiness -> Submission QA
```

The Site and Plugin share `ApplicationCase v1` and the Soleil contracts. The Site stores confirmed structured cases, tasks, facts, approvals, revisions, and freshness metadata in D1. Sensitive originals, raw uploads, full extracted text, and local execution stay on the owner's machine. The Site is an access-controlled companion, not a public replacement for the independently installable Plugin.

## Privacy and data boundary

The public repository contains blank schemas, blank memory templates, generic examples, programme identities, and executable workflow code. It must not contain populated applicant memory, real writing samples, transcripts, credentials, visa identifiers, or invented applicant evidence.

Recommended private memory path:

```text
memory/local-user-memory.json
```

That path is ignored by Git. Retrieve only the smallest relevant memory pack for a task, and use confirmed course or writing evidence across systems only when the user requests it. `SourceRecord v1` carries an opaque local reference and locators; it does not carry raw document bytes or full extracted text.

## Output language

All shipped UI copy, prompts, plans, questions, errors, metadata, tests, documentation, and generated output default to English. The router may understand a request written in another language, but the output remains English unless the user explicitly requests a task-level language override.

## Installation

Clone the repository, then synchronise the canonical router and focused sibling Skills into `~/.codex/skills`:

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

The synchroniser installs `university-application-index` plus the focused Skills while preserving their required shared references, contracts, schemas, scripts, and catalogue resources.

## Example invocations

```text
$university-application-index
Build a source-backed shortlist for postgraduate neuroscience programmes and show every unresolved profile decision before planning.
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

Run the Plugin checks from the repository root:

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
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" .
```

Workbook smoke test:

```bash
python3 scripts/build_admissions_workbook.py \
  tests/fixtures/admissions_case_mvp.json \
  /tmp/application_plan.xlsx
```

## Repository map

| Path | Responsibility |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Canonical router and first-principles workflow. |
| [`skills/`](skills/) | Router wrapper, compatibility alias, and focused Skills. |
| [`plugin-capability-manifest.v2.json`](plugin-capability-manifest.v2.json) | Versioned route and gate registry. |
| [`contracts/`](contracts/) | Shared Soleil interoperability schemas. |
| [`schemas/`](schemas/) | Admissions-specific `ApplicationCase` schema. |
| [`catalogues/`](catalogues/) | Curated, identity-only programme catalogue and schemas. |
| [`references/`](references/) | Evidence, research, writing, memory, governance, refresh, and submission protocols. |
| [`scripts/`](scripts/) | Planning, Ask User payloads, validation, catalogue maintenance, workbook rendering, and local installation. |
| [`memory/`](memory/) | Blank public memory scaffold only. |
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) | Plugin metadata and Codex interface declaration. |

## Security principles

- Never invent applicant facts, requirements, deadlines, fees, scholarships, visa rules, or outcomes.
- Never produce chance scores or safe/match/reach admission labels.
- Use official provenance for mutable hard requirements and government provenance for visa-readiness claims.
- Keep retrieval certificate verification enabled and expose failures as failures.
- Keep raw sources and sensitive applicant files local.
- Require explicit consent before any local bridge data transfer.
- Accept bridge traffic only through the versioned loopback protocol with a random session token, strict origin allowlist, and rate limiting.
- Invalidate writing or submission approvals when the underlying case or evidence revision changes.

## Licence

MIT. See [`LICENSE`](LICENSE).
