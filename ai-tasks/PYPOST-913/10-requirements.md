# PYPOST-913: Rename diagnostics session_fixture → session_source

## Goals

Clarify agent e2e failure artifact diagnostics by renaming the provenance field
from `session_fixture` to `session_source`. The value semantics are unchanged
(fixture name or `"direct"`).

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer** inspecting `diagnostics.json`, I want a field name that
  reflects session provenance (fixture vs direct construction), not pytest
  fixture mechanics alone.
- As a **contributor** writing manual dump calls, I want the public API keyword
  to match the on-disk diagnostics key.
- As a **CI consumer** downloading failure artifacts, I want docs and tests to
  describe `session_source` consistently.

## Definition of Done

- `diagnostics.json` writes `session_source` (not `session_fixture`).
- `dump_agent_e2e_failure_artifacts` accepts `session_source=` kwarg.
- Makereport hook and direct-session dump hook pass provenance via the new name.
- Tests assert `session_source`; Step 3 red test drove the rename.
- `doc/dev/agent_e2e_failure_artifacts.md` updated.
- Steps 1–8 task artifacts exist for PYPOST-913.

## Task Description

**Problem:** The diagnostics field `session_fixture` is overloaded — it records
how the session was obtained (`agent_e2e_session`, `seeded_agent_e2e_session`, or
`direct`), not always a pytest fixture name. Source:
[PYPOST-913](https://pypost.atlassian.net/browse/PYPOST-913), from
[PYPOST-875](https://pypost.atlassian.net/browse/PYPOST-875) tech debt.

**Business need:** Reduce confusion when triaging agent e2e failure dumps.

### In Scope

- Rename diagnostics JSON key and matching Python API parameter.
- Update pytest plugin wiring, unit/subprocess tests, developer docs.
- Workflow artifacts (Steps 1–8).

### Out of Scope

- Changing provenance values (`direct`, fixture names).
- CI artifact upload or retention.
- New logging events or metrics.

## Functional Requirements

- FR1: `_build_diagnostics` emits `"session_source"` with the provenance string.
- FR2: `dump_agent_e2e_failure_artifacts(..., session_source=...)` is the public
  kwarg (old name removed).
- FR3: Auto-dump paths (makereport hook, direct `__exit__` hook) populate
  `session_source` correctly.
- FR4: Documentation table, usage example, and troubleshooting reference
  `session_source`.

## Non-Functional Requirements

- NFR1: No behavior change beyond the field rename.
- NFR2: Existing tests updated; focused contract test for the new key.
- NFR3: Line length ≤ 100 characters.

## Q&A

| Question | Answer |
| --- | --- |
| Backward compatibility for old dumps? | Old artifacts may still have `session_fixture`; readers should accept both during transition or re-run failures. No migration script. |
| Rename pytest fixture names? | No — only diagnostics / API kwarg. |
| Product logging change? | No — provenance is file-only in diagnostics.json. |
