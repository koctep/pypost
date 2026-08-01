# PYPOST-986 — Developer Documentation

## Summary

Documented the new "Import environments" feature for both audiences:

- **End users**: added an "Import environments" section to
  `doc/user/environments.md` (between "Manage environments" and "Activate an
  environment") covering how to start an import, the accepted file shape
  (single JSON object or list, with a minimal example), the
  Overwrite / Keep Both / Skip conflict prompt and its "apply to all
  remaining conflicts" shortcut, the post-import summary dialog, and the
  Hidden/encryption and invalid-file guarantees from the requirements' DoD
  and Non-Functional Requirements.
- **Developers**: added an "Import environments (PYPOST-986)" section to the
  existing `doc/dev/environments_dialog.md` (the dev doc that already covers
  `EnvironmentDialog`/`EnvironmentListWidget`/`EnvironmentVariablesWidget\`),
  describing the pure `pypost/core/environment_import.py` module's public
  surface, the `EnvironmentListWidget.import_environments()` orchestration,
  the identity-preserving Overwrite decision and why it matters for the
  encryption-envelope reuse cache, and the relevant test files. This keeps
  the single existing dev doc for the environments dialog area complete
  rather than splitting import into a separate file.

## Components

| Doc | Audience | What it covers |
| --- | --- | --- |
| `doc/user/environments.md` § Import environments | End user | How to trigger import, file shape, conflict choices, success/error feedback |
| `doc/dev/environments_dialog.md` § Import environments (PYPOST-986) | Developer | `environment_import.py` API, orchestration, identity/encryption interaction, tests |

No new `doc/dev/*.md` file was created: the existing `environments_dialog.md`
already documents `EnvironmentDialog` and its child widgets end-to-end, and
`EnvironmentListWidget` (where `import_environments()` lives) is one of those
child widgets — adding a section there keeps the developer-facing
documentation for "the environments dialog area" in one place, consistent
with how PYPOST-449/PYPOST-496 (prior changes to the same widget family)
extended this same file rather than creating new ones.

## Related

- `ai-tasks/PYPOST-986/10-requirements.md` — DoD item requiring
  `doc/user/environments.md` to document import, the file format, and the
  conflict policy.
- `ai-tasks/PYPOST-986/20-architecture.md` — full design, interfaces, and
  Q&A that this documentation summarizes for a reader who does not need the
  full architecture doc.
- `ai-tasks/PYPOST-986/60-tech-debt.md` — no doc-related follow-ups; the two
  Code Quality Issues corrected during the Phase C blocker review (stale
  hardcoded-filter-string claim) do not affect this step.
