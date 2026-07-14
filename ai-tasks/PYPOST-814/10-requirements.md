# PYPOST-814: Align ExecuteRequestProtocol with RequestService

## Summary

Follow-up from [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734) baseline triage
(R-P2-005b). Mypy reported protocol mismatches when `RequestService` was assigned to
`ExecuteRequestProtocol` in `RequestWorker` and `MCPServerImpl`, plus an implicit Optional on
`RequestWorker.variables`. Harmonize the protocol contract with the implementation so structural
typing checks pass without `# type: ignore`.

## Acceptance Criteria

1. `RequestService.execute` signature matches `ExecuteRequestProtocol.execute` (optional
   parameters use explicit `| None`; completed in PYPOST-813).
2. `RequestWorker.__init__` optional `variables` parameter uses explicit `| None`.
3. Baseline entries removed for:
   - `pypost/core/qt/worker.py` (assignment on `variables` and protocol assignment)
   - `pypost/core/mcp_server_impl.py` (return-value on `_create_request_service`)
4. `mypy-baseline.json` `error_count` updated (42 → 41).
5. `make typecheck` and `make check` pass.
6. `doc/dev/static_type_checking.md` reflects the new baseline count when it changes.

## Out of Scope

- Remaining baseline errors (union-attr, var-annotated in `request_service.py`).
- Type-checking `pypost/ui/` (PYPOST-815).
- Changing runtime behavior of request execution.

## User Stories

- As a **maintainer**, I want `RequestService` to satisfy `ExecuteRequestProtocol` structurally,
  so workers and MCP inbound paths type-check without workarounds.
- As a **reviewer**, I want the baseline count reduced after protocol alignment, so debt
  shrinkage is visible.
