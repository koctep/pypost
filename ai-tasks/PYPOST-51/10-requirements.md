# PYPOST-51: Add ExecuteRequestProtocol for request execution

## Summary

From PYPOST-40 audit R9. Introduce `ExecuteRequestProtocol` so consumers that only call
`execute()` depend on a narrow contract instead of the concrete `RequestService` class.
Enables test doubles and future execution backends (e.g. alternate MCP/gRPC paths) without
changing worker or MCP server code.

## Goals

- Define a structural protocol covering the `execute` surface used by `RequestWorker` and
  `MCPServerImpl`.
- Type execution consumers against `ExecuteRequestProtocol`.
- Keep `RequestService` as the production implementation and composition-root default.
- Preserve runtime behavior — no functional changes.

## User Stories

- As a developer, I want `RequestWorker` to depend on an execution interface so unit tests can
  substitute `MagicMock(spec=ExecuteRequestProtocol)` without constructing full services.
- As a maintainer, I want SOLID audit R9 closed so P3 execution abstraction debt is resolved.

## Scope

### In Scope

| Area | Expected Result |
| --- | --- |
| Protocol definition | `ExecuteRequestProtocol` mirrors `RequestService.execute` |
| Consumer type hints | `RequestWorker.service`, `MCPServerImpl._create_request_service` return type |
| Test seam | `RequestService` satisfies protocol; protocol compliance tests |
| Documentation | `testability.md`, audit follow-up status |

### Out of Scope

- `RequestWorker` constructor injection of executor ([PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379)).
- Moving `ExecutionResult` to a shared types module.
- New execution backends beyond existing `RequestService`.

## Acceptance Criteria

- `ExecuteRequestProtocol` is `@runtime_checkable` and documents the `execute` API.
- `RequestWorker` and `MCPServerImpl` type-hint against `ExecuteRequestProtocol`.
- `RequestService` passes `isinstance(..., ExecuteRequestProtocol)`.
- Existing request execution tests pass without behavior changes.

## References

- PYPOST-40 audit R9
- `HTTPClientProtocol` pattern (PYPOST-46)
