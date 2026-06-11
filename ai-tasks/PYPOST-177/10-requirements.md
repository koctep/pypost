# PYPOST-177: Unit tests for MCP metrics collection

## Goals

After PYPOST-75 split `MetricsManager` into `MetricsRegistry` (pure counters) and
`MetricsServer` (HTTP/MCP), automated tests still relied on the facade and lacked direct
coverage of the Prometheus `/metrics` scrape endpoint. PYPOST-24 debt remains open until
developers can verify counter registration and MCP metrics hooks on the split modules
without starting uvicorn.

## User Stories

- As a **developer**, I want unit tests on `MetricsRegistry` that assert `mcp_*_total`
  counters increment correctly so I can change tracking logic without a live server.
- As a **developer**, I want a unit test that GET `/metrics` returns Prometheus text from the
  metrics ASGI app so scrape behavior is regression-protected after refactors.
- As a **maintainer**, I want `MetricsServer` MCP resource handlers covered at the server
  layer (success and error paths) independent of the facade.

## Definition of Done

- [x] `MetricsRegistry` MCP counter tracking covered by dedicated unit tests.
- [x] HTTP `/metrics` endpoint returns 200 and includes registered counters (TestClient).
- [x] `MetricsServer.read_resource` success and error paths assert `mcp_*_total` labels.
- [x] All new tests declare explicit `@pytest.mark.timeout` markers.
- [x] `make test` passes for new and existing metrics tests.
- [x] Developer docs updated in `doc/dev/testing.md`.

## Task Description

Source: [PYPOST-24](https://pypost.atlassian.net/browse/PYPOST-24) — no unit tests for MCP
metrics collection. PYPOST-75 delivered the module split; this task adds the missing test
coverage on the new boundaries.

**In scope:** Unit tests for `MetricsRegistry`, `MetricsServer` `/metrics` route, MCP
resource metrics counters.

**Out of scope:** Live uvicorn integration tests, MCP SSE round-trip, changing metric names
or labels.

## Q&A

| Question | Answer |
| --- | --- |
| Why not only facade tests? | PYPOST-75 goal was testability of split modules; facade tests alone miss server/registry seams. |
| Replace `test_metrics_manager.py`? | No — keep existing facade tests; add component-level coverage. |
