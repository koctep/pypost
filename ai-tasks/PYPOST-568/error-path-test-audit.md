# Error-path test audit (PYPOST-568)

Baseline: [PYPOST-567](../PYPOST-567/inventory.csv) capture (2026-06-11, 937 passed, 72 ERROR).

Scope: four focus modules — **22 ERROR lines** total.

## Summary

| Module | Tests with ERROR | Risk: low | medium | high |
| --- | ---: | ---: | ---: | ---: |
| `tests/test_worker.py` | 1 | 1 | 0 | 0 |
| `tests/test_collection_tree_delete_metrics.py` | 3 | 3 | 0 | 0 |
| `tests/test_tabs_presenter.py` | 6 | 6 | 0 | 0 |
| `tests/test_retry.py` | 12 | 10 | 2 | 0 |
| **Total** | **22** | **20** | **2** | **0** |

**Verdict:** All audited tests deliberately trigger failure paths. None are high-risk false
positives. Two retry tests are **medium** because `request_execution_failed` ERROR is
expected but not asserted via `caplog`; behavioral assertions remain strong.

Recommended default for PYPOST-571 allowlist: tag all 22 test node ids under their logger
groups as **expected error-path**.

---

## `tests/test_worker.py`

Production site: `pypost/core/worker.py` — `logger.error("RequestWorker unexpected error: …")`
in the bare `except Exception` handler before emitting `ExecutionError(UNKNOWN)`.

| Test | Logger / message | Risk | Assertion strength | Mitigation |
| --- | --- | --- | --- | --- |
| `TestRequestWorkerError::test_worker_wraps_unexpected_exception_as_execution_error_unknown` | `pypost.core.worker` — `RequestWorker unexpected error: boom` | **low** | **strong** — patches `execute` to raise `RuntimeError`, asserts `error` signal with `ExecutionError` category `UNKNOWN` | **Document-only** for allowlist. Optional: `caplog.at_level(ERROR)` asserting message prefix. Do not downgrade production log — genuine unexpected errors should stay ERROR. |

Other worker tests (`cancelled`, `finished-on-error`, retry signal) emit DEBUG/INFO only or
no ERROR — out of scope.

---

## `tests/test_collection_tree_delete_metrics.py`

Production site: `pypost/ui/presenters/collection_tree_actions.py` —
`collection_item_delete_failed item_type=… item_id=… error=…` before `show_delete_failure`.

| Test | Logger / message | Risk | Assertion strength | Mitigation |
| --- | --- | --- | --- | --- |
| `TestCollectionTreeDeleteMetrics::test_collection_delete_error_records_error_metric` | `collection_item_delete_failed` — `error=disk full` | **low** | **strong** — mocks dialog; asserts `track_gui_collection_delete_action("collection", "error")` and tree model unchanged | Allowlist + optional `caplog` assert on `collection_item_delete_failed`. |
| `TestCollectionTreeDeleteMetrics::test_delete_error_does_not_emit_succeeded_metric` | `collection_item_delete_failed` — `error=boom` | **low** | **strong** — asserts only `error` metric, not `succeeded` | Same as above. |
| `TestCollectionTreeDeleteMetrics::test_request_delete_error_records_error_metric` | `collection_item_delete_failed` — `error=permission denied` | **low** | **strong** — asserts `track_gui_collection_delete_action("request", "error")` and child row count | Same as above. |

Related WARNING-only tests (`delete_not_found` → `collection_item_delete_not_found`) are
intentional not-found paths — not ERROR inventory rows.

---

## `tests/test_tabs_presenter.py` (`TestOnRequestError`)

Production site: `pypost/ui/presenters/tabs_presenter.py` — `_on_request_error` logs
`request_error error_msg=…` (str path) or `request_error category=… message=… detail=…`
(ExecutionError path) before showing dialog helpers.

| Test | Logger / message | Risk | Assertion strength | Mitigation |
| --- | --- | --- | --- | --- |
| `TestOnRequestError::test_str_error_shows_dialog` | `request_error error_msg=connection refused` | **low** | **strong** — mocks `show_request_failed_error`, asserts called once | Allowlist; optional `caplog` on `request_error error_msg`. |
| `TestOnRequestError::test_execution_error_network_shows_category_message` | `request_error category=NETWORK …` | **low** | **strong** — mocks `show_request_error`, asserts user message contains "server is running" | Allowlist. |
| `TestOnRequestError::test_execution_error_body_shows_category_message` | `request_error category=BODY …` | **low** | **strong** — asserts YAML conversion message and detail in dialog args | Allowlist. |
| `TestOnRequestError::test_execution_error_timeout_shows_timeout_message` | `request_error category=TIMEOUT …` | **low** | **moderate** — asserts dialog args contain "timed out" (single substring check) | Allowlist; optional strengthen with `assert_called_once`. |
| `TestOnRequestError::test_execution_error_detail_substring_not_treated_as_cancelled` | `request_error category=NETWORK … detail=operation cancelled by upstream proxy` | **low** | **strong** — regression guard; asserts dialog shown despite "cancelled" in detail | Allowlist. |
| `TestOnRequestError::test_execution_error_message_does_not_expose_raw_detail_for_network` | `request_error category=NETWORK …` (raw HTTPS pool detail) | **low** | **strong** — asserts raw detail **not** in user-facing message | Allowlist. |

