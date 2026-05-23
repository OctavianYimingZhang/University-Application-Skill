# Data Lifecycle

Use this lifecycle for official-source research, requirement extraction, essay evidence, workbook rendering, and refresh work.

## Layers

| Layer | Meaning | Objects |
| --- | --- | --- |
| Bronze | Raw official source snapshots. | `SourceSnapshot` |
| Silver | Candidate facts extracted from source snapshots. | `ExtractedFact` |
| Gold | Verified facts used for application decisions. | `RequirementRule`, `Deadline`, `ProgramFitFact`, `RiskFlag`, `Task` |
| Platinum | User-facing rendered outputs. | workbook sheets, shortlist, essay plan, submission checklist |

## Rules

- Do not create final recommendations directly from raw pages.
- Capture official page metadata as `SourceSnapshot` when performing refresh, diff, or audit work.
- Convert source text into `ExtractedFact` before promoting it to verified rules or program-fit facts.
- Promote facts to Gold only when official source evidence, checked date, source type, and verification status are present.
- Render Platinum views only from ontology objects.
- If a source changes, create `FactVersion`, identify affected `ApplicationCase` objects, create `RiskFlag`, and require re-verification.

## Typical Flow

```text
official program page
-> SourceSnapshot
-> ExtractedFact(deadline / fee / language score / module)
-> RequirementRule or ProgramFitFact
-> ApplicationCase, Task, RiskFlag
-> Workbook row, SOP claim, or checklist item
```

## Freshness Defaults

Use official evidence checked during the task. If no institution-specific freshness policy exists, use these conservative defaults:

- deadline: 7 days
- application fee: 14 days
- visa or immigration rule: 7 days
- language requirement: 30 days
- document rule: 30 days
- curriculum or module: 90 days
- ranking: until the ranking cycle changes
- essay prompt: 14 days during an active cycle

These are workflow defaults, not claims about any country's policy.
