# PYPOST-813: Fix implicit Optional defaults (R-P2-005a)

## Summary

Follow-up from [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734) baseline triage
(R-P2-005a). Eight mypy `assignment` errors came from optional parameters annotated with a
concrete type but defaulting to `None` (`no_implicit_optional` in `[tool.mypy]`). Align
implementations with existing protocol signatures.

## Acceptance Criteria

1. `HTTPClient.send_request` optional parameters use explicit `| None` types matching
   `HTTPClientProtocol`.
2. `RequestService.execute` optional parameters use explicit `| None` types matching
   `ExecuteRequestProtocol`.
3. Eight `assignment` baseline entries for `http_client.py` and `request_service.py` are
   removed; `mypy-baseline.json` `error_count` updated.
4. `make typecheck` and `make check` pass.
5. `doc/dev/static_type_checking.md` reflects the new baseline count when it changes.

## Out of Scope

- Fixing remaining baseline errors (union-attr, var-annotated in `request_service.py`).
- `ExecuteRequestProtocol` alignment in `worker.py` / `mcp_server_impl.py` (PYPOST-814).
- Type-checking `pypost/ui/` (PYPOST-815).

## User Stories

- As a **maintainer**, I want optional callback parameters typed as `T | None`, so mypy and
  protocols agree without implicit-optional warnings.
- As a **reviewer**, I want the baseline count reduced after intentional fixes, so debt
  shrinkage is visible.