Cancellation tests (`test_str_cancellation_message_no_dialog`, `test_execution_error_cancelled_no_dialog`)
log INFO only — not in ERROR inventory.

---

## `tests/test_retry.py`

Production site: `pypost/core/request_service.py` —
`request_execution_failed method=… url=… category=… detail=…` when `ExecutionError` is
returned from the HTTP retry loop (exhaustion, body errors, cancellation).

### Exhaustion and alert tests (NETWORK category)

| Test | Logger / message | Risk | Assertion strength | Mitigation |
| --- | --- | --- | --- | --- |
| `TestRetryOnException::test_detail_contains_retries_attempted_on_exhaustion` | `request_execution_failed` NETWORK, `retries_attempted: 2` | **medium** | **moderate** — asserts `execution_error.detail` substring only | Allowlist; add `caplog` assert for `request_execution_failed` when tightening. |
| `TestRetryOnException::test_exhausted_exception_retries_returns_execution_result_with_error` | `request_execution_failed` NETWORK | **medium** | **strong** — category NETWORK, call count 3 | Allowlist; optional `caplog`. |
| `TestExhaustionAlert::test_alert_manager_emit_called_on_exhaustion` | `request_execution_failed` NETWORK | **low** | **strong** — full alert payload assertions | Allowlist. |
| `TestExhaustionAlert::test_no_alert_manager_does_not_raise_on_exhaustion` | `request_execution_failed` NETWORK | **low** | **moderate** — asserts `execution_error` present, no raise | Allowlist. |
| `TestExhaustionAlert::test_track_request_retry_exhaustion_called_on_exhaustion` | `request_execution_failed` NETWORK | **low** | **strong** — metrics exhaustion called | Allowlist. |
| `TestRetryableStatusExhaustion::test_alert_manager_emit_on_status_exhaustion` | `request_execution_failed` NETWORK, HTTP 503 | **low** | **strong** — alert payload with `retries_attempted: 0` | Allowlist. |
| `TestRetryableStatusExhaustion::test_detail_contains_retries_attempted_on_status_exhaustion` | `request_execution_failed` NETWORK | **low** | **moderate** — detail substring | Allowlist; optional `caplog`. |
| `TestRetryableStatusExhaustion::test_exhausted_status_retries_returns_execution_error` | `request_execution_failed` NETWORK, HTTP 503 | **low** | **strong** — category, message, call count | Allowlist. |
| `TestRetryableStatusExhaustion::test_track_request_retry_exhaustion_on_status_exhaustion` | `request_execution_failed` NETWORK, HTTP 502 | **low** | **strong** — metrics exhaustion | Allowlist. |

### Cancellation and body-error tests

| Test | Logger / message | Risk | Assertion strength | Mitigation |
| --- | --- | --- | --- | --- |
| `TestStopFlagDuringRetry::test_stop_flag_cancels_retry` | `request_execution_failed` **CANCELLED** | **low** | **strong** — category CANCELLED, stop_flag called | Allowlist; note CANCELLED ERROR is intentional (differs from worker cancel DEBUG path). |
| `TestBodyErrorNonRetryable::test_body_error_not_retried` | `request_execution_failed` **BODY** | **low** | **strong** — category BODY, single HTTP call | Allowlist. |
| `TestBodyErrorNonRetryable::test_body_error_no_retry_metrics` | `request_execution_failed` **BODY** | **low** | **strong** — `track_retry_attempt` not called | Allowlist. |

Retry tests that succeed after retries (503 → 200) emit WARNING (`retryable_status`) only —
not ERROR inventory rows.

---

## Cross-cutting recommendations

1. **PYPOST-571 allowlist** — Register all 22 test node ids as expected ERROR emitters grouped
   by logger (`pypost.core.worker`, `pypost.ui.presenters.tabs_presenter`,
   `pypost.ui.presenters.collection_tree_actions`, `pypost.core.request_service`).
2. **Optional caplog hardening** — Priority: the two **medium** retry exhaustion tests and
   delete-metric tests (ties log emission to metric assertions explicitly).
3. **No production log changes** — ERROR level is correct for these failure paths; the problem
   is test-run visibility under `log_cli_level = WARNING`, not mis-leveled production logs.
4. **Focused regression command** — Already documented in `doc/dev/testing.md` (PYPOST-400
   surface); re-run after any retry/worker/presenter changes.

## Focused verification

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_worker.py \
  tests/test_tabs_presenter.py::TestOnRequestError \
  tests/test_collection_tree_delete_metrics.py \
  tests/test_retry.py \
  -v --tb=short 2>&1 | grep ERROR
```

Expect ERROR lines matching inventory patterns while tests pass.
