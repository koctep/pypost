# PYPOST-963: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Documented and asserted the slow-smoke minimum `pypost/` stub tree policy. Changes are
policy constant, one fast contract test, and dev docs — no seed helper or CI edits.

## Shortcuts Taken

- **Exact file-set assertion under `pypost/` only.** Does not assert workspace-root files
  (`README.md`, `Makefile`) in the minimum-tree test — covered separately by pyproject
  artifact test (TD-1).
- **Policy constant is manual.** Not derived from `pyproject.toml` automatically; widening
  requires updating constant + seed together (intentional explicit policy).

## Code Quality Issues

None introduced. Aligns with PYPOST-943 seed helpers.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Minimum stub `pypost/` tree (no subpackages) | Covered — `test_slow_smoke_seed_materializes_minimum_pypost_tree` |
| Pyproject-derived packaging artifacts | Covered — existing PYPOST-943 test |
| Future dynamic metadata beyond version/readme | Deferred — PYPOST-964 |
| Workspace assembly deduplication | Deferred — PYPOST-965 |

## Performance Concerns

None — one additional fast filesystem assertion.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | None new | Parent PYPOST-943 follow-ups (964–967) remain tracked there | — |

## Blocker review

**No blockers.** Policy documented and machine-checked. Safe to close.
