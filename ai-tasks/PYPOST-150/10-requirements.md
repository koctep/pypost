# PYPOST-150: Automated tests for server bind host

## Goals

Operators configure MCP and metrics server bind hosts in Settings. Without automated
verification that uvicorn honors those hosts, regressions in host binding would only be
caught by manual `netstat` checks.

## User Stories

- As a **PyPost maintainer**, I want integration tests that start MCP and metrics servers
  with each supported bind host, so host binding regressions fail CI instead of reaching
  operators.
- As a **PyPost user**, I want confidence that choosing `127.0.0.1`, `0.0.0.0`, `localhost`,
  or `::1` in Settings results in a server listening on that address family.

## Definition of Done

- [x] Integration tests cover MCP server bind for each Settings-supported host.
- [x] Integration tests cover metrics server bind for each Settings-supported host.
- [x] Tests assert the process listens on the configured address (not only that a port is open).
- [x] Developer testing docs list the new module.
- [x] PYPOST-151 / PYPOST-19 tech-debt item for missing host-bind tests is resolved.

## Task Description

Follow-up from PYPOST-19 and PYPOST-151: existing startup tests hardcode `127.0.0.1` and
verify port readiness only. This task adds host-parameterized integration coverage.

**In scope:** MCP (`MCPServerManager`) and metrics (`MetricsManager`) uvicorn bind hosts
supported by `validate_bind_host`.

**Out of scope:** cross-host port conflicts, external-network reachability, IPv6 on CI
without loopback.

## Q&A

| Question | Answer |
| --- | --- |
| Which hosts? | Same set as PYPOST-151 validation: `127.0.0.1`, `0.0.0.0`, `localhost`, `::1`. |
| How verify bind? | TCP connect probe plus `lsof` listen-address parse when available. |
