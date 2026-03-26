# PYPOST-418 — Requirements: AlertManager Never Injected into RequestWorker

> Analyst: 2026-03-26
> Jira: PYPOST-418
> Parent: PYPOST-402
> Sprint: 167
> Priority: High
> Type: Tech Debt

---

## 1. Problem Statement

`AlertManager` is fully implemented and its infrastructure is wired inside `RequestService`
(see `request_service.py:45-59`). However, it is **never instantiated at application
bootstrap** (`main.py`) and **never injected into `RequestWorker`** (`worker.py:24-41`).

As a consequence:

- `RequestWorker` creates `RequestService` without an `alert_manager` (worker.py:39).
- `RequestService._emit_exhaustion_alert()` silently no-ops because `self._alert_manager`
  is always `None` in production.
- All retry-exhaustion alert callbacks are dead code in the running application.

This was registered as RISK-1 carry-forward in Sprint 134.

---

## 2. Scope

### In-Scope

1. Instantiate `AlertManager` at application bootstrap (`main.py` or equivalent entry
   point) using application config (log path, optional webhook URL / auth header).
2. Propagate the `AlertManager` instance down the call chain:
   `main.py` → `MainWindow` → `TabsPresenter` → `RequestWorker` → `RequestService`.
3. `RequestWorker.__init__` must accept an optional `alert_manager: AlertManager | None`
   parameter and forward it to `RequestService`.
4. `TabsPresenter._handle_send_request()` must pass the stored `_alert_manager` reference
   when constructing `RequestWorker`.
5. `MainWindow` must receive and store the `AlertManager` instance, forwarding it to
   `TabsPresenter` (or directly to any presenter that creates `RequestWorker`).
6. All existing tests must continue to pass (no regressions).
7. New unit tests covering the injection path in `RequestWorker` and
   `TabsPresenter`.

### Out-of-Scope

- Changes to `AlertManager` internals (covered by PYPOST-420, already closed).
- Retry policy logic changes (PYPOST-419).
- New alert event types beyond what `AlertPayload` already supports.
- UI alert display / notification surfaces.

---

## 3. Functional Requirements

### FR-1 — Bootstrap Instantiation

The application entry point (`main.py`) MUST create exactly one `AlertManager` instance
before the main window is shown. Construction parameters MUST be sourced from application
configuration (e.g., `config_manager`):

| Config key | AlertManager param | Fallback |
|---|---|---|
| `alerts.log_path` | `log_path` | `~/.pypost/alerts.log` |
| `alerts.webhook_url` | `webhook_url` | `None` |
| `alerts.webhook_auth_header` | `webhook_auth_header` | `None` |

### FR-2 — MainWindow Receives AlertManager

`MainWindow.__init__` MUST accept an optional `alert_manager: AlertManager | None`
parameter. The instance MUST be stored and forwarded to any presenter that creates
`RequestWorker`.

### FR-3 — TabsPresenter Receives AlertManager

`TabsPresenter.__init__` (or its equivalent dependency-injection point) MUST accept
`alert_manager: AlertManager | None`. The instance MUST be stored as
`self._alert_manager`.

### FR-4 — RequestWorker Injection

`RequestWorker.__init__` MUST accept `alert_manager: AlertManager | None = None` and
pass it through to `RequestService`:

```python
self.service = RequestService(
    metrics=metrics,
    history_manager=history_manager,
    template_service=template_service,
    alert_manager=alert_manager,   # <-- new
)
```

### FR-5 — TabsPresenter Passes AlertManager to RequestWorker

Inside `TabsPresenter._handle_send_request()`, the `RequestWorker` constructor call
MUST include `alert_manager=self._alert_manager`.

### FR-6 — Graceful Degradation

If `AlertManager` is `None` at any point in the chain (e.g., in unit tests or when
config is absent), no exception MUST be raised. All existing behavior is preserved.

### FR-7 — No Duplicate Instantiation

Only one `AlertManager` instance is created per application run. It MUST NOT be
re-created per request or per worker.

---

## 4. Non-Functional Requirements

### NFR-1 — Backward Compatibility

All new parameters are optional with a `None` default. No existing call sites are broken.

### NFR-2 — Test Coverage

- `test_worker.py`: add tests asserting that `alert_manager` is forwarded to
  `RequestService` when provided, and remains `None` when omitted.
- `test_tabs_presenter.py` (or equivalent): add tests asserting that
  `_alert_manager` is passed to `RequestWorker` on request dispatch.
- All 17 existing `test_alert_manager.py` tests must continue to pass.

### NFR-3 — Code Style

- Follow `.cursor/lsr/do-python.md` rules.
- Max line length: 100 characters.
- UTF-8, LF line endings, no trailing whitespace.

---

## 5. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `AlertManager` is instantiated exactly once at application startup. |
| AC-2 | `RequestWorker.__init__` signature includes `alert_manager: AlertManager \| None = None`. |
| AC-3 | `RequestService` inside `RequestWorker` receives the injected `alert_manager`. |
| AC-4 | `TabsPresenter._handle_send_request()` passes `alert_manager=self._alert_manager` to `RequestWorker`. |
| AC-5 | When `alert_manager` is `None`, no exception is raised and existing behavior is unchanged. |
| AC-6 | New tests cover the injection path; all existing tests pass. |
| AC-7 | `_emit_exhaustion_alert()` fires in a live application run when retries are exhausted. |

---

## 6. Key Files

| File | Relevance |
|---|---|
| `pypost/main.py` | Bootstrap — create `AlertManager` here |
| `pypost/core/alert_manager.py` | `AlertManager` definition (lines 39-135) |
| `pypost/core/worker.py` | `RequestWorker` — add `alert_manager` param (lines 24-41) |
| `pypost/core/request_service.py` | Already accepts `alert_manager` (line 48) |
| `pypost/ui/presenters/tabs_presenter.py` | Creates `RequestWorker` (lines 348-374) |
| `tests/test_worker.py` | Extend with injection tests |
| `tests/test_alert_manager.py` | Must not regress (17 tests) |
| `tests/test_retry.py` | Must not regress (exhaustion alert tests) |

---

## 7. Dependencies

| Dependency | Status |
|---|---|
| PYPOST-420 (logger accumulation fix) | **Done** — commit `a397a18` |
| PYPOST-419 (retry policy) | Blocked on this issue |

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| MainWindow / presenter chain has many constructors | Add `alert_manager=None` defaults everywhere — no breakage |
| Config keys for alerts may not exist yet | Use safe `config_manager.get()` with fallbacks |
| Integration test may need a real `AlertManager` | Use existing context-manager support (`with AlertManager(...)`) |
