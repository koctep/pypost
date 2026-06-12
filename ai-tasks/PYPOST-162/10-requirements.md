# PYPOST-162 — Requirements: Centralize Tab Signal Wiring

> Analyst: 2026-06-12
> Jira: PYPOST-162
> Parent: PYPOST-22 (Manual Signal Connection)
> Type: Debt
> Priority: Medium

---

## 1. Problem Statement

Per-tab Qt signals in `TabsPresenter` are connected inside `add_new_tab`. Save and save-as
handlers still resolve the originating tab via `QObject.sender()` at dispatch time. That pattern
is fragile (same class of issue resolved for send in PYPOST-71) and scatters tab lifecycle
concerns across `add_new_tab` instead of a single factory path.

---

## 2. Scope

### In-Scope

1. Centralize request-tab creation and signal wiring in one private method used by `add_new_tab`.
2. Connect save and save-as signals with closure bindings that pass the `RequestTab` explicitly.
3. Remove `_find_tab_for_sender` and post-dialog `currentIndex()` fallbacks for save paths.
4. Add tests proving save handlers work without a signal sender context.
5. All existing tab/save tests must pass.

### Out-of-Scope

- Refactoring copy-curl handler signature (no tab lookup today).
- Observability or metrics changes.

---

## 3. Functional Requirements

### FR-1 — Single tab factory

All dynamically created request tabs must go through one method that wires signals before the tab
is inserted into the widget.

### FR-2 — Explicit tab at wire time

Save and save-as handlers receive the originating `RequestTab` from the signal connection
closure, not from `self.sender()`.

### FR-3 — Behavioral parity

Save-new, save-as, overwrite, cancellation, and collection persistence behavior unchanged.

---

## 4. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `_create_request_tab` encapsulates tab construction, env/indent setup, and `_wire_tab_signals`. |
| AC-2 | `_wire_tab_signals` uses closure bindings for save and save-as (like send). |
| AC-3 | No `_find_tab_for_sender` or `self.sender()` in save/save-as handlers. |
| AC-4 | New test calls `_handle_save_request(tab, data)` directly without sender context. |
| AC-5 | `tests/test_tabs_presenter.py` and save-flow integration tests pass. |
