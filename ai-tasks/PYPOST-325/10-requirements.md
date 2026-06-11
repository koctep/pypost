# PYPOST-325: Dedicated metric-focused automated tests for deletion telemetry

## Goals

PYPOST-35 introduced delete-action telemetry (`gui_collection_delete_actions_total`) with
status labels and item types, but shipped without automated tests that assert metric
emission. Maintainers need confidence that regressions in telemetry — silent drops of
`cancelled`, `error`, or `not_found` counters — are caught in CI.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want automated tests that verify every delete metric status
  (`selected`, `cancelled`, `succeeded`, `not_found`, `error`) for both collection
  and request item types.
- As a maintainer, I want tests to run headlessly in CI without manual Prometheus
  scraping.
- As a maintainer, I want developer docs to list the test modules and metric matrix.

## Definition of Done

- Confirmation-dialog path (`show_context_menu`) asserts `selected`, `cancelled`, and
  `succeeded` metrics for collection and request nodes.
- Post-confirmation `handle_delete` path asserts `error` and `not_found` metrics for
  both item types; failure paths do not emit `succeeded`.
- All metric-focused delete tests pass.
- `doc/dev` documents the test modules and status matrix.
- PYPOST-35 tech-debt entry for missing metric tests is resolved.

## Task Description

Parent debt item from `ai-tasks/PYPOST-35/60-tech-debt.md`. Delivery spans
confirmation-boundary tests (PYPOST-330) and `handle_delete` failure tests
(PYPOST-339). This task closes the umbrella debt once the combined coverage is
verified and documented.

### Scope

- In scope: metric assertions on `track_gui_collection_delete_action`, both item types,
  all five status values, developer documentation.
- Out of scope: live Prometheus scrape validation, GUI context-menu composition
  (PYPOST-329), open-tab cleanup (PYPOST-332).

## Q&A

- **Q:** Why not one monolithic test file? **A:** Confirmation and `handle_delete`
  failure paths exercise different entry points; separate modules keep tests focused
  and match incremental debt resolution (PYPOST-330, PYPOST-339).
- **Q:** Overlap with PYPOST-331? **A:** PYPOST-331 tracked the same missing-tests
  line; close or deduplicate PYPOST-331 when this umbrella debt is resolved.
