# PYPOST-329: Automated GUI tests for collection tree context menu

## Goals

Collection tree right-click actions (New tab, Rename, Delete) were implemented in
PYPOST-35 but lacked automated GUI coverage. Without tests, regressions in menu
composition, confirmation branching, or signal emission can reach users unnoticed.
This debt item closes that gap so maintainers can refactor tree actions safely.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want automated tests for collection tree context menus so menu
  actions and side effects stay correct when the UI is refactored.
- As a maintainer, I want tests that cover both collection and request nodes so menu
  options match item type.
- As a maintainer, I want delete confirmation branching tested so Yes/No outcomes are
  verified at the GUI layer (complementing PYPOST-330 metric-focused coverage).

## Definition of Done

- Automated Qt-level tests exercise `CollectionTreeActions.show_context_menu` through
  the wired `CollectionsPresenter` tree.
- Invalid click positions do not open a menu.
- Collection nodes show **Rename** and **Delete** only.
- Request nodes show **New tab**, **Rename**, and **Delete**.
- Selecting **Rename** starts inline edit (pending rename state).
- Selecting **New tab** on a request emits `open_isolated_tab` with a copied request.
- Selecting **Delete** and confirming removes the item; cancelling leaves the tree
  unchanged.
- All new and existing related tests pass.
- Developer docs list the new test module.

## Task Description

Follow-up from `ai-tasks/PYPOST-35/60-tech-debt.md`. Scope is GUI tests for
right-click context menu behavior on the collections tree — not metrics (PYPOST-331),
not open-tab reconciliation after delete (PYPOST-332), and not confirmation-dialog
metric labels alone (PYPOST-330).

### Scope

- In scope: `CollectionTreeActions.show_context_menu` menu composition and dispatch.
- Out of scope: full MainWindow integration, Prometheus metric assertions, tab cleanup
  after delete.

## Q&A

- **Q:** Unit tests on `CollectionTreeActions` or full MainWindow? **A:** Presenter-wired
  Qt tests with mocked `QMenu`/`QMessageBox`, consistent with `test_history_panel.py`
  and existing `test_collections_presenter.py` patterns.
