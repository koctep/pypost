# PYPOST-1201: Developer Documentation Assessment

## Maintainer decision

The silent WebSocket mock transport remains file-local to
`tests/test_websocket_client_ui_repro.py`. Repository inventory found one
qualifying UI consumer boundary: the two lifecycle scenarios in that module
share one local owner. The reuse threshold is therefore unmet, and extracting
the helper would add a shared test dependency without removing cross-module
duplication.

The local support remains intentionally hermetic. It is supplied through the
existing `WebSocketSessionController.set_transport_factory` seam, accepts the
handshake target without opening a network connection, treats transport
operations as no-ops, and emits no listener callbacks. Tests should continue to
inject it explicitly and use independent instances where state is observed.

Do not move this helper into a generic shared fixture merely because other
tests contain transport doubles. Controller-, session-engine-, and integration-
focused doubles have different responsibilities and should retain their
purpose-specific contracts.

## Future extraction trigger

Revisit the decision when either of these conditions is evidenced in a new task:

- a distinct UI test module or scenario needs materially the same silent
  transport behavior; or
- duplicated silent behavior creates a credible risk that consumers will drift.

Before extracting, record the new consumer or duplication evidence, migrate only
the qualifying UI consumers to the smallest test-only support module, preserve
explicit factory injection and no-network behavior, and run focused lifecycle
tests through Make. Similar names or unrelated protocol-level doubles do not
qualify on their own.

## Repository documentation assessment

N/A — no external `doc/dev` guide update is warranted. PYPOST-1201 changes no
production behavior, public API, WebSocket protocol, or shared test harness.
The existing [WebSocket UI client guide](../../doc/dev/websocket_ui_client.md)
and [WebSocket test harness guide](../../doc/dev/websocket_test_harness.md)
already document the broader runtime and test infrastructure; adding a
file-local, optional no-op helper to either guide would create misleading
shared-support guidance.

## References

- [Requirements](10-requirements.md)
- [Architecture](20-architecture.md)
- [Cleanup audit](40-code-cleanup.md)
- [Observability decision](50-observability.md)
- [Technical-debt analysis](60-tech-debt.md)
- [PYPOST-1201 in Jira](https://pypost.atlassian.net/browse/PYPOST-1201)
