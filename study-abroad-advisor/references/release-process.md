# Release Process

Rule bundles should be treated as versioned release artifacts.

## Why

Country and application-system rules change. A route bundle should not be treated as permanent static text.

## Release Metadata

Each released rule bundle should record:

- bundle ID
- jurisdiction
- valid cycle or intake
- source evidence IDs
- reviewer
- released timestamp
- deprecated timestamp if applicable
- breaking changes
- affected route families

Example:

```yaml
rule_bundle_release:
  bundle_id: uk_2026_cycle_v1
  jurisdiction: uk
  valid_for_cycle: "2026"
  source_evidence_ids: []
  reviewed_by: advisor
  released_at: ""
  deprecated_at: ""
  breaking_changes:
    - ATAS check logic changed
    - financial evidence threshold source changed
```

## Rules

- Do not hardcode current money thresholds, fee amounts, exact dates, or country lists unless live official evidence was checked during the task.
- If a bundle changes, create `FactVersion` and affected-case `RiskFlag` objects.
- Do not use deprecated bundles for final recommendations.
