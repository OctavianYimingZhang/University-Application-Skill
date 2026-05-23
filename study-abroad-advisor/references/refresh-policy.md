# Refresh Policy

Admissions facts change. Refresh is not a silent overwrite; it is a controlled pipeline step.

## Refresh Flow

```text
SourceEvidence
-> fetch official source
-> SourceSnapshot(current)
-> ExtractedFact(current)
-> compare with previous ExtractedFact
-> FactVersion
-> affected ApplicationCase
-> RiskFlag / Task
```

## Rules

- Do not silently update final advice when an official source changes.
- Create `FactVersion` for new, changed, removed, or unchanged facts.
- Mark affected `ApplicationCase` objects for re-verification.
- Create `RiskFlag` when a changed fact affects active requirements, deadlines, fees, visa rules, or essay claims.
- Create `Task` when the source is unavailable, contradictory, or no longer official.

## Staleness Defaults

- deadline: 7 days
- application fee: 14 days
- visa or immigration rule: 7 days
- language requirement: 30 days
- document rule: 30 days
- curriculum or module: 90 days
- essay prompt: 14 days during active cycle

Use official cycle dates when they are available; otherwise use these as conservative operational defaults.
