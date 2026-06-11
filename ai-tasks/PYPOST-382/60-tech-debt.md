# PYPOST-382: Technical Debt Analysis

## Code Review Summary

Pragmatic testability improvements delivered:

- `RequestService` accepts optional `http_client` and `mcp_client`.
- `HTTPClient` accepts optional `session`.
- `doc/dev/testability.md` documents seams and mocking patterns for all three audit targets.
- Four unit tests verify constructor injection.

Production behavior unchanged when optional parameters are omitted.

## Shortcuts Taken

- **No HTTPClient protocol** ([PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46)):
  Seams use concrete types; mocks rely on duck typing.
- **No RequestWorker RequestService injection**
  ([PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379)): Worker still constructs
  `RequestService` internally.
- **MainWindow not decomposed**
  ([PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43)): Documented patch patterns only;
  no new presenter injection parameters.

## Code Quality Issues

None introduced. Existing post-construction mock assignment in tests remains valid.

## Missing Tests

- Integration test proving injected `http_client` flows from a future `RequestWorker` seam — blocked
  on PYPOST-379.
- Protocol-based mock type checking — blocked on PYPOST-46.

## Performance Concerns

None. Optional parameters add no runtime overhead beyond a None check at construction.

## Follow-up Tasks

All items already tracked in Jira from PYPOST-40 audit:

1. [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46) — HTTPClient protocol
2. [PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379) — RequestService injection into
   RequestWorker / MCPServerImpl
3. [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) — MainWindow decomposition

## Resolution of PYPOST-40 audit item

The "Testability gaps" item in `ai-tasks/PYPOST-40/60-tech-debt.md` is **partially resolved**:
documented patterns and constructor seams are in place; full DI refactor deferred to linked tickets.
