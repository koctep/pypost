# PYPOST-135: MCP tool arguments — architecture verification

## Verdict

**Already implemented.** No new architecture required for PYPOST-135.

## Current pipeline

### 1. Parameter discovery and schema (`list_tools`)

| Component | Role |
| --- | --- |
| `McpSecretsPolicy.extract_mcp_request_variables` | Regex discovery of `{{ mcp.request.VAR }}` in URL, headers, params, body |
| `resolve_mcp_param_specs` | Merges discovered names with `RequestData.mcp_params` (`McpToolParam`) |
| `McpSecretsPolicy.filter_agent_param_specs` | Removes env-only and hidden keys from agent contract (PYPOST-554) |
| `build_tool_input_schema` | Builds JSON Schema for `Tool.inputSchema` |

`MCPServerImpl._generate_schema` orchestrates the above; `list_tools` attaches schema to each
registered tool.

### 2. Argument execution (`call_tool`)

```
Agent call_tool(name, arguments)
        │
        ▼
MCPServerImpl._build_execution_variables(arguments)
        │  variable_supplier() → active env snapshot
        │  _merge_execution_variables(env, arguments)
        ▼
RequestService.execute(request, { **env, "mcp": { "request": arguments } })
        │
        ▼
TemplateService renders {{ mcp.request.* }} and {{ env_var }} placeholders
```

Module-level merge helper:

```python
def _merge_execution_variables(env_vars, mcp_args):
    return {**env_vars, "mcp": {"request": mcp_args}}
```

The `mcp` namespace wins over a flat env key named `mcp`.

### 3. Authoring and preview (UI)

| Field / feature | Module | Ticket |
| --- | --- | --- |
| `mcp_description`, `mcp_params` | `RequestData`, request editor MCP tab | PYPOST-553 |
| Agent contract preview | `mcp_tool_contract.py` | PYPOST-555 |
| Env var merge at execution | `MCPServerImpl`, `EnvPresenter` supplier | PYPOST-550 |

## Verification evidence

| Check | Location |
| --- | --- |
| Schema from placeholders + metadata | `tests/test_mcp_tool_contract.py` |
| Secrets policy filtering | `tests/test_mcp_secrets_policy.py` |
| `call_tool` merge and execution | `tests/test_mcp_server_impl.py` |
| Integration with mock client | `tests/test_mcp_server_integration.py` |

## Gaps found

None. PYPOST-135 acceptance criteria are satisfied by the existing implementation.
