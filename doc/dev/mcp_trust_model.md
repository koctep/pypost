# Inbound MCP Trust Model (PYPOST-705)

PyPost exposes two inbound MCP surfaces when enabled:

| Surface | Default bind | Purpose |
| --- | --- | --- |
| Request tools (`MCPServerImpl`) | Per MCP Servers row (default conversion values: `127.0.0.1:1080`) | Execute one selected collection's HTTP requests as MCP tools |
| Metrics (`MetricsServer`) | `127.0.0.1:9080` | Prometheus scrape + observability MCP resources |

Agent UI drive (`pypost.agent.ui_actions`) is **not** a product inbound MCP
surface. Out-of-process agent-UI MCP is a **separate trust boundary** from
request-tool MCP; packaging path is documented in
[ui_actions.md](ui_actions.md) (PYPOST-918). Do not expand request-tool blast
radius with UI automation — UI tools must never appear on `MCPServerImpl`.

## Agent-UI attach / sidecar (ATTACH-1)

The agent-UI stdio sidecar ([agent_ui_actions_mcp.md](agent_ui_actions_mcp.md))
can use **spawn-session** (sidecar-owned session) or **attach** (bind to an
already-running desktop). Attach is a separate surface from product MCP:

| Concern | Guidance |
| --- | --- |
| Product MCP | Collection request tools only; no `ui_*` tools |
| Attach / sidecar | Drives live (or spawned) UI on the agent-UI surface |
| Local-host posture | Same-machine privilege; treat like local shell access |
| Surfaces | Do **not** merge agent-UI and product MCP catalogs |

Local-host posture means whoever can run or reach the sidecar can drive the
bound desktop — not a weaker remote API. Aligns in spirit with the local-trust
posture below without merging blast radii. Operator path, lifecycle, and soft
contract: [agent_ui_actions_mcp.md](agent_ui_actions_mcp.md). Capability:
[PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207).

## Trust boundary

**Default posture: local trust.** Both servers default to loopback (`127.0.0.1`). Any process
on the same machine can call `list_tools` / `call_tool` without presenting credentials.
PyPost does **not** implement inbound MCP client authentication today.

Operators are expected to treat network MCP like a **local privilege boundary**:

- Only trusted users and agents on the same host should reach loopback endpoints.
- Binding to `0.0.0.0`, a LAN IP, or a hostname reachable from other machines **exposes
  unauthenticated** tool execution and (for metrics) unauthenticated `/metrics` scraping.

When metrics bind outside loopback, PyPost logs `metrics_server_non_localhost_bind` (WARNING).
Request MCP has no equivalent runtime warning — choose each MCP Servers row's bind address
deliberately.

## Metrics MCP surface (PYPOST-712)

`MetricsServer` exposes **two unauthenticated endpoints** on the metrics bind address:

| Path | Protocol | Data exposed |
| --- | --- | --- |
| `/metrics` | HTTP GET | Full Prometheus text exposition (request counts, MCP activity, etc.) |
| `/mcp` | MCP Streamable HTTP | `metrics://all` resource — same scrape payload to MCP clients |

**Hardening shipped:**

- `AppSettings.metrics_host` defaults to `127.0.0.1` (PYPOST-704).
- Non-loopback bind emits `metrics_server_non_localhost_bind` WARNING at startup.
- Trust model documented here and in [security_audit.md](security_audit.md).

**Not implemented:** bearer-token or mTLS on metrics HTTP/MCP. Keep metrics on loopback or
front with an authenticated reverse proxy when remote scrape is required.

## What agents can do

With network access to the MCP endpoint, a client can:

1. Discover all `expose_as_mcp` tools (`list_tools`).
2. Invoke any tool with agent-supplied `mcp.request.*` arguments (`call_tool`).
3. Trigger real HTTP requests using the endpoint's selected environment snapshot (including
   hidden env values merged at execution — see [mcp_secrets_policy.md](mcp_secrets_policy.md)).
4. Receive **sanitized** upstream response bodies and script logs (PYPOST-703).

Agents **cannot** read hidden env key names/values from `list_tools` schemas. They **can**
still cause PyPost to **use** hidden values when executing tools.

## Operator guidance

| Scenario | Recommendation |
| --- | --- |
| Local Claude Desktop / Cursor on same machine | Keep default `127.0.0.1` bind; no extra auth needed |
| Remote agents or shared network | Do **not** expose MCP without a reverse proxy, VPN, or host firewall; token auth is not built in |
| Metrics on shared LAN | Keep `metrics_host` on loopback; scrape via local agent or SSH tunnel |
| Multi-user workstation | Treat MCP as equivalent to shell access — any local user can invoke tools |

## Future authentication (not implemented)

A future enhancement may add optional bearer-token validation on inbound MCP HTTP when an
MCP Servers row's `host`, or `metrics_host`, is not loopback. Until then, **network exposure
= full trust** for anyone who can reach the bind address.

Related: [security_audit.md](security_audit.md) (T-004), [mcp_integration.md](mcp_integration.md).
