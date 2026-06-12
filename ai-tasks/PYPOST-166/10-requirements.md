# PYPOST-166: Declarative metrics HTTP routing

## Goals

PYPOST-23 identified that the observability stack used a manual WSGI-style check
(`environ['PATH_INFO'] == '/metrics'`) inside a wrapper on `MetricsManager`. Maintainers need
confidence that metrics HTTP routing uses the same declarative Starlette pattern as the main
MCP server, so future route changes do not reintroduce ad-hoc path checks.

## User Stories

- As a **maintainer**, I want metrics HTTP routes registered declaratively so routing stays
  consistent with the rest of the ASGI stack.
- As a **developer**, I want `MetricsManager` to remain a thin facade without HTTP routing
  logic so counter tracking and server lifecycle stay separated (PYPOST-75).
- As a **reviewer**, I want automated tests that assert `/metrics` is a Starlette mount, not
  a manual path wrapper, so regressions are caught early.

## Definition of Done

- [x] No manual `PATH_INFO` or WSGI wrapper routing for `/metrics` in `MetricsManager` or
  `MetricsServer`.
- [x] `/metrics` exposed via Starlette `Mount` with Prometheus ASGI app (PYPOST-75 layout).
- [x] Existing unit tests pass (`make test` for metrics ASGI compatibility).
- [x] Developer docs note declarative routing for the metrics server.
- [x] PYPOST-23 tech-debt item "Manual Route Handling" closed.

## Task Description

**Source:** [PYPOST-23](https://pypost.atlassian.net/browse/PYPOST-23) tech-debt —
`MetricsManager` manually checked `PATH_INFO == '/metrics'` in a wrapper.

After the metrics split (PYPOST-49/75), routing moved to `MetricsServer._create_app()`.
This task verifies that migration is complete or completes any remaining refactor.

**In scope:** Verification of routing approach; documentation; close debt item.

**Out of scope:** Changing metric names, ports, MCP resource URIs, or adding new HTTP routes.

## Q&A

| Question | Answer |
| --- | --- |
| Was code change required? | No — PYPOST-75 already uses `Mount("/metrics")`; facade has no routing. |
| New tests needed? | No — `TestMetricsServerAsgiCompatibility` in PYPOST-161 covers mount structure. |
