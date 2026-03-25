# Sprint 134 — Execution Report

> Date: 2026-03-25
> Sprint: 134
> Total issues: 3

---

## Completed Issues

| # | Key | Summary | Commit(s) |
|---|-----|---------|-----------|
| 1 | PYPOST-403 | Fix failing tests in CI | `afd2a58` |
| 2 | PYPOST-404 | Font size settings not applied on startup | `4ac96b8`, `cf45465` |
| 3 | PYPOST-405 | Open request in new independent tab | `061a590` |

---

## Failed Issues

None.

---

## Blockers

None encountered during execution.

---

## Retries Performed

None. All 3 issues completed on first attempt.

---

## Notes

- **PYPOST-403** resolved two independent test-infrastructure regressions and removed an 86 MB ELF
  crash dump from the repo. Fixes: `HTTPClient` default-constructs `TemplateService()` when arg is
  `None`; `HistoryManager` retains `_save_thread` reference and exposes a `flush()` method.
  Full test suite: **191 passed, 0 failed**.

- **PYPOST-404** fixed call-order regression in `apply_settings` (Qt 6 stylesheet re-polish was
  overriding `app.setFont`). `ConfigManager` is now injected from `main.py` into `MainWindow`,
  eliminating a redundant `load_config()` call. Three low-severity tech debt items identified
  (TD-1 PYPOST-425, TD-2 PYPOST-426, TD-3 PYPOST-427) — none require immediate action.
  Test suite: **191 passed, 0 failed**.

- **PYPOST-405** added `open_request_in_isolated_tab` signal and "New tab" context menu in
  `CollectionsPresenter`, wired in `MainWindow`, and passed a `model_copy(deep=True)` of
  `RequestData` into `TabsPresenter.add_new_tab`. `restore_tabs` was also fixed to avoid aliasing
  multiple tabs to the same model instance. Three medium/low tech debt items flagged for backlog
  (PYPOST-406 left-click unification, PYPOST-407 deep-copy overhead, PYPOST-408 stale-tab
  metadata sync).
