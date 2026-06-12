# PYPOST-71 — Requirements: Explicit Tab Reference in Send Handler

> Analyst: 2026-06-12
> Jira: PYPOST-71
> Parent: PYPOST-43 (TD-6)
> Type: Debt
> Priority: Medium

---

## 1. Problem Statement

`TabsPresenter._handle_send_request` locates the originating tab by scanning all tabs and
comparing each `request_editor` to `QObject.sender()`. That API is fragile: it returns
`None` outside a Qt signal-slot invocation and couples the presenter to Qt's internal
dispatch. The tab is already known when `send_requested` is wired in `_wire_tab_signals`.

---

## 2. Scope

### In-Scope

1. Pass the tab reference explicitly into `_handle_send_request` at signal connection time.
2. Remove the `self.sender()` tab lookup loop from `_handle_send_request`.
3. Add a test proving the handler works without a signal sender context.
4. All existing send/worker tests must pass.

### Out-of-Scope

- Refactoring `_find_tab_for_sender` used by save/copy handlers (separate tech debt).
- Observability or metrics changes.

---

## 3. Functional Requirements

### FR-1 — Explicit tab at wire time

`_wire_tab_signals` must connect `send_requested` with a closure that captures the tab and
calls `_handle_send_request(sender_tab, request_data)`.

### FR-2 — No sender() lookup in send path

`_handle_send_request` must not call `self.sender()` or iterate tabs to find the origin.

### FR-3 — Behavioral parity

Send, stop, stale-worker guard, and worker creation behavior must remain unchanged for
signal-driven sends.

---

## 4. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `_handle_send_request(self, sender_tab, request_data)` signature in `tabs_presenter.py`. |
| AC-2 | `_wire_tab_signals` uses closure `lambda data, t=tab: self._handle_send_request(t, data)`. |
| AC-3 | No `self.sender()` usage inside `_handle_send_request`. |
| AC-4 | New test calls `_handle_send_request(tab, data)` directly and asserts worker on correct tab. |
| AC-5 | `tests/test_tabs_presenter.py`, `tests/test_worker_race.py` pass. |
