# Memory Templates

This directory is intentionally blank-by-default.

The repository may contain only public-safe templates such as `blank-memory.json`. Do not commit populated user memory, private writing samples, lecture notes, application data, visa details, credentials, or local exports.

Recommended private files, ignored by `.gitignore`:

- `memory/local-user-memory.json`
- `memory/private-user-memory.json`
- `memory/<project>.local.json`

Use `blank-memory.json` as the starting point, then keep the filled version outside public Git history unless the user deliberately chooses a private fork or private repository.

For local setup, copy `blank-memory.json` to an ignored path such as `memory/local-user-memory.json`. `scripts/extract_inspiration_file.py` can create provisional labelled blocks from runtime source files, but it does not modify memory or confirm evidence. Review every extracted fact before adding it to private memory.

The owner-only [Soleil Admissions Site](https://soleil-admissions.ready-loach-3659.chatgpt.site) stores confirmed structured cases, tasks, facts, approvals, and freshness metadata separately from this Plugin repository. Keep raw files, full extracts, private writing samples, and local execution on the owner's machine.
