# PYPOST-733: Requirements

**Parent:** [PYPOST-687](https://pypost.atlassian.net/browse/PYPOST-687) R-P2-004

## Summary

Narrow broad `except Exception` handlers in persistence-layer modules so I/O, JSON, and HTTP
errors are caught explicitly and unexpected failures are logged with stack traces.

## Acceptance Criteria

1. `storage.py` — replace 7 broad catches with typed handlers (`OSError`, `json.JSONDecodeError`,
   `ValidationError`); retain one intentional broad catch in `deserialize_environment_records`
   with `logger.exception`.
2. `alert_manager.py` — replace 4 broad catches: `OSError` for handler close, typed
   `requests` exceptions for webhook delivery.
3. `request_manager.py` — verified: no `except Exception`; document in tech-debt (no code change).
4. Add tests for corrupt JSON and file-level error paths where missing.
5. `make check` passes.

## Out of Scope

- Refactoring other modules with broad catches outside the three persistence layers.
- Switching `alert_manager` from `requests` to `httpx`.
