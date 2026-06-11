# PYPOST-342: Rename test coverage does not include GUI

Parent epic: [PYPOST-36](https://pypost.atlassian.net/browse/PYPOST-36) — Add Rename Action to
Context Menu.

## Goals

Ensure the collections-tree rename flow is covered by automated GUI and presenter tests so
regressions in context-menu dispatch, inline edit wiring, validation feedback, and rename
metrics are caught before release.

## User Stories

- As a maintainer, I want rename context-menu selection tested at the GUI layer so menu
  dispatch and inline edit startup stay correct.
- As a maintainer, I want presenter-level rename tests for success, cancel, empty-name
  rejection, persistence errors, and not-found paths so observability and tree sync stay
  aligned with delete-flow coverage.

## Definition of Done

- Context-menu **Rename** selection is tested for collection and request nodes (isolated and
  presenter wiring).
- Rename lifecycle paths record the expected `track_gui_collection_rename_action` statuses:
  `selected`, `cancelled`, `succeeded`, `rejected_empty`, `error`, `not_found`.
- Tests follow project timeout rules (`pytest.mark.timeout`).
- Full test suite passes.

## Scope

- In scope: `CollectionTreeActions`, `CollectionsPresenter`, shared test helpers.
- Out of scope: end-to-end storage collision tests, live browser verification, production code
  changes beyond test support helpers.
