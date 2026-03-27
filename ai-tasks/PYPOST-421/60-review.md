# PYPOST-421: Technical Review (STEP 6)

**Task:** Reliable failure handling on HTTP retry exhaustion (scope of related PYPOST-402 finding).

---

## What was delivered

- **Production behavior:** `RequestService._execute_http_with_retry` no longer relies on a bare
  `assert` after retries are exhausted. Exhaustion after `ExecutionError` retries and after
  retryable HTTP status codes finalizes through `ExecutionError`, `_emit_exhaustion_alert`, and
  explicit `raise`, matching the architecture in `20-architecture.md`.
- **Control flow:** The `try` / `except` / `else` structure avoids double-handling when a
  retryable status exhausts on the last attempt; shared retry metrics and back-off run only when
  another attempt is possible.
- **Defensive path:** If the loop exits without return or raise (e.g. degenerate iteration),
  the code logs `retry_loop_invariant_failed` and raises `ExecutionError` with a stable message
  instead of relying on assertions or `raise None`.
- **Observability (STEP 5):** `retry_exhausted` logs include `detail` for correlation; the
  defensive path is observable at ERROR without changing primary exhaustion metrics semantics.
- **Tests:** `tests/test_retry.py` includes `TestRetryableStatusExhaustion` plus existing
  exhaustion and metrics/alert coverage for exception-based exhaustion.

Artifacts for earlier steps: `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`,
`50-observability.md`.

---

## Technical debt findings

**Release-blocking debt:** None identified for PYPOST-421. The change removes the unsafe
assertion-only contract and replaces it with explicit errors and logging.

**Minor / follow-up (non-blocking):**

- **Defensive path coverage:** There is no unit test that forces execution after the `for` loop
  to assert `retry_loop_invariant_failed` and the defensive `ExecutionError`. Under normal
  `RetryPolicy` usage (`max_retries` non-negative), that path should be unreachable; adding a
  targeted test would require contrived setup (e.g. invalid policy) or refactoring for
  injectability.
- **`RetryPolicy` validation:** `RetryPolicy` does not constrain `max_retries >= 0`. A negative
  value yields an empty `range(max_retries + 1)` and would hit the defensive path. Hardening the
  model (or request validation) would narrow this edge case; it is outside the minimal scope of
  PYPOST-421 unless product wants a separate hygiene task.
- **Repository-wide lint:** `40-code-cleanup.md` notes many pre-existing `flake8` findings
  outside the touched files. This is not introduced by PYPOST-421 and does not block this task.

---

## Risk assessment

| Area | Level | Notes |
| ---- | ----- | ----- |
| Success / non-retryable responses | Low | Early `return response` unchanged; tests cover common paths. |
| Cancellation | Low | `stop_flag` preserved; existing tests exercise cancellation. |
| Double metrics or alerts | Low | Exhaustion raises before shared retry metrics on final status attempt. |
| Defensive path in production | Low | Unlikely with valid policy; explicit `ExecutionError` + ERROR if hit. |
| Log volume | Low | Extra ERROR only on invariant failure; normal exhaustion unchanged. |

**Trade-offs accepted:** Slightly more branching in the retry loop for clarity and parity between
exception and status exhaustion; acceptable for maintainability and testability.

---

## Test adequacy assessment

**Strengths:**

- Exception exhaustion: error propagation, `retries_attempted` in `detail`, call counts, metrics,
  and `AlertManager.emit` behavior are covered.
- Status-code exhaustion: dedicated class asserts category, message (`HTTP <code>`), detail,
  metrics, and alerts for exhaustion after retryable statuses.
- Integration with `execute()`: tests use `RequestService.execute` and mocked `http_client`,
  matching real call patterns.

**Gaps (acceptable for this task):**

- No automated test for the post-loop defensive branch (see technical debt).
- End-to-end UI or multi-service tests are out of scope per requirements; unit coverage is
  appropriate for the stated scope.

Overall, test adequacy is **sufficient** for release of PYPOST-421 as a focused HTTP retry fix.

---

## Recommended follow-ups (optional)

1. Add a unit test or small refactor to cover the defensive post-loop path if compliance or
   coverage thresholds require every ERROR log line to be executed in tests.
2. Optionally add `Field(ge=0)` (or equivalent) on `RetryPolicy.max_retries` to prevent
   negative values and make the defensive path purely theoretical.
3. If product needs separate analytics for “status exhaustion” vs “exception exhaustion,”
   consider a follow-up task for an extra metric label or log field (`50-observability.md` noted
   this as optional).

---

## STEP 6 conclusion

- **Blockers for STEP 7:** None from this review.
- **Ready for:** User review of this document and roadmap checkpoint; then STEP 7 (developer
  documentation) per project process.
