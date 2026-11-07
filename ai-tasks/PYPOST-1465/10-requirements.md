# PYPOST-1465: Live Collection Tool Refresh for Isolated MCP Servers

## Goals

Operators who run standalone MCP servers in isolated execution mode must see edits to their backed
request collections take effect without restarting PyPost or manually stopping and restarting each
affected server. When an operator adds, edits, or removes requests in a collection, every running
isolated server backed by that collection must expose the updated tool set and updated collection
variables just as shared-execution servers already do.

This closes the collection-refresh parity gap identified in
[PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439) within the approved MCP Process
Reliability sprint goal.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **automation author**, I can add, modify, or remove requests in a collection while an
  isolated MCP server is running and immediately discover and invoke the updated tools without
  restarting PyPost or manually cycling the server.
- As an **automation author**, I can update collection-scoped variables alongside request edits and
  have running isolated servers resolve the refreshed collection values on subsequent tool calls.
- As an **enterprise operator**, I can refresh one collection without disrupting unrelated running
  isolated servers or proxy servers, and without leaking variables across servers.

## Definition of Done

1. When a collection is refreshed, all running isolated MCP servers backed by that collection
   expose the updated set of tools (added, modified, and removed requests) for subsequent tool
   discovery and invocation without requiring a host restart or manual server stop/start.
2. Collection-scoped variables updated as part of a collection refresh are reflected in subsequent
   tool invocations on the affected isolated servers, while active environment variables remain
   preserved.
3. Running isolated servers backed by other collections, as well as running proxy servers, are not
   disrupted or altered when an unrelated collection is refreshed.
4. Each isolated server continues to resolve only its own configuration and variable values;
   refreshing a collection never leaks secrets or variables across servers or into diagnostics.
5. If a running isolated server is already in a stopped or failed state, or if a refresh cannot be
   applied to an unavailable server, the host remains stable and neighboring servers continue
   operating normally.
6. Existing shared-execution collection refresh behavior remains intact and covered by regression
   checks.
7. Automated acceptance checks verify live tool-list discovery and invocation updates (addition,
   modification, removal) and collection variable updates for running isolated servers.

## Task Description

### Problem and Scope

In shared execution mode, editing a collection refreshes the tools and collection variables served
by any running MCP server backed by that collection. In isolated execution mode, running servers do
not currently receive collection tool updates after startup, forcing operators to manually stop and
restart servers whenever a collection changes.

Scope includes:

- Propagating collection tool definitions and collection-scoped variable updates to matching
  running isolated servers during collection refresh workflows.
- Preserving server identity, listening endpoint, and isolation guarantees across refreshes.
- Keeping unrelated local and proxy servers unaffected.
- Maintaining full parity with shared execution mode for collection refresh outcomes.

Out of scope are new MCP protocol features, automatic crash-restart policies, settings UI controls,
memory admission limits, and active health watchdogs, which belong to separate follow-up tasks from
[PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439).

### Functional Requirements

- **FR1 (Live Tool Set Refresh)**: Refreshing a collection updates the exposed tools (names,
  descriptions, schemas, and request behavior) on every running isolated server bound to that
  collection.
- **FR2 (Collection Variable Refresh)**: Refreshing a collection updates the collection-scoped
  variables used by every running isolated server bound to that collection while retaining the
  active environment context.
- **FR3 (Target Selectivity)**: Only running servers bound to the refreshed collection are updated;
  servers bound to other collections and proxy servers remain untouched.
- **FR4 (Endpoint and Identity Continuity)**: A refreshed isolated server retains its server
  identity, configured listening endpoint, and running status from the operator's perspective.
- **FR5 (Failure Containment)**: Refreshing a collection when a server has exited or fails to
  apply the update must not crash the host application or interrupt healthy peer servers.
- **FR6 (Shared-Mode Compatibility)**: Collection refresh in shared execution mode continues to
  update running servers without regression.

### Non-Functional Requirements

- **NFR1 (Bounded Refresh Completion)**: Applying a collection refresh to running isolated servers
  must finish within a bounded operator-interactive window without hanging the host.
- **NFR2 (Secret and Variable Privacy)**: Updated collection variables and request headers remain
  private to the owning server and are never exposed in logs or error diagnostics.
- **NFR3 (Cross-Platform Consistency)**: Live collection refresh behaves consistently across
  supported desktop operating systems.

### Constraints and Assumptions

- The business need is established by the approved MCP Process Reliability sprint and the deferred
  collection-refresh item from [PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439).
- Whether live tool updates are delivered in-place or via a coordinated worker lifecycle action is
  an architectural decision deferred to Step 2.
- Only local collection-backed servers derive tools from a collection; proxy servers derive tools
  from their upstream endpoint and must ignore collection refreshes.

### Main Business Entities

- **Backed Collection**: An operator-authored group of requests and collection variables that
  defines the tools exposed by one or more local MCP servers.
- **Isolated Collection Server**: A running standalone MCP server in isolated mode bound to a
  specific backed collection, with its own identity, endpoint, tool catalog, and variable context.
- **Collection Refresh Event**: An operator or workflow action indicating that a collection's
  requests or variables have changed and running servers backed by that collection must update.
- **Neighboring Server**: Any running server backed by a different collection or operating as an
  upstream proxy, whose availability and state must remain unaffected.

### User Scenarios

1. **Add and Edit Tools Live**: An operator starts an isolated server backed by a collection with
   one request, then adds a second request and edits the first request's path. Without restarting
   the server, an MCP client lists tools, sees both updated tools, and invokes the new tool.
2. **Remove a Tool Live**: An operator deletes a request from the backed collection. Subsequent
   tool discovery on the running isolated server no longer lists the removed tool, and calls to
   remaining tools continue working.
3. **Update Collection Variables**: An operator changes a collection variable used by a request in
   a running isolated server. After collection refresh, invoking the tool reflects the updated
   collection variable value without disturbing active environment variables.
4. **Unrelated Servers Unaffected**: Two isolated servers backed by different collections and one
   isolated proxy server are running. Refreshing the first collection updates only the first
   server; the second collection server and the proxy server continue serving uninterrupted.

## Q&A

**Q: Why is live collection refresh needed for isolated servers?**
A: Operators iteratively authoring API requests expect running MCP servers to reflect collection
edits immediately, just as shared-mode servers do, without manual server restarts.

**Q: Does this task prescribe how the isolated server applies the updated tool list?**
A: No. Step 1 defines the required operator-visible outcome; Step 2 decides the internal mechanism.
