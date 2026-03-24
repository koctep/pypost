# Requirements: PYPOST-402 — Add Retry and Alerting for Email Failures

## Jira Metadata

| Field       | Value                                                              |
|-------------|--------------------------------------------------------------------|
| Key         | PYPOST-402                                                         |
| Type        | Debt                                                               |
| Priority    | High                                                               |
| Status      | To Do                                                              |
| Labels      | high-priority, sprint-mar24                                        |
| Reporter    | Ilya Ashchepkov                                                    |
| Summary     | [HP] Add retry and alerting for email failures                     |
| Description | Implement retry strategy and operational alerts for failed outbound |
|             | email notifications in background jobs.                            |

---

## Context

PyPost is a desktop HTTP client built with PyQt. HTTP requests execute asynchronously
via `RequestWorker` (a `QThread`). The `RequestService` orchestrates execution with
structured error reporting (`ExecutionError` / `ErrorCategory`). Prometheus metrics
are exposed via `MetricsManager`.

"Email notifications" in this context refers to outbound HTTP requests targeting email
delivery services (e.g. webhooks, transactional email API calls). When these fail,
the worker currently surfaces a one-shot error signal with no retry and no durable
alerting.

---

## Goals

1. **Retry Strategy**: Automatically retry failed outbound HTTP requests for designated
   requests (e.g. requests tagged as email notification calls) before surfacing an error.
2. **Operational Alerting**: Emit structured alerts when email-notification requests
   exhaust all retries, making failures visible beyond the in-session UI.

---

## Functional Requirements

### FR-1: Retry Configuration per Request

- A request may carry an optional retry policy specifying:
  - `max_retries` (integer, default 0 — no retries)
  - `retry_delay_seconds` (float, default 1.0)
  - `retry_backoff_multiplier` (float, default 2.0 — exponential back-off)
  - `retryable_status_codes` (list of int, default `[429, 500, 502, 503, 504]`)
- Retry policy is stored alongside the existing request model / environment config
  so it can be persisted and loaded like other request settings.

### FR-2: Retry Execution in Background Worker

- `RequestWorker` (or a dedicated retry wrapper in `RequestService`) must:
  - Attempt the HTTP request.
  - On failure (network error, timeout, or HTTP status in `retryable_status_codes`),
    wait `retry_delay_seconds` (exponentially scaled) and retry up to `max_retries` times.
  - Emit a new signal `retry_attempt(attempt: int, max: int, error: ExecutionError)` so
    the UI can display live retry progress.
  - Honour the existing `stop()` cancellation: if the worker is stopped mid-retry, abort
    immediately without further attempts.
  - Record each retry attempt in the Prometheus metric `request_retries_total{method,
    status_category}`.

### FR-3: Exhaustion — Final Error

- When all retries are exhausted the worker emits the existing `error` signal with an
  `ExecutionError` whose `category` is `ErrorCategory.NETWORK` (or `TIMEOUT`) as
  appropriate.
- The error `detail` field must include `retries_attempted: N` so callers have full
  context.

### FR-4: Alerting on Retry Exhaustion

- When a request exhausts all retries, `MetricsManager` must increment a dedicated
  counter: `email_notification_failures_total{endpoint}`.
- Additionally, a configurable alert channel must be invoked:
  - **Default / MVP**: write a structured JSON alert entry to a rotating log file
    (`pypost-alerts.log`) in the application data directory.
  - **Stretch**: support sending an alert via an HTTP webhook (URL + optional auth
    header) configured in application settings.
- Alert payload fields:
  - `timestamp` (ISO-8601)
  - `request_name` (string)
  - `endpoint` (URL)
  - `retries_attempted` (int)
  - `final_error_category` (string)
  - `final_error_message` (string)

### FR-5: UI Feedback

- During retry, the existing status area in `tabs_presenter.py` should show:
  `"Retrying… (attempt N of M)"`.
- After exhaustion (or on final success following retries) the normal success/error
  display resumes.

### FR-6: Settings UI

- Application settings must expose retry policy fields (FR-1) and alert-webhook URL
  (FR-4 stretch) so users can configure them without editing files.

---

## Non-Functional Requirements

### NFR-1: Performance

- Retry waits must run on the worker thread, not the Qt event loop, to avoid blocking
  the GUI.
- Total wall-clock time added by retries must not exceed `max_retries * max_delay`
  (capped at 60 s per attempt).

### NFR-2: Testability

- Retry and alerting logic must be unit-testable without a live HTTP server:
  use dependency injection or mock-friendly seams.
- New tests must achieve ≥ 90 % branch coverage on retry/alerting code paths.

### NFR-3: Backward Compatibility

- Default `max_retries = 0` means existing behaviour is unchanged for requests that
  do not set a retry policy.
- Existing `ExecutionError`, `ErrorCategory`, and worker signals must not be renamed
  or removed.

### NFR-4: Observability

- All retry events must be emitted to existing Prometheus metrics infrastructure
  (`MetricsManager`) following the pattern established in PYPOST-400 / PYPOST-401.

---

## Out of Scope

- Sending alerts via SMTP directly from the application (the alert channel is HTTP
  webhook or log file only).
- Retry for MCP requests (`_execute_mcp`).
- Persistent job queue (e.g. Celery, RQ) — PyPost uses in-process `QThread` workers.

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | A request with `max_retries=3` retries up to 3 times on a 503 response before emitting `error`. |
| AC-2 | A `retry_attempt` signal is emitted for each retry with correct attempt number. |
| AC-3 | Cancelling the worker during a retry delay stops execution immediately (no further retries). |
| AC-4 | `request_retries_total` Prometheus counter increments on each retry attempt. |
| AC-5 | `email_notification_failures_total` Prometheus counter increments on retry exhaustion. |
| AC-6 | A JSON entry is appended to `pypost-alerts.log` on retry exhaustion. |
| AC-7 | A request with `max_retries=0` (default) behaves identically to current behaviour. |
| AC-8 | All new code paths have unit tests with ≥ 90 % branch coverage. |
| AC-9 | Settings UI exposes retry policy fields and saves/loads them correctly. |
