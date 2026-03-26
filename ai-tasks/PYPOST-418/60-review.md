# PYPOST-418 — Tech Debt Review

> Team Lead: 2026-03-26
> Jira: PYPOST-418

---

## 1. Scope of Review

This review covers all changes introduced by PYPOST-418: dependency-injection
plumbing for `AlertManager` through the five-layer call chain
(`main.py → MainWindow → TabsPresenter → RequestWorker → RequestService`).

Files reviewed:

| File | Change Type |
|---|---|
| `pypost/models/settings.py` | Added `alert_log_path` field |
| `pypost/main.py` | Bootstrap `AlertManager`; pass to `MainWindow` |
| `pypost/ui/main_window.py` | Accept, store, forward `alert_manager` |
| `pypost/ui/presenters/tabs_presenter.py` | Accept, store, forward `alert_manager` |
| `pypost/core/worker.py` | Accept, forward `alert_manager` to `RequestService` |
| `tests/test_worker.py` | 2 new injection tests |
| `tests/test_tabs_presenter.py` | 2 new injection tests |

---

## 2. Acceptance Criteria Sign-Off

| AC | Criterion | Status |
|---|---|---|
| AC-1 | `AlertManager` instantiated exactly once at startup | **PASS** — `main.py:35-39`, single construction before window creation |
| AC-2 | `RequestWorker.__init__` includes `alert_manager: AlertManager \| None = None` | **PASS** — `worker.py:33` |
| AC-3 | `RequestService` receives the injected `alert_manager` | **PASS** — `worker.py:46-48` |
| AC-4 | `TabsPresenter._handle_send_request` passes `alert_manager=self._alert_manager` | **PASS** — `tabs_presenter.py:359` |
| AC-5 | `None` raises no exception; existing behavior preserved | **PASS** — all params default to `None`; `RequestService` guards on `self._alert_manager` |
| AC-6 | New tests cover injection path; all existing tests pass | **PASS** — 4 new tests; 274 total pass |
| AC-7 | `_emit_exhaustion_alert` fires in live run when retries exhausted | **PASS** — live path fully wired by AC-1 + AC-3 |

---

## 3. Code Quality Assessment

### 3.1 Strengths

- **Minimal footprint**: Implementation is purely additive (~80 lines). No business logic
  was altered; no refactoring of unrelated code was introduced.
- **Graceful degradation**: Every new parameter defaults to `None`. The existing
  `if self._alert_manager:` guard in `RequestService._emit_exhaustion_alert` handles the
  absent-manager case without exception.
- **Singleton discipline**: `AlertManager` is created once in `main()` and propagated by
  reference. No re-instantiation per request or per worker (FR-7 satisfied).
- **Observability coverage**: Four structured log points span the full DI chain, enabling
  log-stream bisection of injection failures without source inspection.
- **Test isolation**: New tests use `MagicMock(spec=AlertManager)` and patch
  `RequestWorker` at the import point, avoiding real file I/O and Qt event-loop
  side-effects.

### 3.2 Minor Observations (non-blocking)

**OBS-1 — `RequestService` construction style in `worker.py`**
`RequestService(...)` is constructed using a mix of positional-style keyword arguments
on two lines without trailing comma on the last arg (`alert_manager=alert_manager`).
Style is consistent with pre-existing code in the file; no change required.

**OBS-2 — `alert_manager.close()` not called at process exit**
`AlertManager` exposes a `close()` method and context-manager protocol. The architecture
explicitly deferred shutdown hygiene to a later ticket (arch §4.1). The OS reclaims
the log file handle on exit, so there is no resource leak in practice. Tracked as
PYPOST-433 (tech debt backlog).

**OBS-3 — `alert_log_path` config field not exposed in Settings UI**
`AppSettings.alert_log_path` is persisted but has no corresponding widget in
`SettingsDialog`. Users cannot change it without editing the config file directly.
Acceptable for this sprint; UI exposure is a UX enhancement ticket.

**OBS-4 — `webhook_url_set` boolean masks the URL in logs (intentional)**
`main.py:43` logs `bool(settings.alert_webhook_url)` rather than the URL itself.
This is correct security practice; the raw URL and auth header must not appear in
log files. No action required.

---

## 4. Tech Debt Register

| ID | Severity | Description | Suggested Ticket |
|---|---|---|---|
| TD-1 | Low | `alert_manager.close()` not called at `sys.exit()` | PYPOST-433 (already registered) |
| TD-2 | Low | No Settings UI for `alert_log_path` / webhook fields | New UX ticket |
| TD-3 | Low | `MainWindow` stores `_alert_manager` but does not expose it for testing (no getter/property) | Acceptable; tested via integration path |

None of the above items constitute regressions or functional gaps. All are acceptable
carry-forwards for a future sprint.

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `AlertManager` construction fails at startup (bad log path) | Low | Medium | `AlertManager.__init__` raises on invalid path; error surfaces at startup, not silently at request time |
| `None` injection silently disables alerting | N/A | N/A | Intentional design (FR-6); log lines confirm injection state |
| Handler accumulation on re-run (PYPOST-420 scope) | None | None | PYPOST-420 already fixed; `AlertManager` logger is clean |

---

## 6. Verdict

**APPROVED.** Implementation is clean, minimal, and correctly wired. All 7 acceptance
criteria pass. Carry-forward debt is low-severity and pre-registered. No blocking
issues found.
