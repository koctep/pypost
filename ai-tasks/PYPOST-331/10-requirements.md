# PYPOST-331: No tests for emitted metric labels/status values for delete actions

## Goals

PYPOST-35 introduced delete-action telemetry (`gui_collection_delete_actions_total`)
with status labels (`selected`, `cancelled`, `succeeded`, `not_found`, `error`) and
item types (`collection`, `request`). Without automated assertions, regressions in
metric emission could go unnoticed in CI. This debt item ensures the full status
matrix is covered by headless unit tests.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want tests that verify every delete metric status for both
  collection and request item types.
- As a maintainer, I want confirmation-dialog paths (`selected`, `cancelled`,
  `succeeded`) and `handle_delete` failure paths (`error`, `not_found`) covered.
- As a maintainer, I want failure paths to avoid emitting spurious `succeeded` metrics.
- As a maintainer, I want developer docs to list the test modules and metric matrix.

## Definition of Done

- All five status values asserted in automated tests for both item types where
  applicable.
- Confirmation boundary and `handle_delete` failure paths each have dedicated tests.
- All delete metric tests pass headlessly (`QT_QPA_PLATFORM=offscreen`).
- Developer docs reference the test modules and status matrix.
- PYPOST-35 tech-debt entry for missing metric label tests is resolved.

## Task Description

Follow-up from `ai-tasks/PYPOST-35/60-tech-debt.md`. Delivery spans confirmation
tests (PYPOST-330) and `handle_delete` failure tests (PYPOST-339). This issue
closes the umbrella debt once combined coverage is verified and documented.

### Scope

- In scope: metric assertions on `track_gui_collection_delete_action`, both item
  types, all five status values, developer documentation cross-references.
- Out of scope: live Prometheus scrape validation, GUI context-menu composition
  (PYPOST-329), open-tab cleanup (PYPOST-332).

## Q&A

- **Q:** Overlap with PYPOST-339? **A:** PYPOST-339 delivered `handle_delete`
  failure metrics; PYPOST-330 delivered confirmation metrics. PYPOST-331 closes the
  parent debt line once the combined matrix is verified.
- **Q:** New production code needed? **A:** No — existing instrumentation is
  sufficient; only test coverage and documentation were missing.
