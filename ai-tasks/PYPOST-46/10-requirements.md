# PYPOST-46: Introduce HTTPClient protocol and inject into RequestService

## Goals

From PYPOST-40 audit R4: decouple `RequestService` from the concrete `HTTPClient` class so
tests and future transports can substitute a mock or alternate implementation without
subclassing.

## User Stories

- As a maintainer, I want `RequestService` to depend on an HTTP interface so unit tests can
  inject `MagicMock(spec=HTTPClientProtocol)` without network I/O.
- As a maintainer, I want the production default to remain `HTTPClient` when nothing is injected.

## Acceptance Criteria

- [x] `HTTPClientProtocol` defines the `send_request` surface used by `RequestService`.
- [x] `RequestService.__init__` accepts `http_client: HTTPClientProtocol | None`.
- [x] Default construction still creates `HTTPClient` with metrics and template service.
- [x] `HTTPClient` satisfies `HTTPClientProtocol` at runtime (`isinstance` check).
- [x] Tests document protocol compliance and mock substitution.

## Out of Scope

- MCP client protocol (separate ticket).
- `RequestWorker` accepting `RequestService` injection ([PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379)).
- Moving `HTTPRequestResult` / `ResolvedRequestFields` to a shared types module.
