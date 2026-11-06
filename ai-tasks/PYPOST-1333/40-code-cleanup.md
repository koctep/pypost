# PYPOST-1333: Code Cleanup Report

## Linter Fixes

- `flake8` on changed production modules (`pypost/core/http_client.py`,
  `pypost/core/request_service.py`): clean.
- Full `make lint` still fails on pre-existing
  `tests/test_mcp_server_registry.py:308` E501 via `lint-tests` baseline check —
  unrelated to this task (documented in Step 7).

## Formatting

- Line length kept ≤ 100 characters on changed Python.
- No formatter-only churn outside the touched paths.

## Code Cleanup

- Reused existing `_error_log_url` / `sanitize_text`; no duplicate sanitizer helpers
  beyond a small `_log_safe_error_message` wrapper in `request_service`.
- Timeout / connection paths compute `safe_url` once for both the ERROR log and the
  `ExecutionError.message`.
- No debug prints, commented-out code, or unused imports introduced.

## Quality Check

- Focused suite green:
  `TestHTTPClientErrorLogging`, `TestHTTPClientSSEStreamLogging`,
  `TestHTTPClientResponseBodyCap::test_truncation_warning_logs_redacted_resolved_url`,
  `TestRetryLogSanitization`, `TestExhaustionAlert`.
- New tests inherit module `pytestmark = pytest.mark.timeout(...)` (60s /
  30s).

## Remaining Issues

- Pre-existing `make lint` / `lint-tests` failure on
  `tests/test_mcp_server_registry.py` (E501) — out of scope; see
  `60-tech-debt.md`.
