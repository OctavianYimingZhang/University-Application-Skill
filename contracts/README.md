# Soleil Interoperability Contracts

These JSON Schemas are the versioned boundary between the four independently installable Soleil Plugins and the private ChatGPT Sites.

- `PluginCapabilityManifest v2` declares route ownership, inputs, gates, outputs, adapters, and supported context versions.
- `AcademicTaskContext v1` carries the original request, course or case, source references, relevant memory, permissions, and user decisions.
- `TaskRunState v1` preserves one `run_id` from source readiness through QA or failure.
- `SourceRecord v1` describes a locally held source without embedding its raw bytes or full extracted text.
- `LocalBridgeProtocol v1` defines the loopback handshake and authenticated request envelopes.

All shipped output defaults to English. A task-level language override is valid only when the user explicitly requests it. Recommended decisions remain `suggested` until the user selects them.

The schema files in each Plugin are intentionally byte-identical. Plugin-specific route declarations live in `plugin-capability-manifest.v2.json`.
