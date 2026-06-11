# PYPOST-550: Inject active environment variables into MCP tool execution

## Goals

PyPost users expose saved HTTP requests as MCP tools so AI agents (e.g. Cursor, Claude) can
call them. Those requests often rely on environment variables — such as `{{ base_url }}` or
`{{ api_key }}` — that belong to the **active environment** selected in the app.

Today, running the same request from the GUI resolves those placeholders correctly, but
calling it through MCP does not. Agents receive failed or incorrect requests (unresolved
templates, wrong URLs, missing auth values) even though the user has configured the
environment and enabled the MCP server for it.

The business goal is **parity**: an MCP tool call must behave the same as executing that
request from the GUI with the same active environment and the same agent-supplied tool
arguments. Users should not need duplicate configuration or workarounds to make MCP usable
for real collections.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **PyPost user**, I want MCP tool calls to use my active environment's variables, so
  tools I expose to AI agents work the same way they do when I send them from the app.
- As a **PyPost user**, I want requests that mix environment placeholders (e.g.
  `{{ base_url }}`) and MCP argument placeholders (e.g. `{{ mcp.request.user_id }}`) to
  resolve both when an agent calls the tool, so I can build reusable tools without hard-coding
  host or credential values.
- As an **AI agent operator**, I want tools exposed by PyPost to succeed when the user's
  environment is configured, so I can rely on MCP integration without asking the user to
  inline secrets or URLs into every tool definition.
- As a **PyPost user**, I want switching the active environment to change which variable
  values MCP tools use, so staging and production environments stay isolated the same way
  they are for GUI sends.

## Definition of Done

- [ ] When the MCP server is running for an environment with MCP enabled, `call_tool`
  resolves all environment-variable placeholders in the tool's request (URL, headers, query
  params, body) using that environment's current values.
- [ ] For the same exposed request, the same active environment, and the same MCP tool
  arguments, execution via MCP produces the same resolved request and outcome as sending
  the request from the GUI.
- [ ] Environment variables and MCP tool arguments can appear together in one request; both
  are applied at execution time.
- [ ] Hidden environment variables continue to supply real values at execution time (masking
  applies only to display, consistent with GUI behavior).
- [ ] Existing MCP-specific behavior (`{{ mcp.request.* }}` arguments from the agent) is
  preserved and still works alongside environment variables.
- [ ] Automated tests cover at least one tool that uses environment placeholders and
  demonstrates parity with the GUI execution path.

## Task Description

### Problem

Users mark requests as MCP tools and enable the MCP server on an environment that holds
their API base URL, tokens, and other shared values. When an external client invokes
`call_tool`, those environment placeholders are not applied. The tool either fails or hits
the wrong endpoint, while the identical request works from the GUI because the GUI passes
the active environment's variables into request execution.

This breaks the core value of MCP integration: agents cannot use the user's existing
PyPost configuration and must either fail or require redundant setup outside PyPost.

### Scope

**In scope**

- Resolving active-environment variable placeholders during MCP `call_tool` execution.
- Parity with the GUI request execution path for template resolution and HTTP execution.
- Support for requests that combine environment variables and MCP tool arguments.
- Behavior when the user changes the active environment while the MCP server is running.

**Out of scope**

- New MCP transport protocols or changes to how tools are listed or named.
- New UI for MCP configuration beyond what already exists (expose-as-tool, enable MCP on
  environment).
- Defining new placeholder syntax; only existing `{{ variable }}` and `{{ mcp.request.* }}`
  forms are in scope.
- Changing how environment variables are stored, encrypted, or edited.
- Metrics-server MCP (observability resources); only user-facing request tools are in scope.

### Functional requirements

1. **Environment variable resolution on MCP execution** — When an agent calls an exposed
   tool, every environment-variable placeholder in that request must be substituted with
   the value from the **currently active environment** (the one for which MCP is enabled).
2. **GUI parity** — Given the same request definition, active environment, and MCP tool
   arguments, MCP execution must match GUI execution: same resolved URL/headers/body and
   same HTTP result (success or error category).
3. **Combined placeholders** — Requests may reference both environment variables and MCP
   tool arguments; all must resolve in a single execution.
4. **Active environment changes** — When the user selects a different environment (or
   re-selects one after editing its variables), subsequent MCP tool calls must use the new
   environment's values without requiring a manual MCP server restart beyond what the app
   already performs today.
5. **Hidden variables** — Hidden flags affect display only; execution must still use the
   stored values, matching GUI send behavior.
6. **Post-request scripts** — If a tool's request includes a post-request script that reads
   environment context, it must receive the same variable set as in the GUI path (including
   values available before any script-driven updates).

### Non-functional requirements

- **Consistency** — Users must not need to learn a separate variable model for MCP; the
  same environment they select for manual testing is the source of truth for agents.
- **Security** — No regression in how secrets are handled: hidden-variable masking in UI
  and logs must remain unchanged; this task only closes the execution gap.
- **Backward compatibility** — Tools that rely only on `{{ mcp.request.* }}` must keep
  working as they do today.

### Constraints and assumptions

- MCP server lifecycle is tied to environment selection with `enable_mcp=True` (existing
  behavior).
- Environment variables are key–value strings defined on the `Environment` entity; template
  function expressions (e.g. allowed built-in functions on variables) are in scope only
  insofar as they already work on the GUI path and depend on environment values.
- Localhost MCP access model is unchanged (local agents connect to a user-started server).
- Implementation approach is deferred to Step 2; this document defines *what* must be true,
  not *how* to wire variables into the server.

### Main entities (business view)

| Entity | Role |
| --- | --- |
| **Active Environment** | The environment currently selected in PyPost; supplies variable values for request execution. |
| **Environment Variable** | A named configuration value (e.g. `base_url`, `api_key`) referenced in request templates. |
| **MCP Tool** | A saved request exposed to external agents via MCP. |
| **MCP Tool Argument** | A runtime value provided by the agent for placeholders such as `{{ mcp.request.name }}`. |
| **Template Placeholder** | A `{{ ... }}` reference in request fields that must be resolved before the HTTP call. |

**Interactions**

1. User selects an environment and enables MCP → server exposes marked requests as tools.
2. Agent calls `call_tool` with arguments → PyPost resolves environment variables from the
   active environment, resolves MCP arguments from the call payload, executes the HTTP
   request, returns the response.
3. User switches environment → later MCP calls use the new environment's variables.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this needed? | MCP tools are unusable for typical collections that centralize URLs and credentials in environments; GUI works, MCP does not. |
| What does "active environment" mean? | The environment currently selected in the PyPost UI while MCP is enabled for that environment. |
| Should MCP arguments override environment variables with the same name? | Not specified as a user requirement; parity with GUI implies environment variables and `mcp.request.*` occupy separate placeholder namespaces today. Any collision behavior should match the GUI path (to be confirmed in architecture if ambiguous). |
| Do hidden variables block MCP execution? | No. Hidden means masked in UI; execution uses real values, same as GUI. |
| Is listing tools (`list_tools`) in scope? | Only indirectly — schemas for `mcp.request.*` args stay as today; this task is about execution-time resolution of environment vars. |
| Acceptance from Jira? | MCP `call_tool` resolves active environment variables; behavior matches GUI execution path. |
