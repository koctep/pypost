# Inbound MCP Trust Model (PYPOST-705)

PyPost exposes two inbound MCP surfaces when enabled:

| Surface | Default bind | Purpose |
| --- | --- | --- |
| Request tools (`MCPServerImpl`) | `127.0.0.1:1080` | Execute collection HTTP requests as MCP tools |
| Metrics (`MetricsServer`) | `127.0.0.1:9080` | Prometheus scrape + observability MCP resources |

## Trust boundary

**Default posture: local trust.** Both servers default to loopback (`127.0.0.1`). Any process
on the same machine can call `list_tools` / `call_tool` without presenting credentials.
PyPost does **not** implement inbound MCP client authentication today.

Operators are expected to treat network MCP like a **local privilege boundary**:

- Only trusted users and agents on the same host should reach loopback endpoints.
- Binding to `0.0.0.0`, a LAN IP, or a hostname reachable from other machines **exposes
  unauthenticated** tool execution and (for metrics) unauthenticated `/metrics` scraping.

When metrics bind outside loopback, PyPost logs `metrics_server_non_localhost_bind` (WARNING).
Request MCP has no equivalent runtime warning — use Settings → Server bind fields deliberately.

## What agents can do

With network access to the MCP endpoint, a client can:

1. Discover all `expose_as_mcp` tools (`list_tools`).
2. Invoke any tool with agent-supplied `mcp.request.*` arguments (`call_tool`).
3. Trigger real HTTP requests using the **active environment** (including hidden env values
   merged at execution — see [mcp_secrets_policy.md](mcp_secrets_policy.md)).
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

A future enhancement may add optional bearer-token validation on inbound MCP HTTP when
`mcp_host` or `metrics_host` is not loopback. Until then, **network exposure = full trust**
for anyone who can reach the bind address.

Related: [security_audit.md](security_audit.md) (T-004), [mcp_integration.md](mcp_integration.md).
