# PYPOST-39: MCP Tools Should Support Testing MCP Servers

## Goals

PyPost exposes HTTP requests as MCP tools. Users need to verify that MCP servers (including
PyPost's own MCP server) are working correctly. Today, when a user creates an MCP tool that
targets an MCP server's connection endpoint, the operation fails or hangs indefinitely,
providing no useful feedback. The goal is to enable users to create and use MCP tools that
successfully test and verify MCP servers.

## User Stories

- As a developer, I want to create an MCP tool that verifies an MCP server is reachable and
  responsive so that I can include health checks in my workflows.
- As a developer, I want to test the PyPost MCP server itself via PyPost tools so that I can
  validate the server without external tools.
- As a user, I want clear, predictable behavior when testing MCP server endpoints (no
  indefinite hangs, no opaque "Connection closed" errors) so that I understand what happened.

## Definition of Done

- User can create and use an MCP tool that successfully tests or verifies an MCP server
  (including PyPost MCP).
- When testing MCP server connection endpoints, behavior is clear and predictable: no
  indefinite hang, no opaque error messages.
- The solution works for the PyPost MCP server as a concrete verification target.

## Task Description

**Scope:** PyPost MCP tools (HTTP requests exposed as tools).

**Problem:** MCP servers use long-lived streaming connections for their transport. A normal
HTTP request to such an endpoint blocks until timeout or connection close. Users who create
MCP tools to test MCP servers experience failures ("Connection closed") or indefinite waits,
with no way to get a meaningful result.

**Functional scope:**

- MCP tools must support testing MCP servers.
- User must be able to verify that an MCP server (including PyPost MCP) is reachable and
  responsive.
- Behavior when targeting MCP server endpoints must be predictable and understandable.

**Out of scope:** Changing the MCP protocol, modifying external MCP clients.

**Programming language:** Python (PyPost).

## Q&A

- **Q:** What does "test an MCP server" mean? **A:** Verify that the server is reachable and
  responds in a way that indicates it is operational (e.g., accepts connection, returns
  initial data, or provides a clear success/failure result).
- **Q:** Why is this needed? **A:** Users want to include MCP server health checks in their
  workflows and validate PyPost MCP without switching to other tools.
- **Q:** What is the current workaround? **A:** Use MCP tools with normal HTTP requests
  (GET/POST to REST APIs). Testing MCP server connection endpoints does not work today.
