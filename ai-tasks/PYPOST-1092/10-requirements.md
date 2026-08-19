# PYPOST-1092: MCP Proxy: Forward requests to upstream MCP servers with env variable header resolution

## Goals

PyPost supports local MCP server capabilities, enabling AI agents to discover and execute tools, access prompts, and read resources. However, modern workflows increasingly rely on external, distributed, or cloud-hosted upstream MCP servers (such as internal enterprise microservices, specialized domain tools, or remote agent endpoints).

To integrate with these external services securely and seamlessly, PyPost needs to act as a transparent MCP Proxy. Users and AI agents need the ability to configure upstream MCP endpoints in PyPost and route standard MCP protocol operations through PyPost to those upstream servers.

Additionally, upstream servers often require authentication credentials, API keys, or tenant tokens (such as `Authorization: Bearer <token>` or `X-API-Key: <key>`). These credentials vary per environment (e.g. staging vs. production) and must not be hardcoded or exposed to AI agents or unmasked logs. PyPost must allow defining custom HTTP request headers for upstream MCP servers that dynamically resolve variable values from active PyPost environments while strictly enforcing secret masking and security policies.

**Implementation language**: Python (integrated within the existing PyPost application; no new language runtime required).

## User Stories

- As an API developer / workspace user, I want to configure external upstream MCP servers in PyPost by providing their target endpoint URL and transport mode (Streamable HTTP / SSE), so that my agent or PyPost client can access remote MCP capabilities.
- As a security-conscious engineer, I want to attach custom authentication headers (e.g., `Authorization`, `X-API-Key`) with dynamic environment variable placeholders (e.g., `{{ API_KEY }}`) to upstream MCP configurations, so that sensitive tokens are resolved at request time from my active environment without hardcoding secrets.
- As an AI agent or client communicating with PyPost, I want PyPost to transparently forward standard MCP operations (`list_tools`, `call_tool`, prompt operations, and resource operations) to the upstream server and return the results as standard MCP responses, so that I can use upstream tools seamlessly without needing custom upstream adapters.
- As an operator inspecting PyPost MCP activity, I want all forwarded proxy calls recorded in the MCP activity log with execution metadata (operation, outcome, latency, HTTP status), while ensuring resolved secret values and sensitive header tokens are consistently masked in the UI and logs.
- As an end user or agent encountering network hiccups or upstream failures, I want PyPost to gracefully handle connection errors, invalid endpoints, and timeouts by returning structured, standardized MCP error responses instead of crashing or hanging indefinitely.

## Definition of Done

- Users can create, view, edit, and remove upstream MCP proxy target configurations specifying target URL, transport mode (Streamable HTTP or Server-Sent Events / SSE), and optional custom HTTP headers.
- Custom headers support dynamic variable substitution using standard PyPost template syntax (e.g. `{{ VAR }}` or `{{ bearer_token }}`), resolving against the currently active environment variables when forwarding requests.
- All MCP protocol requests (including `list_tools`, `call_tool`, prompts, and resources) received by PyPost targeting an upstream proxy server are faithfully forwarded to the upstream server over the configured transport, and responses/errors are relayed back to the client.
- Sensitive header values, authentication tokens, and secret environment variables are automatically masked in user-facing activity logs, inspect dialogs, and diagnostic views in compliance with PyPost's MCP secrets policy.
- Network connection failures, DNS resolution errors, upstream HTTP errors, and request timeouts are trapped and mapped to clear, standardized MCP error responses with appropriate error codes/messages.
- Comprehensive automated tests verify header resolution, environment substitution, secret masking, and proxy request/response forwarding across standard MCP workflows.
- User and developer documentation is updated to describe configuring upstream MCP servers, header templating, and security practices.

## Task Description

PyPost currently provides local MCP tooling capabilities. This task expands PyPost's MCP feature set by introducing an MCP Proxy capability to forward MCP protocol calls to upstream servers.

### Functional Scope

1. **Upstream Server Target Management**:
   - Configure upstream MCP targets with a user-friendly name, target endpoint URL, and transport type (Streamable HTTP, Server-Sent Events / SSE).
   - Configure zero or more custom HTTP headers for each upstream target.

2. **Dynamic Header Resolution**:
   - Header values can contain environment variable expressions using PyPost template syntax (`{{ VAR }}`).
   - During proxy execution, PyPost evaluates these expressions against the currently active environment's variable values.
   - If an environment variable is missing or cannot be resolved, an informative error is generated and the request is prevented from sending unauthenticated or malformed requests.

