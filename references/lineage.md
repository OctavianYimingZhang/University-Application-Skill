# Lineage

Lineage proves where recommendations, checklist rows, workbook cells, essay claims, and risk flags came from.

## Required Paths

Requirement lineage:

```text
SourceSnapshot -> ExtractedFact -> RequirementRule -> ApplicationCase -> WorkbookCell
```

Risk lineage:

```text
SourceEvidence / ExtractedFact -> RequirementRule / Deadline -> RiskFlag -> Task
```

Essay lineage:

```text
StudentEvidence + ProgramFitFact + SourceEvidence -> EssayClaim -> SOP paragraph
```

Refresh lineage:

```text
SourceSnapshot(previous) + SourceSnapshot(current) -> FactVersion -> affected ApplicationCase -> RiskFlag
```

## Rules

- Every verified requirement must trace to `SourceEvidence`.
- Every program-specific essay claim must trace to `ProgramFitFact`.
- Every student-specific achievement claim must trace to `StudentEvidence`.
- Every workbook row that claims a fact should expose backing IDs when possible.
- Orphan objects should be treated as quality warnings or errors depending on severity.

The machine-readable expectations live in `ontology/lineage_rules.yaml`.
