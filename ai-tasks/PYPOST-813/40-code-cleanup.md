# PYPOST-813: Code Cleanup

## Changes

| File | Change |
| --- | --- |
| `pypost/core/http_client.py` | `send_request`: four optional params annotated with `\| None` |
| `pypost/core/request_service.py` | `execute`: four optional params annotated with `\| None` |
| `mypy-baseline.json` | Removed 12 resolved signatures; `error_count` 54 → 42 |

## Verification

- [x] `make typecheck` — pass (baseline match)
- [x] `make check` — pass (lint + 1617 tests)
- [x] No runtime logic changes
- [x] Signatures match `HTTPClientProtocol` and `ExecuteRequestProtocol`

## Checklist

- [x] Line length ≤ 100
- [x] UTF-8, LF endings
- [x] English comments and docs
- [x] Minimal diff — annotations only
