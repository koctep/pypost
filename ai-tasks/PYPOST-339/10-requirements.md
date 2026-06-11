# PYPOST-339: Delete metric emission tests by status and item type

## Goals

PYPOST-35 added delete-action telemetry (`gui_collection_delete_actions_total`) with
status labels and item types. Confirmation-dialog outcomes (`selected`, `cancelled`,
`succeeded`) are covered by PYPOST-330, but `handle_delete` failure paths lacked
automated metric assertions. This debt item prevents silent regressions on error and
not-found telemetry.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want tests that verify `error` metrics when delete persistence
  raises, for both collection and request items.
- As a maintainer, I want tests that verify `not_found` metrics when delete returns
  false, for both collection and request items.
- As a maintainer, I want failure paths to avoid emitting success metrics.

## Definition of Done

- Automated tests call `CollectionTreeActions.handle_delete` via `CollectionsPresenter`
  with controlled `RequestManager` outcomes.
- Collection + request: exception → single `error` metric, tree unchanged.
- Collection + request: `False` return → single `not_found` metric, tree unchanged.
- No spurious `succeeded` metric on failure paths.
- All new and related tests pass.
- Developer docs list the new test module and metric matrix.

## Task Description

Follow-up from `ai-tasks/PYPOST-35/60-tech-debt.md`. Complements PYPOST-330
(confirmation branching metrics) with `handle_delete` outcome metrics.

### Scope

- In scope: `track_gui_collection_delete_action` for `error` and `not_found` on
  `handle_delete`, both `collection` and `request` item types.
- Out of scope: confirmation-dialog `selected` / `cancelled` (PYPOST-330), Prometheus
  scrape integration, production code changes unless a defect is found.

## Q&A

- **Q:** Overlap with PYPOST-331? **A:** PYPOST-331 tracks the same debt line; this
  task delivers the `handle_delete` metric matrix. Confirmation metrics remain in
  PYPOST-330 tests.
