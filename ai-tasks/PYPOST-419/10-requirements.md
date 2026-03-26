# PYPOST-419 — Requirements

## Summary

`AppSettings.default_retry_policy` is persisted (serialised to / deserialised from disk via
`config_manager.py`) and editable via the Settings dialog, but `RequestService` never reads it
at runtime. Any request that lacks a per-request `retry_policy` silently falls back to
`max_retries=0`, making the user-facing default retry configuration completely inert.

## Background / Context

- **Parent epic**: PYPOST-402 — AlertManager / retry-wiring group.
- **Execution order in sprint**: PYPOST-420 (logger fix) → PYPOST-418 (AlertManager DI) →
  **PYPOST-419** (retry policy wiring). Both upstream issues are now closed.
- **Priority**: High (tech-debt item flagged as RISK-2 carry-forward from Sprint 134).

## Affected Components

| File | Role |
|------|------|
| `pypost/models/retry.py` | `RetryPolicy` Pydantic model |
| `pypost/models/settings.py` | `AppSettings` — contains `default_retry_policy: Optional[RetryPolicy]` |
| `pypost/core/config_manager.py` | Loads/saves `AppSettings` from `~/.config/pypost/settings.json` |
| `pypost/core/request_service.py` | `_execute_http_with_retry()` — retry logic lives here |
| `pypost/core/worker.py` | `RequestWorker` — owns `RequestService`, receives `AppSettings` indirectly |
| `pypost/ui/dialogs/settings_dialog.py` | UI for editing `default_retry_policy` |

## Current Behaviour

1. User sets a `default_retry_policy` in the Settings dialog (max retries, delay, backoff, status
   codes).
2. `SettingsDialog` saves the policy back into `AppSettings` and `ConfigManager` persists it to
   disk.
3. On the next request, `RequestService._execute_http_with_retry()` checks
   `request.retry_policy`. If that field is `None` (no per-request override), it falls back to
   hardcoded defaults (`max_retries=0`, `delay=1.0`, `multiplier=2.0`) — it never consults
   `AppSettings.default_retry_policy`.
4. The retry feature is therefore silently inactive for all requests that do not carry an
   explicit per-request policy.

## Required Behaviour

1. `RequestService` (or its call-site in `RequestWorker`) must receive the current
   `AppSettings.default_retry_policy` at construction time or per-execute call.
2. When `request.retry_policy` is `None`, the service must use `AppSettings.default_retry_policy`
   as the fallback (if it is also set).
3. When both are `None`, the existing hardcoded safe defaults (`max_retries=0`) continue to
   apply — no change in observable behaviour for users who have never configured the setting.
4. The policy resolution precedence is:
   ```
   per-request retry_policy > AppSettings.default_retry_policy > hardcoded defaults
   ```
5. No change to the persistence path, the Settings dialog, or the `RetryPolicy` model itself.

## Functional Requirements

### FR-1 — Policy injection into RequestService

`RequestService` must accept `AppSettings` (or `Optional[RetryPolicy]`) so the
`_execute_http_with_retry()` method can use it as a fallback.

### FR-2 — Policy resolution order

`_execute_http_with_retry()` must resolve the active retry policy in this priority order:

1. `request.retry_policy` (per-request, highest priority)
2. `AppSettings.default_retry_policy` (user default)
3. Hardcoded inline defaults (lowest priority, unchanged)

### FR-3 — RequestWorker wiring

`RequestWorker` must pass the loaded `AppSettings.default_retry_policy` (or the full
`AppSettings` instance) to `RequestService` during construction or each `execute()` call, so the
correct policy is available without requiring a global settings lookup inside the service layer.

### FR-4 — No silent degradation

If `AppSettings.default_retry_policy` is set and `request.retry_policy` is `None`, the request
MUST use the application-level default. Logging or metrics that already record retry attempts
must remain accurate.

### FR-5 — Backward compatibility

- Existing serialised `settings.json` files that omit `default_retry_policy` must continue to
  load cleanly (Pydantic defaults to `None`; no migration needed).
- Requests that already carry an explicit `retry_policy` must be unaffected.

## Non-Functional Requirements

- **No new public API surface** beyond what is strictly needed to thread the settings value
  through the DI chain.
- **No UI changes** — the Settings dialog already handles this correctly.
- **Test coverage**: Unit tests must verify all three policy-resolution branches (per-request
  wins, default used, hardcoded fallback used).

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | A request with `retry_policy=None` and `AppSettings.default_retry_policy` set to `RetryPolicy(max_retries=3)` retries up to 3 times on a retryable status code. |
| AC-2 | A request with an explicit `retry_policy=RetryPolicy(max_retries=1)` ignores `AppSettings.default_retry_policy` and retries at most once. |
| AC-3 | A request with `retry_policy=None` and `AppSettings.default_retry_policy=None` behaves exactly as before (max_retries=0, no retries). |
| AC-4 | Existing unit tests for `RequestService` pass without modification (no regressions). |
| AC-5 | `ConfigManager.load_config()` on an old `settings.json` without `default_retry_policy` returns `AppSettings` with `default_retry_policy=None` (no error). |

## Out of Scope

- Changing the `RetryPolicy` model schema.
- Adding per-environment retry policies.
- UI changes to `SettingsDialog`.
- Changing how `AppSettings` is persisted.
