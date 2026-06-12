# PYPOST-72 — Requirements: Save Tab Index Before Dialog

> Analyst: 2026-06-12
> Jira: PYPOST-72
> Parent: PYPOST-43 (TD-8)
> Type: Debt
> Priority: Medium

---

## 1. Problem Statement

After a save or save-as dialog closes, `TabsPresenter` reads `QTabWidget.currentIndex()` to
decide which tab receives the persisted name and baseline. While the modal dialog is open,
the user may switch tabs (keyboard shortcuts on some platforms). The post-dialog index can
then point at the wrong tab, mislabeling it and applying save state to the wrong editor.

---

## 2. Scope

### In-Scope

1. Identify the originating request tab before the save orchestrator shows a modal dialog.
2. Apply save-new and save-as UI updates to that tab (or the tab index captured before the
   dialog when sender lookup is unavailable).
3. Add tests proving correct tab is updated when `currentIndex()` changes during dialog exec.
4. All existing save/save-as tests must pass.

### Out-of-Scope

- Refactoring `_wire_tab_signals` to pass explicit tab refs for save handlers (future debt).
- Observability or metrics changes.

---

## 3. Functional Requirements

### FR-1 — Tab identity before dialog

Save handlers must capture the source tab (via sender lookup) or tab index before calling
the save orchestrator.

### FR-2 — Post-dialog application

After a successful save-new or save-as, tab label and persisted baseline updates must target
the captured tab, not `currentIndex()` read after the dialog.

### FR-3 — Behavioral parity

Overwrite save path, cancellation, and collection persistence behavior unchanged.

---

## 4. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | No `currentIndex()` read after save orchestrator returns in save-new/save-as paths. |
| AC-2 | Tab label and `_apply_save_result_to_tab` target the originating tab. |
| AC-3 | Tests simulate tab switch during dialog and assert only source tab changes. |
| AC-4 | `tests/test_tabs_presenter.py` and save-flow tests pass. |
