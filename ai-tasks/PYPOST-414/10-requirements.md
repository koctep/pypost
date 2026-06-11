# PYPOST-414: Pre-existing test failures not addressed (PYPOST-400 follow-up)

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Close the tech-debt item deferred from PYPOST-400 review (TD-6): ensure the test suite is
green for failures introduced or exposed by the PYPOST-400 worker/error-handling work and
related DI changes (PYPOST-378).

## Problem statement

PYPOST-400 shipped with known failing tests:

1. Three `test_http_client_sse_probe.py` tests — `HTTPClient()` without `TemplateService`
   caused `AttributeError` on `render_string`.
2. `test_history_manager.py` — async save thread raced `TemporaryDirectory` cleanup
   (`OSError: Directory not empty`), including flaky `test_concurrent_appends`.

These were tracked as out-of-scope in PYPOST-400 and filed as PYPOST-414.

## User stories

- As a **developer merging PYPOST-400 follow-ups**, I want `pytest tests/` green so CI is
  trustworthy.
- As a **maintainer**, I want deterministic history-manager teardown without `time.sleep`
  hacks in every test.

## Functional requirements

- **FR-1:** All SSE probe tests pass with proper `TemplateService` injection (or production
  default).
- **FR-2:** History manager tests synchronize async saves before temp-dir teardown.
- **FR-3:** PYPOST-400 worker/error-handling tests (`test_worker`, `test_retry`,
  `TestOnRequestError`) remain passing.

## Non-functional requirements

- **NFR-1:** Prefer explicit `HistoryManager.flush()` over arbitrary sleeps.
- **NFR-2:** No regression to `HTTPClient` callers that already inject `TemplateService`.

## Out of scope

- New PYPOST-400 feature work (error categories, presenter messaging).
- Full-suite performance or timeout-marker enforcement (separate backlog).

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | `tests/test_http_client_sse_probe.py` — 3/3 pass |
| AC-2 | `tests/test_history_manager.py` — all pass, no tmpdir race |
| AC-3 | `tests/test_worker.py`, `tests/test_retry.py`, `TestOnRequestError` pass |
| AC-4 | Targeted and full `make test` verification documented |

## References

- PYPOST-400 `60-review.md` TD-6
- PYPOST-403 `afd2a58` — original fix commit
