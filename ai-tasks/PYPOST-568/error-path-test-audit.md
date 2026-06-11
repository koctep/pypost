# Error-path test audit (PYPOST-568)

Analysis of tests that emit **ERROR** logs while still **PASSED**. Source: PYPOST-567
inventory (`inventory.csv`).

## Summary

| Risk | Count | Meaning |
| --- | ---: | --- |
| **Low** | 12 | Strong assertions on signals/UI mocks; log is side effect only |
| **Medium** | 2 | Assertions OK but no `caplog`; regression could match log noise |
| **High** | 0 | Weak assertions that could pass if handler breaks silently |

**Verdict:** No high-risk false positives in worker/presenter ERROR paths. Main issue is
**log noise** masking real ERRORs in CI output, not weak tests.

## Worker (`pypost.core.worker`)

| Test | ERROR log | Assertions | Risk | Mitigation |
| --- | --- | --- | --- | --- |
| `test_worker_wraps_unexpected_exception_as_execution_error_unknown` | `RequestWorker unexpected error: boom` + traceback | `error` signal → `ExecutionError`, category `UNKNOWN` | **Low** | `caplog.at_level(ERROR)` + assert 1 record; or `patch.object(logger, "error")` |

The test correctly verifies the `error` signal. The ERROR log is expected side effect of
`worker.run()` exception handler. A regression that stopped emitting the signal would **fail**.

## Tabs presenter (`pypost.ui.presenters.tabs_presenter`)

All six ERROR lines come from `TestOnRequestError` calling `_on_request_error` directly.

| Test | ERROR log pattern | Assertions | Risk |
| --- | --- | --- | --- |
| `test_execution_error_body_shows_category_message` | BODY / YAML→JSON | `show_request_error` called; message contains category text + detail | **Low** |
| `test_execution_error_network_shows_category_message` | NETWORK | dialog text contains "server is running" | **Low** |
| `test_execution_error_timeout_shows_timeout_message` | TIMEOUT | dialog contains "timed out" | **Medium** — no `assert_called_once` | 
| `test_execution_error_detail_substring_not_treated_as_cancelled` | NETWORK + "cancelled" in detail | `show_request_error` called once | **Low** |
| `test_execution_error_message_does_not_expose_raw_detail_for_network` | NETWORK | raw detail **not** in dialog args | **Low** |
| `test_str_error_shows_dialog` | str error | `show_request_failed_error` called | **Low** |

**Note:** `test_execution_error_timeout_shows_timeout_message` checks dialog args but omits
`assert_called_once()` — add for consistency (low effort, not a false-positive risk).

Logger call is **before** dialog mock; ERROR always appears even when dialog is mocked.

## Collection tree actions

| Test | Level | Assertions | Risk |
| --- | --- | --- | --- |
| `test_collection_delete_error_records_error_metric` | ERROR | metrics `error` label | **Low** |
| `test_delete_error_does_not_emit_succeeded_metric` | ERROR | succeeded metric absent | **Low** |
| `test_request_delete_error_records_error_metric` | ERROR | metrics | **Low** |

## Retry / YAML body (`test_retry.py`)

YAML conversion errors appear in **request_service** WARNING/ERROR logs during retry tests,
not tabs_presenter. Tests assert retry counts, alerts, and `ExecutionError` categories —
**Low** risk; noise only.

## Recommendations (implementation follow-ups)

1. **PYPOST-571:** Add CI allowlist for known ERROR message prefixes from this audit.
2. **Optional fix tasks:**
   - Wrap worker exception test with `caplog.at_level(logging.ERROR)`.
   - Add `assert_called_once()` to timeout presenter test.
   - Consider `logger.error` → `logger.debug` for expected-path logging in production
     (product decision — out of scope for analysis-only epic).

## False-positive scenario analysis

Could a broken `_on_request_error` still pass?

- If handler becomes no-op: tests patching `show_request_error` would **fail** (not called).
- If wrong category message: string assertions would **fail**.
- If worker stops emitting `error` signal: worker test would **fail**.

Log output alone is **not** used as pass criterion — pytest outcome is independent.
