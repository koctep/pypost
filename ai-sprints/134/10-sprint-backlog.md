# Sprint 134 — Backlog

> Date: 2026-03-25
> Total issues: 3
> Priority: Highest / High

## Issues

| # | Key | Summary | Type | Priority | Status |
|---|-----|---------|------|----------|--------|
| 1 | PYPOST-403 | [HP] Fix failing tests in CI | Debt | Highest | Done |
| 2 | PYPOST-404 | [Bug] Font size settings not applied on application startup | Bug | High | Done |
| 3 | PYPOST-405 | Open request in new independent tab | Feature | High | Done |

## Execution Order & Rationale

### 1 · PYPOST-403 — Fix failing CI tests

**Description:** Investigate and fix 5 currently-failing automated tests in CI: 3 `AttributeError`
failures in SSE probe tests due to `HTTPClient` missing a `TemplateService`, and 2 `OSError`
failures in `HistoryManager` tests caused by temp-dir cleanup racing the async save thread.

**Rationale:** Foundational. CI must be green before any new feature work. Fixes unblock the
remaining debt items from Sprint 100 (TD-1 wiring of `AlertManager`, TD-2 runtime retry policy)
which also rely on a stable test baseline.

---

### 2 · PYPOST-404 — Font size settings not applied on application startup

**Description:** After the user changes font size settings and restarts the application, the
selected font size is not applied. Root cause: Qt 6 `setStyleSheet()` re-polishes all widgets and
resets the app-level font; `apply_settings` called `app.setFont(font)` before
`style_manager.apply_styles(app)`.

**Rationale:** High-visibility UI regression. Directly impacts user trust. Fix is surgical
(call-order swap + ConfigManager injection; < 20 lines).

---

### 3 · PYPOST-405 — Open request in new independent tab

**Description:** Add a "New tab" context menu item on collection request items so a user can open
duplicate editors for the same saved request. Each new tab must receive a deep copy of
`RequestData` to prevent inadvertent shared-state mutations.

**Rationale:** User-facing feature enabling parallel request editing workflows. Depends on a
stable test suite (PYPOST-403) to confirm no regressions.

---

## Notes

- Sprint 100 tech debt (TD-1 `AlertManager` wiring, TD-2 default retry policy) was assessed but
  is NOT in this sprint — PYPOST-403 made the test suite green, unblocking a future sprint for
  those items.
- All three issues are independent and were executed sequentially for CI stability.
