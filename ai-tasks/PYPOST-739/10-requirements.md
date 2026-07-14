# PYPOST-739: Document Error-Handling Convention

> Parent: [PYPOST-687](https://pypost.atlassian.net/browse/PYPOST-687) R-P3-003

## Summary

Document PyPost's three error-handling patterns — **log-only**, **log + dialog**, and
**silent pass** — so new code follows consistent conventions instead of mixing ad hoc
approaches.

## User Stories

- As a **contributor**, I want a clear decision guide for error paths, so I pick the right
  pattern (log, dialog, or silent fallback) without reading dozens of call sites.
- As a **reviewer**, I want the convention referenced in dev docs, so PRs can be checked
  against a single source of truth.

## Acceptance Criteria

- [x] Error-handling section expanded in `doc/dev/maintainability_audit.md` (or
  `architecture.md`).
- [x] Three patterns documented with when-to-use guidance and real module examples.
- [x] Layer rules stated: `core/` logs; `ui/` owns user-visible messaging via
  `collection_item_dialogs.py`.
- [x] Cross-references to `logging.md`, `collection_tree_actions.md`, and persistence docs.
- [x] No application code changes required.

## Out of Scope

- Refactoring existing handlers to match the convention (R-P2-004 and follow-ups).
- Adding new QMessageBox helpers or metrics for error paths.
- Resolving remaining direct `QMessageBox` usage outside `collection_item_dialogs.py`.

## Constraints

- Documentation-only; `make check` must pass (no regressions from doc edits).