3. **Transparent Protocol Proxying**:
   - Forward all MCP protocol requests (`list_tools`, `call_tool`, prompts list/get, resources list/read) to the target upstream endpoint.
   - Support both Streamable HTTP and SSE transport protocols as required by the MCP specification.
   - Preserve tool parameters, execution arguments, and payload structures transparently.

4. **Security, Secrets Management & Activity Logging**:
   - Sensitive headers (e.g., `Authorization`, `X-API-Key`, `Proxy-Authorization`) and resolved secret values must never be exposed in plaintext in activity logs or UI views.
   - Inbound proxy operations are recorded in the MCP Activity Log with key operational metrics (operation name, duration, outcome, HTTP status, and sanitized details).

5. **Error Handling & Timeouts**:
   - Configurable or sensible default request timeouts to avoid indefinite hanging on unresponsive upstream servers.
   - Standardized mapping of network errors (connection refused, host unreachable, DNS failure, timeout) and upstream HTTP errors (4xx, 5xx) to structured MCP protocol error responses.

### Boundaries and Out of Scope

- Modifying upstream server implementations or non-MCP HTTP proxying.
- Caching of tool execution results (proxying is real-time and transparent).
- Implementing new transport mechanisms beyond Streamable HTTP and SSE for MCP proxying.

## Non-Functional Requirements

- **Security & Privacy**: Strict adherence to secrets masking. Secrets from environment variables and sensitive HTTP headers must be masked in logs, UI, and diagnostics.
- **Reliability & Fault Tolerance**: Robust timeout management and exception isolation ensuring that an unreachable upstream server does not degrade other local PyPost operations or UI responsiveness.
- **Performance & Latency**: Minimal proxy overhead when resolving headers and relaying payloads between client and upstream.
- **Compatibility**: Adherence to standard Model Context Protocol (MCP) specifications for Streamable HTTP and SSE transports.

## Main Entities

- **Upstream MCP Proxy Configuration**: Represents the configuration settings for an external MCP server, including target URL, transport protocol (Streamable HTTP / SSE), active/enabled status, and associated custom headers.
- **Custom Proxy Header**: A key-value pair associated with an upstream target where the value may contain template variables to be evaluated dynamically at request time.
- **Active Environment Context**: The current set of environment variables supplied by the selected PyPost environment, used to resolve header placeholders.
- **Proxy Request / Response Exchange**: A single MCP operation forwarded to the upstream server, encapsulating the inbound MCP call, resolved outgoing HTTP request, upstream response, and mapped MCP result.
- **MCP Activity Record**: An auditable log entry capturing the forwarded operation type, timestamp, execution duration, success/error outcome, and sanitized operational detail.

## User Scenarios

1. **Configuring a Cloud MCP Server with Bearer Auth**:
   - A user opens the MCP Server configuration, adds a new upstream target with URL `https://mcp.internal.example.com/mcp` and transport `Streamable HTTP`.
   - The user adds a custom header `Authorization` with value `Bearer {{ MCP_ACCESS_TOKEN }}`.
   - When an AI agent executes a tool on this upstream server, PyPost resolves `MCP_ACCESS_TOKEN` from the active environment, sends the authenticated request to the upstream server, and returns the tool output to the agent.
   - The activity log displays the operation as successful, with the header token masked.

2. **Upstream Server Outage / Timeout**:
   - An AI agent requests `list_tools` for an upstream MCP server whose endpoint is unreachable or down.
   - PyPost attempts connection, times out according to the configured timeout limit, and returns a standard MCP error payload detailing the connectivity failure.
   - The activity log records the failure outcome and duration without crashing the application.

3. **Missing Environment Variable for Header**:
   - A user executes a request against an upstream target requiring `{{ PROD_API_KEY }}`, but the currently selected environment does not define `PROD_API_KEY`.
   - PyPost detects the unresolvable variable, halts the request before dispatching, and returns a clear error indicating the missing variable.

## Q&A

| Question | Answer |
| --- | --- |
| What is the primary business motivation for this task? | To enable PyPost users and AI workflows to seamlessly leverage external and centralized MCP services with secure, per-environment credential management. |
| Which transport types must be supported for upstream proxying? | Streamable HTTP and Server-Sent Events (SSE), consistent with the standard MCP specification. |
| How are custom headers resolved dynamically? | Using PyPost's standard template syntax `{{ VAR_NAME }}` against the variables defined in the currently active PyPost environment. |
| What are the security rules regarding header tokens? | All sensitive headers and resolved environment secret values must be masked in activity logs, diagnostics, and UI inspection tools following PyPost's MCP secrets policy. |
