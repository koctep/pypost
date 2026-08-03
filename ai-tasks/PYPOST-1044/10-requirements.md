# PYPOST-1044: Launch multiple independent MCP servers

## Goals

PyPost users need to make different sets of collection-backed MCP tools
available at the same time without mixing their credentials, requests, or
operating context.  Today, starting an MCP server represents one shared
configuration, which prevents a user from serving separate collections and
environments concurrently.

This task enables users to launch and manage multiple MCP servers, where each
server has its own listening port, selected collection, and selected
environment.  The business outcome is that separate AI clients or workflows
can connect to the appropriate tool catalog and credentials without disrupting
other running MCP integrations.

**Programming language:** Python

## User Stories

- As a **PyPost user**, I want to launch more than one MCP server in the same
  application session so I can support separate AI-client workflows at once.
- As an **integration operator**, I want each launched MCP server to have its
  own port so clients can connect to the intended server unambiguously.
- As a **collection owner**, I want a server to expose tools from its selected
  collection so unrelated collection tools are not presented to that server's
  clients.
- As an **environment owner**, I want a server to run with its selected
  environment so it uses the correct contextual configuration for that
  integration.
- As a **PyPost user**, I want to see and control the independently launched
  servers so I can identify which integrations are available and stop only the
  one I intend to stop.

## Definition of Done

- [ ] A user can launch multiple MCP servers during one PyPost session.
- [ ] Every launched server has a distinct port selected for that server.
- [ ] Every launched server is associated with one selected collection and one
      selected environment.
- [ ] An MCP client connected to a server receives tools from that server's
      selected collection, using that server's selected environment context.
- [ ] Starting, stopping, or changing one launched server does not interrupt
      the availability or configuration of other running servers.
- [ ] The product clearly reports a server that cannot be launched because its
      chosen port is already unavailable, while leaving other running servers
      unaffected.
- [ ] Existing single-server users retain an understandable path to launch and
      manage their MCP integration.

## Task Description

**Problem:** Users who maintain more than one collection or environment cannot
currently make those integrations available as separate MCP endpoints at the
same time.  They must choose one shared server context, which can expose an
inappropriate tool set or force an active integration to be stopped before a
different one can be served.

**Business outcome:** PyPost can serve independent MCP integration contexts
concurrently.  Each external client connects to the endpoint intended for its
workflow and receives only the collection tools and environment context chosen
for that server.

### In Scope

- Launching and managing more than one concurrently available PyPost MCP
  server.
- Selecting a port, collection, and environment independently for each server.
- Keeping the tool catalog and environment context of one server separate from
  those of every other server.
- Clear user-visible handling when a requested server cannot be launched due
  to an unavailable port.
- Preserving a usable single-server workflow for existing users.

### Out of Scope

- Changes to the HTTP requests, tool definitions, or credentials stored in a
  collection or environment.
- Altering external MCP client products or their connection configuration
  beyond the endpoint each client chooses to use.
- Sharing one server's tools or environment context with another server unless
  the user deliberately launches an equivalent separate server.
- New remote hosting, account management, or access-control products.

## Functional Requirements

- The product must allow a user to create and launch multiple MCP server
  instances in one application session.
- For each server instance, the user must be able to select its port,
  collection, and environment independently of other instances.
- A server must make available only the MCP tools represented by its selected
  collection.
- A server must apply the selected environment context for requests invoked by
  its clients.
- The product must keep server lifecycle actions independent: stopping or
  reconfiguring one server must not stop or reconfigure another running server.
- The product must prevent an unavailable port from being used by a new server
  and communicate the condition clearly to the user.
- The product must present enough server identity and state for a user to
  distinguish concurrently launched servers and manage the intended one.

## Non-functional Requirements

- **Isolation:** Tool exposure, environment context, and lifecycle control
  remain isolated between concurrently running servers.
- **Reliability:** A failed launch of one server must not make already running
  servers unavailable.
- **Compatibility:** Existing users with one MCP integration can continue to
  operate it without needing multiple-server expertise.
- **Usability:** Users can understand which port, collection, and environment
  belong to each running server.
- **Security:** An integration must not receive tools or environment context
  selected for a different server.
- **Maintainability:** The product behavior can be verified for concurrent
  server operation, isolation, and port-conflict handling.

## Constraints and Assumptions

- Issue key: PYPOST-1044.
- The requested behavior is scoped to MCP servers launched by one PyPost
  application session.
- A port is the client-facing identifier used to reach a particular server and
  therefore must be unique among concurrently active servers.
- A collection represents the tool catalog selected for an integration.
- An environment represents the contextual configuration selected for an
  integration, including any values required by its collection requests.
- The task requires a product behavior change; the later architecture step
  determines the user interaction and internal design.

## Main Entities

| Entity | Description |
| --- | --- |
| MCP server instance | An independently launched PyPost integration endpoint with its own state. |
| Port | The client-facing endpoint identifier assigned to one server instance. |
| Collection | The user-selected set of requests that defines a server's available MCP tools. |
| Environment | The user-selected contextual configuration used by a server's collection requests. |
| MCP client | An external AI client or workflow that connects to one server instance. |
| Server lifecycle | The user-controlled availability state of an individual server, such as launched or stopped. |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this needed? | Users need separate AI workflows to be available concurrently without mixing their collections or environments or stopping a working integration. |
| What defines one server's identity? | Its selected port, collection, and environment together identify the integration context the user intends to serve. |
| Can two launched servers use the same port? | No. The product must prevent the unavailable-port launch and preserve the other server's availability. |
| Does a server expose every collection loaded in PyPost? | No. Each server exposes the tools from the collection selected for that server. |
| Does this modify collection requests or credentials? | No. It selects existing collection and environment contexts; changing their content is outside this task. |
| How does this affect the current one-server workflow? | It must remain understandable and usable for existing users. |

## STEP 1 Approval Basis

The applicable `sprint-runner` workflow is explicitly autonomous, and the user
has additionally instructed that every review or approval be performed by a
subagent without stopping.  An independent Step 1 review is therefore required
and is the approval basis recorded in the roadmap once it passes.
