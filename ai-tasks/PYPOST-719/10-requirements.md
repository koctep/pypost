# PYPOST-719: Unit test MCPServerManager lifecycle

## Goals

Raise MCPServerManager coverage from 38% (at audit time) to ≥90% using fast,
port-free unit tests that mock the uvicorn server, eliminating the flakiness of
integration tests that bind real ports.

## User Stories

- As a developer, I want MCPServerManager lifecycle paths (startup signals, error
  signals, unexpected exit) covered by isolated unit tests that pass deterministically
  without port conflicts.

## Definition of Done

- `pypost/core/mcp_server.py` coverage ≥ 90%.
- New tests use mocks instead of real server threads where possible.
- Full test suite passes without flaky failures.

## Task Description

The audit identified `mcp_server.py` at 38% coverage with unstable integration tests.
Remediation: mock `_run_uvicorn` internals (create_app, uvicorn.Server.serve) to
exercise all signal-emission paths without binding ports.

## Q&A

**Q: Why was coverage only 38%?**
A: Many branches inside `_run_uvicorn` (generic exception, unexpected exit, restart
   while running) were only reachable by real server interactions that are slow and
   port-sensitive.
