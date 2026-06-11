# PYPOST-414: Observability

## Scope

No new logging or metrics in PYPOST-414.

## Related observability (PYPOST-403)

Already present from the fix commit:

| Location | Event |
|----------|-------|
| `history_manager.py` | `history_cap_enforced` WARNING |
| `history_manager.py` | `flush` lifecycle DEBUG |
| `http_client.py` | `sse_probe_detected` DEBUG |

## Verification

PYPOST-400 error-path tests assert metrics behavior (`test_retry.py::TestRetryMetrics`,
`TestExhaustionAlert`) — all pass in targeted run.
