# Sprint 134 — Sprint Report

> Date: 2026-03-25
> Sprint: 134
> Reporter: Team Lead

---

## Result Summary

**3 of 3 issues completed. 0 failed.**

| Key | Summary | Result | Commits |
|-----|---------|--------|---------|
| PYPOST-403 | Fix failing tests in CI | Done | `afd2a58` |
| PYPOST-404 | Font size settings not applied on startup | Done | `4ac96b8`, `cf45465` |
| PYPOST-405 | Open request in new independent tab | Done | `061a590` |

Test suite: **191 passed, 0 failed** across all three issues — baseline restored and maintained.

---

## Done Issues

### PYPOST-403 · Fix failing tests in CI

Resolved two independent test-infrastructure regressions:
1. `HTTPClient` now default-constructs `TemplateService()` when the argument is `None`, closing
   the latent `AttributeError` that broke 3 SSE probe tests.
2. `HistoryManager` now stores `_save_thread` and exposes `flush()`, providing deterministic
   synchronisation before temp-dir teardown — fixes 2 `OSError` race failures.
An 86 MB ELF crash dump was removed from the repo root and `core`/`core.*` patterns were added to
`.gitignore`. No new debt introduced. Observability logs added for lifecycle and timing.

### PYPOST-404 · Font size settings not applied on application startup

Call-order fix in `apply_settings`: `style_manager.apply_styles(app)` now executes before
`app.setFont(font)`, preventing Qt 6's stylesheet re-polish from overriding the user-configured
font size. `ConfigManager` injected from `main.py` into `MainWindow` (FR-4), eliminating a
redundant `load_config()` on startup. Three automated tests (T-1 font-is-applied, T-2 exact-size,
T-3 style-applied-first) verify the fix. No regressions.

### PYPOST-405 · Open request in new independent tab

Added `open_request_in_isolated_tab` Qt signal and "New tab" context menu item on collection
request items. Tab opening uses `model_copy(deep=True)` to ensure each tab receives an isolated
`RequestData` graph. `restore_tabs` was hardened to avoid aliasing multiple restored tabs to the
same model reference. Implementation is fully wired through `CollectionsPresenter` → `MainWindow`
→ `TabsPresenter`. Observability and code cleanup phases completed.

---

## Failed Issues

None.

---

## Key Risks

### RISK-1 (Carried from Sprint 100, still open) — AlertManager not wired into RequestWorker

`AlertManager` (PYPOST-402) is fully implemented and unit-tested but is never injected at the
production call-site (`pypost/core/worker.py`). Alerts will never fire until TD-1 is resolved.

**Recommendation**: Schedule in next sprint alongside TD-2.

### RISK-2 (Carried from Sprint 100, still open) — default_retry_policy has no runtime effect

`AppSettings.default_retry_policy` is saved by the Settings UI but not read by `RequestWorker`
or `RequestService`. All requests without a per-request policy silently fall back to
`max_retries=0`.

**Recommendation**: Schedule in next sprint alongside TD-1.

---

## Technical Debt Backlog (new items from Sprint 134)

### From PYPOST-403

| ID | Severity | Description |
|----|----------|-------------|
| — | Low | Investigate root cause of the deleted `core` crash dump (separate backlog item) |
| — | Low | Replace SSE URL heuristic (`"/sse" in url`) with content-type-based detection |

### From PYPOST-404

| ID | Jira | Severity | Description |
|----|------|----------|-------------|
| TD-1 | PYPOST-425 | Low | Explicit widget font loop in `apply_settings` is now redundant — consider removing |
| TD-2 | PYPOST-426 | Low | `apply_settings(self, settings)` parameter lacks `AppSettings` type annotation |
| TD-3 | PYPOST-427 | Very Low | Document ConfigManager early-creation intent in architecture notes |

### From PYPOST-405

| ID | Jira | Priority | Description |
|----|------|----------|-------------|
| TD-1 | PYPOST-406 | Medium | Unify object-copying behaviour for left-click tree navigation |
| TD-2 | PYPOST-407 | Low | Deep-copy overhead if `RequestData` grows heavier in future |
| TD-3 | PYPOST-408 | Medium | Stale tabs not notified when disk state changes from another tab |

---

## Recommendations for Next Sprint

1. **Wire TD-1 and TD-2 from Sprint 100** (AlertManager injection, default_retry_policy runtime
   application). Both are small wiring fixes (< 20 lines each) but represent a release blocker
   for the PYPOST-402 alerting and retry-policy features.
2. **Schedule PYPOST-406** (left-click tree navigation unification) alongside any further
   collections-tree work to keep the object-copying contract consistent.
3. **Schedule PYPOST-408** (stale-tab metadata sync) as a medium-priority follow-up to PYPOST-405
   if the team sees user-facing complaints about stale tab titles/URLs.
4. **File a bug ticket** for the crash that produced the deleted `core` dump — it may indicate an
   application-level crash path that needs investigation.
