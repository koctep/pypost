# PYPOST-330: Delete confirmation-dialog Yes/No branching tests

## Goals

PYPOST-35 added a confirmation dialog before collection-tree deletes, but automated
tests did not assert the Yes/No branch outcomes. Without coverage, a regression could
skip the dialog, call delete on cancel, or drop telemetry on the cancelled path.
This debt item locks in correct branching for both collection and request nodes.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want tests that verify **No** cancels delete and records
  `cancelled` telemetry so accidental deletes are not persisted.
- As a maintainer, I want tests that verify **Yes** proceeds to delete and records
  `succeeded` telemetry for both collection and request items.
- As a maintainer, I want confirmation-dialog message content exercised so label
  regressions are caught.

## Definition of Done

- Automated Qt-level tests exercise `CollectionTreeActions.show_context_menu` delete
  path through `CollectionsPresenter` with mocked `QMessageBox.question`.
- **No** on collection node: tree unchanged, `selected` + `cancelled` metrics, no
  `handle_delete`.
- **Yes** on collection node: collection removed, `selected` + `succeeded` metrics.
- **No** on request node: request remains, `selected` + `cancelled` metrics.
- **Yes** on request node: request removed, `selected` + `succeeded` metrics.
- All new and related tests pass.
- Developer docs list the new test module.

## Task Description

Follow-up from `ai-tasks/PYPOST-35/60-tech-debt.md`. Complements PYPOST-329
(context-menu composition and tree side effects) with metric-focused confirmation
branching. Full delete metric status matrix (`error`, `not_found`, etc.) remains
PYPOST-331.

### Scope

- In scope: confirmation Yes/No branching, `track_gui_collection_delete_action` on
  `selected` / `cancelled` / `succeeded` at the dialog boundary.
- Out of scope: context-menu item lists (PYPOST-329), post-delete tab cleanup
  (PYPOST-332), exhaustive metric label matrix (PYPOST-331).

## Q&A

- **Q:** Duplicate `test_collections_presenter.py` delete tests? **A:** Presenter
  tests use a no-op metrics stub; this module asserts metric call sequences and
  covers both item types explicitly at the confirmation boundary.
