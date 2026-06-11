# PYPOST-557: Structured MCP tool call result (status, error flag, body)

## Goals

AI agents invoke PyPost MCP tools to run saved HTTP requests. Today the agent receives an
opaque text blob — usually the raw HTTP response body, sometimes with script logs or errors
appended as free-form sections. That makes it hard to tell whether PyPost failed to execute
the request, the upstream API returned an error status, or the MCP protocol itself failed.

The business goal is **predictable tool results**: every successful `call_tool` response uses
the same JSON shape so agents (and PyPost users previewing behavior) can reliably read HTTP
status, an execution error flag, the response body, and optional script logs — and distinguish
those from MCP protocol errors (unknown tool, internal server failure).

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As an **AI agent operator**, I want MCP tool responses in a consistent JSON structure with
  HTTP status, error flag, and body, so my agent can parse outcomes without custom heuristics.
- As a **PyPost user**, I want execution failures (network, template, script) flagged separately
  from successful HTTP calls that return 4xx/5xx, so I can debug configuration vs API errors.
- As an **AI agent operator**, I want script log lines in an optional field rather than appended
  prose, so logs do not corrupt the response body field.
- As a **PyPost user**, I want MCP protocol errors (e.g. unknown tool) to remain protocol-level
  failures, not disguised as structured execution results.

## Definition of Done

- [ ] Every successful MCP `call_tool` that runs `RequestService.execute()` returns
  `TextContent` whose text is JSON with keys `status` (int), `error` (bool), and `body` (str).
- [ ] `error` is `true` when PyPost execution failed (`execution_error` set or HTTP status `0`);
  `false` when the HTTP request completed (including upstream 4xx/5xx).
- [ ] When post-request scripts emit log lines, they appear in optional `logs` (array of strings).
- [ ] When `execution_error` is set, optional `error_category` and `error_message` fields
  expose structured failure semantics.
- [ ] Unknown tools still raise protocol errors (not JSON envelope).
- [ ] Unexpected internal failures in `call_tool` return plain-text protocol errors (unchanged).
- [ ] Automated tests cover success, upstream 404, execution error, script logs, and integration
  round-trip.
- [ ] Developer documentation updated in `doc/dev/mcp_integration.md`.

## Task Description

### Problem

MCP tool responses today return raw HTTP body text. Script logs and script errors are appended
as markdown-like sections. Agents cannot reliably extract status codes or know if PyPost failed
before reaching the upstream API. This conflicts with the MCP Tools epic goal of predictable,
agent-friendly tool contracts.

### Scope

**In scope**

- Structured JSON envelope for all `ExecutionResult`-based `call_tool` responses.
- Error flag semantics tied to PyPost execution outcome, not upstream HTTP success.
- Optional `logs`, `error_category`, `error_message` fields.
- Metrics outcome aligned with execution error flag.
- Tests and dev docs.

**Out of scope**

- Masking or redacting HTTP response bodies (see PYPOST-554 follow-ups).
- Changing `RequestService` or GUI response presentation.
- MCP resources / metrics server responses.
- UI preview of structured results (PYPOST-555).

### Functional requirements

1. **Structured envelope** — JSON with `status`, `error`, `body` on every execution-path
   `call_tool` response.
2. **Error flag** — `error: true` when `execution_error` is present or `status == 0`;
   `error: false` when HTTP dispatch completed with a non-zero status.
3. **Optional logs** — Include `logs` only when script logs are non-empty.
4. **Execution error detail** — Include `error_category` and `error_message` when
   `execution_error` is set.
5. **Protocol separation** — Unknown tool → raise; internal exception → plain-text error
   (not JSON envelope).

### Non-functional requirements

- **Backward awareness** — Agents must migrate to JSON parsing; document the shape in dev docs.
- **Consistency** — Same envelope for all exposed request tools.
- **Safety** — Do not add new secret leakage in logs or envelope fields.

### Constraints and assumptions

- MCP SDK returns tool results as `TextContent`; JSON is serialized to the text field.
- `RequestService.execute()` already returns `ExecutionResult` with `response`, `script_logs`,
  and `execution_error`.
- Implementation approach deferred to Step 2.

## Q&A

| Question | Answer |
| --- | --- |
| Is HTTP 404 from upstream an error? | No — `error: false`, `status: 404`; PyPost executed successfully. |
| Is a network failure an error? | Yes — `error: true`, `status: 0`. |
| Are script failures errors? | Yes — `execution_error` with category `script`, `error: true`. |
| Jira acceptance | Predictable structured result (HTTP status, error flag, body, optional logs). |
