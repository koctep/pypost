# Common Workflows

## Ad-hoc API call

1. `Ctrl+N` — new tab.
2. Set method and URL (optionally with `{{ host }}`).
3. Add headers or body if needed.
4. **Send** (`F5`).
5. Search the response with `Ctrl+F` if the body is large.
6. Optionally **Save** into a collection.

## Dev vs Prod

1. Create two environments with the same variable names (`host`, `token`, …) but different
   values.
2. Write requests only with placeholders, never hard-coded hosts.
3. Switch the top dropdown before sending or before an MCP agent session.

## Capture an auth token

1. Send a login request that returns JSON with a token.
2. On **Script**:

   ```python
   pypost.env.set('auth_token', response.json()['token'])
   ```

3. Mark `auth_token` as **Hidden** in **Manage Environments**.
4. On later requests set header `Authorization: Bearer {{ auth_token }}`.

## Expose an API to Cursor

To start from a shipped example instead of building requests from scratch, import the
[Jira Cloud MCP pair](../../examples/README.md) (or another fixture under `examples/`).

1. Build and test the request in the GUI until **Send** succeeds.
2. Check **MCP Tool**, fill the **MCP** tab, add `{{ mcp.request.* }}` for agent inputs.
3. Save the request.
4. Check **Enable MCP (Model Context Protocol)** on the environment the agent should use.
5. Confirm **MCP: ON (host:port)** in the top bar.
6. Point Cursor at `http://127.0.0.1:1080/mcp` (Streamable HTTP).
7. Ask the agent to list tools and call one; verify it parses the JSON envelope.

Full reference: [MCP Tools](mcp-tools.md) and [MCP Integration](../mcp_integration.md).

## Debug agent usage

1. Keep a single environment selected.
2. Open **MCP Tools** to confirm names and count.
3. Watch **MCP Activity** for `list_tools` / `call_tool`.
4. Re-run the same request with **Send** in PyPost if a tool call fails.

## Reuse from the shell

1. **Actions → Copy cURL** for the current draft, or
2. History → copy the executed entry as cURL.
3. Paste into a terminal. Redact secrets before sharing.

## Operator metrics

With PyPost running:

```bash
curl -s http://127.0.0.1:9080/metrics | head
```

See [Prometheus Monitoring](../prometheus_monitoring.md).
