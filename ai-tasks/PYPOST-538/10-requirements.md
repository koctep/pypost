# PYPOST-538: Extract shared collections tree test fixtures

## Goals

Deduplicate context-menu test setup shared between `test_collections_presenter.py` and
isolated `CollectionTreeActions` tests. Consolidate PYPOST-537 harness into a single
`tests/helpers/collections_tree.py` module.

## User Stories

- As a maintainer, I want one place for fake managers and QMenu patch helpers so tree tests
  stay consistent when menu wiring changes.
- As a contributor, I want presenter and isolated tests to import the same fixtures without
  copying `_patch_menu` or `FakeRequestManager` blocks.

## Definition of Done

- `tests/helpers/collections_tree.py` exports shared fixtures and context-menu patch helpers.
- `test_collections_presenter.py`, `test_collection_tree_actions.py`, and
  `test_collection_tree_delete_confirmation.py` import from the shared module.
- `tests/collection_tree_actions_test_support.py` removed (merged into helpers).
- All affected unit tests pass.
- Dev docs reference the shared helper module.

## Task Description

Follow-up from `ai-tasks/PYPOST-329/60-tech-debt.md`. PYPOST-537 introduced an isolated
harness in `collection_tree_actions_test_support.py`; this task unifies that harness with
presenter test helpers.

### Programming Language

Python

### Functional Requirements

- Shared `FakeRequestManager`, `FakeStateManager`, `FakeMetrics`, `make_collection`,
  `make_request`.
- Context-menu patch helpers: `patch_tree_context_menu`, `patch_view_context_menu`,
  `patch_delete_context_menu`.
- Isolated harness: `IsolatedTreeActions`, `build_isolated_tree_actions`.

### Non-Functional Requirements

- No production code changes.
- Patch targets remain `pypost.ui.presenters.collection_tree_actions`.
