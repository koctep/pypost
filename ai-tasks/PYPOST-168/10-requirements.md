# PYPOST-168: Close debt — optional metrics via constructor injection

## Goals

Close follow-up debt from [PYPOST-23](https://pypost.atlassian.net/browse/PYPOST-23): decouple
`HTTPClient` and MCP server from mandatory metrics collection.

## Definition of Done

- [x] `metrics=None` constructor parameter on `HTTPClient` and MCP server types
- [x] Metric tracking skipped when no manager is injected
- [x] Residual import coupling documented as accepted

## Task Description

Sprint 492 debt closure. Optional injection replaces implicit global dependency for tests and
headless use; full event-bus decoupling remains out of scope.
