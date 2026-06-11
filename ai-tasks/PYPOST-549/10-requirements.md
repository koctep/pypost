# PYPOST-549: MCP Tools — turn HTTP requests into safe local AI agent tools

## Goals

PyPost users already maintain working HTTP requests in collections. Giving a local AI agent
(Cursor, Claude Desktop, etc.) access to those APIs today usually means hand-building an MCP
server: re-describing endpoints, auth, and parameters, with weak control over what the agent
sees and whether secrets leak.

This epic defines the **product vision** for closing that gap: turn saved requests into
**safe, reliable MCP tools** through the PyPost UI — in seconds, without writing server
code. Implementation is delivered incrementally by child stories (PYPOST-550..557 and related
follow-ups).

## Programming Language

Python 3.11+ (PyPost project standard). Code changes belong to child stories, not this epic.

## User Stories

- As a **solo developer**, I want to mark a saved HTTP request as an MCP tool and enable a
  local MCP server from the UI, so my AI agent can call my APIs without a separate
  integration project.
- As a **PyPost user**, I want each exposed tool to have a clear name, description, and
  parameters, so agents understand how to invoke my requests correctly.
- As a **PyPost user**, I want environment variables from my active environment applied when
  an agent calls a tool, so MCP behavior matches sending the same request from the GUI.
- As a **PyPost user**, I want secrets and hidden variables handled safely in a network MCP
  context, so credentials are not exposed to agents or logs beyond what I intend.
- As an **AI agent operator**, I want to connect my local MCP client to PyPost using a
  current, supported network transport, so setup matches client documentation and works with
  tools like Cursor.
- As a **PyPost user**, I want to preview what the agent will see (tool contract) and see
  reliable server status in the UI, so I can trust the integration before connecting an agent.
- As a **PyPost user**, I want predictable structured results from tool calls (HTTP status,
  error flag, body), so agents and I can distinguish execution failures from protocol errors.
- As an **operator**, I want Prometheus metrics for request and MCP activity on my machine,
  so I can monitor usage and errors without exposing operational telemetry to the agent.

## Definition of Done (Epic)

The epic is **done** when all of the following hold:

- [ ] Product vision is documented in README.md and matches Jira epic description.
- [ ] Epic-level requirements and architecture artifacts exist under `ai-tasks/PYPOST-549/`.
- [ ] Child story **PYPOST-550** (environment variables in MCP execution) is Done.
- [ ] Child story **PYPOST-551** (Streamable HTTP transport) is Done.
- [ ] Child story **PYPOST-552** (E2E verification with Cursor; user-facing MCP docs) is Done.
- [ ] Child stories **PYPOST-553..557** (metadata, secrets policy, UI preview, overview/status,
  structured results) are Done.
- [ ] A local AI agent can connect to PyPost, list tools, and successfully invoke at least
  one exposed request with env vars resolved and secrets handled per policy.
- [ ] User-facing and developer documentation describe current connection URLs
  (`http://<host>:<port>/mcp` for Streamable HTTP) and setup flow end-to-end.

## Task Description

### Problem

API client users already have correct requests, environments, and secrets configured in
PyPost. MCP integration should reuse that work — not force a parallel server implementation.
Without a coherent vision and staged delivery, features risk inconsistent safety (secrets in
agent context), broken transport (deprecated SSE-only), or poor operator experience (opaque
tool contracts, unreliable “MCP: ON” status).

### Vision (from Jira)

**Turn existing HTTP requests into safe MCP tools for a local AI agent — in seconds, through
the UI, without writing server code.**

**North star:** Any request marked as an MCP tool is reliably available to the local agent
with a clear name, description, and parameters; environment variables resolved; secrets
handled safely.

### Scope

**In scope (epic / program)**

- Local-first, solo-developer use case.
- One saved request = one MCP tool.
- Network MCP server for local AI clients (not stdio subprocess transport).
- Safety-by-default: operator sees more than the agent; secrets masked where appropriate.
- Reuse of existing request execution, templating, and environment model.
- Observability for operators via Prometheus on localhost (not a separate agent event stream).
- Staged delivery via child stories listed in `00-roadmap.md`.

**Out of scope (epic level)**

- Multi-tenant or hosted MCP SaaS.
- Remote authentication/TLS beyond existing host/port configuration.
- Rewriting PyPost's core HTTP client or collection model.
- Implementation code in this epic ticket (tracked in child stories).

### Functional requirements (program-level)

1. **Expose as tool** — User can mark a request as an MCP tool and enable MCP on an
   environment; PyPost serves tools for that environment on a configurable local port.
2. **Execution parity** — MCP `call_tool` uses the same request execution path as the GUI,
   including environment variables and MCP argument placeholders.
3. **Current transport** — Local agents connect via Streamable HTTP (`/mcp`); legacy SSE may
   remain during transition (PYPOST-551).
4. **Tool contract** — Agents receive meaningful name, description, and parameter schema (not
   name-only descriptions and all-string required params).
5. **Secrets policy** — Hidden keys and opt-in rules govern what reaches network MCP context
   and logs.
6. **Operator UX** — Preview of agent-visible contract; accurate server status; clear errors
   (e.g. port busy).
7. **Structured results** — Tool responses expose HTTP status, error semantics, and body in a
   predictable shape.
8. **Verification** — Documented E2E path with a representative local agent (Cursor).

### Non-functional requirements

- **Local-first** — Default bind to localhost; user explicitly opts into broader exposure.
- **Safety by default** — Prefer withholding secrets from agent-visible payloads and logs.
- **Maintainability** — Align with current MCP spec and Python SDK transport direction.
- **Observability** — Prometheus `/metrics` for operators; agent context in tool responses.

### Constraints and assumptions

- PyPost remains a desktop app with embedded MCP HTTP servers (request tools + metrics).
- Child stories own code, tests, and user-doc updates for their slice.
- README.md is the canonical **product vision**; `doc/dev/` holds developer detail.

### Main entities (business view)

| Entity | Role |
| --- | --- |
| **Saved request** | HTTP request definition in a collection; candidate for MCP exposure. |
| **MCP tool** | A request marked “expose as MCP”; one tool per request. |
| **Environment** | Named set of variables; active environment drives MCP server and var resolution. |
| **MCP server** | Local HTTP service exposing tools for the enabled environment. |
| **MCP client (agent)** | External or in-app software that lists and invokes tools. |
| **Tool contract** | Name, description, and parameter schema visible to the agent. |
| **Operator** | PyPost user who configures tools, monitors metrics, and sees full context. |

**Interactions**

1. User marks requests as tools and enables MCP on an environment → server starts locally.
2. Agent connects via Streamable HTTP → `list_tools` / `call_tool`.
3. PyPost resolves env vars and agent args → executes HTTP request → returns structured result.
4. Operator monitors via Prometheus; agent receives execution context in tool response only.

## Q&A

| Question | Answer |
| --- | --- |
| Where is the product vision written? | README.md Vision section; must stay aligned with this epic. |
| Who implements code? | Child stories PYPOST-550..557 (and PYPOST-561/562 for docs/metrics). |
| Is stdio MCP in scope? | No — network/local HTTP server integrated with the Qt app. |
| Epic vs story DoD? | Epic closes when all planned child stories meet their acceptance criteria. |
| README says “you see more than the agent” vs epic “what you see is what the agent sees”? | README refines the principle for safety (PYPOST-554); operator preview vs agent payload. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: (subagent aggregate)
