# PYPOST-169: Metrics HTTP server integration tests

## Goals

Close PYPOST-23 debt: maintainers need automated proof that the metrics observability server
binds a real port and serves Prometheus text over HTTP, not only via in-process ASGI tests.

## User Stories

- As a **maintainer**, I want integration tests that start `MetricsManager` on a free port and
  scrape `/metrics` over HTTP, so regressions in uvicorn startup or routing are caught in CI.
- As a **reviewer**, I want assertions on HTTP status, content type, and counter text so the
  test verifies end-to-end behavior after server start.

## Definition of Done

- [x] Integration tests bind a local port and wait until the server listens.
- [x] HTTP GET `/metrics` returns 200 with Prometheus `text/plain` body.
- [x] Tracked counters appear in the live scrape payload.
- [x] Tests use explicit pytest timeouts and bounded port waits.
- [x] Developer testing docs list the new integration coverage.
- [x] PYPOST-23 missing-tests debt item addressed.

## Task Description

Follow-up from `ai-tasks/PYPOST-23/40-tech-debt.md`. Unit tests (`TestClient`) already cover
ASGI routing; this task adds live-server integration coverage for the HTTP scrape path.

**In scope:** integration tests only.

**Out of scope:** production code changes, MCP round-trip tests (PYPOST-563).

## Q&A

| Question | Answer |
| --- | --- |
| Where do tests live? | Extend `tests/test_metrics_server_integration.py`. |
| Why not only `TestClient`? | Live uvicorn thread + socket bind validates real startup. |
