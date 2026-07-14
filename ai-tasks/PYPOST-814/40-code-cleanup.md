# PYPOST-814: Code Cleanup

## Changes

| File | Change |
| --- | --- |
| `pypost/core/qt/worker.py` | `__init__`: `variables: dict \| None = None` |
| `mypy-baseline.json` | Removed `worker.py:42:assignment`; `error_count` 42 → 41 |

## Verification

- [x] `make typecheck` — pass (baseline match, 41 errors)
- [x] `make check` — pass (lint + tests)
- [x] No runtime logic changes
- [x] `RequestService` structurally satisfies `ExecuteRequestProtocol`
- [x] `MCPServerImpl._create_request_service` return type clean

## Checklist

- [x] Line length ≤ 100
- [x] UTF-8, LF endings
- [x] English comments and docs
- [x] Minimal diff — one annotation + baseline refresh
