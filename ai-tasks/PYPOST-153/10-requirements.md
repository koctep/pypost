# PYPOST-153: Port binding error handling for observability servers

## Goals

Operators need a clear, actionable message when PyPost cannot bind the metrics or MCP server
port, instead of inferring failure from logs or silent OFF status.

## User Stories

- As a **PyPost user**, I want a visible error when the metrics port is busy at startup, so I
  can change Settings without reading log files.
- As a **PyPost user**, I want MCP bind failures to show the same style of message (already
  delivered in PYPOST-556), so behavior is consistent across servers.

## Definition of Done

- [x] Metrics server bind failures produce an operator-facing message.
- [x] Main window shows a warning dialog for metrics bind failures.
- [x] Failures that occur before the UI connects are replayed when the window opens.
- [x] MCP server bind handling verified unchanged and still covered by tests.
- [x] Automated tests cover metrics port-busy and deferred-delivery paths.
- [x] Developer docs updated.

## Task Description

Follow-up from PYPOST-20 tech debt: port binding errors were swallowed in background threads.
PYPOST-556 added `start_failed` for `MCPServerManager`. This task closes the gap for
`MetricsManager` / `MetricsServer`.

**In scope:** metrics bind error signaling, UI notification, shared bind-error formatting.

**Out of scope:** auto-retry, alternate port selection (PYPOST-154).

## Q&A

| Question | Answer |
| --- | --- |
| Is MCP already handled? | Yes — verified; refactored to shared `format_bind_error`. |
| Where is metrics UI wired? | `MainWindow.connect_start_failed` after startup in `main.py`. |
