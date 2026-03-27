# PYPOST-421: Developer documentation (STEP 7)

Task-specific notes for maintainers. Related artifacts: `10-requirements.md`,
`20-architecture.md`, `50-observability.md`, `60-review.md`.

## What changed for developers

- **Primary module:** `pypost/core/request_service.py`, method
  `RequestService._execute_http_with_retry`.
- **Removed unsafe contract:** Retry exhaustion no longer relies on a bare `assert` after the
  retry loop. Final failure is always an explicit `ExecutionError` path.
- **Parity of exhaustion paths:**
  - **Retryable `ExecutionError` from `http_client.send_request`:** On the last allowed attempt,
    the code sets `detail` (including `retries_attempted`), calls `_emit_exhaustion_alert`, then
    re-raises the error.
  - **Retryable HTTP status codes:** On the last attempt, the code builds an
    `ExecutionError`, calls `_emit_exhaustion_alert`, then raises—same alert/metrics funnel as
    the exception path.
- **Control flow:** `try` / `except ExecutionError` / `else` separates HTTP response handling from
  exception handling so retryable status exhaustion on the final attempt is not double-handled
  and does not run the shared “another retry” block (metrics + back-off) after exhaustion.
- **Defensive branch:** If the `for` loop exits without returning or raising (e.g. degenerate
  iteration), the code logs `retry_loop_invariant_failed` at **ERROR** and raises
  `ExecutionError` with a stable message instead of relying on assertions.

## How retry exhaustion behaves

1. **Successful or non-retryable outcome:** Unchanged—early `return response` when the status is
   not in `retryable_status_codes`.
2. **Retries remain:** For both exception and retryable-status paths, if `attempt < max_retries`,
   the code logs `retryable_error` or `retryable_status`, records `last_error`, increments
   `request_retries_total` via `track_retry_attempt` (when metrics are configured), invokes
   `retry_callback` if provided, then applies exponential back-off (subject to cancellation).
3. **Exhaustion (last attempt):** No further `track_retry_attempt` for that failure: exhaustion
   raises immediately after `_emit_exhaustion_alert` (see observability below).
4. **Cancellation:** `stop_flag` checks before each attempt and during back-off are unchanged;
   cancellation still raises `ExecutionError` with the existing messages.
5. **`execute()` surface:** Failures propagate as `ExecutionError`; `execute()` continues to log
   structured execution failure for those errors (see `50-observability.md`).

## Test commands relevant to this task

From the repository root (see `Makefile` for the full test target):

- **Focused (recommended for this task):**
  - `python -m pytest tests/test_retry.py tests/test_request_service.py -q`
  - Or with `uv` if that is your workflow:
    `uv run --with pytest python -m pytest tests/test_retry.py tests/test_request_service.py -q`
- **Lint (touched production module):**
  - `python -m flake8 pypost/core/request_service.py`
  - Or: `uv run --with flake8 --with pytest python -m flake8 pypost/core/request_service.py`
- **Full suite:** `make test` or `QT_QPA_PLATFORM=offscreen python -m pytest tests/` (as in
  `Makefile`).

**Notable tests:** `TestRetryableStatusExhaustion` in `tests/test_retry.py` covers retryable HTTP
status exhaustion; other classes in the same file cover exception exhaustion, alerts, metrics, and
callbacks.

## Observability notes for developers

- **WARNING `retry_exhausted`:** Emitted inside `_emit_exhaustion_alert` once per exhaustion;
  includes `detail=%s` (`ExecutionError.detail`) for correlation with attempt counts without
  logging large bodies.
- **ERROR `retry_loop_invariant_failed`:** Only if the post-loop defensive path runs; should not
  occur with normal non-negative `max_retries` and expected loop structure.
- **ERROR `request_execution_failed`:** Logged in `execute()` when an `ExecutionError` surfaces;
  having **WARNING** `retry_exhausted` followed by **ERROR** `request_execution_failed` is
  intentional (alert path vs. user-visible failure recording).
- **Metrics:** On exhaustion, `track_email_notification_failure` runs once inside
  `_emit_exhaustion_alert`; `track_request_error` is applied when `execute()` handles the error;
  `track_retry_attempt` is not duplicated on the final exhausted attempt. See
  `50-observability.md` and `pypost/core/metrics.py` for counter names and semantics.

## Troubleshooting

- **Suspect double metrics or duplicate alerts:** Confirm exhaustion paths raise before the shared
  block that calls `track_retry_attempt` and back-off (see `_execute_http_with_retry` structure).
- **Unexpected `retry_loop_invariant_failed`:** Investigate `RetryPolicy.max_retries` and loop
  inputs; negative `max_retries` can yield an empty range (see non-blocking notes in
  `60-review.md`).
