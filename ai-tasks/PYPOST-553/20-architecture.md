# PYPOST-553: Tool metadata authoring

## Research

### Current behavior

```137:148:pypost/core/mcp_server_impl.py
    def _generate_schema(self, req: RequestData) -> dict:
        ...
        for var in variables:
            properties[var] = {"type": "string"}
            required.append(var)
```

`list_tools` sets `description=req.name`. All `{{ mcp.request.VAR }}` placeholders from URL,
body, headers, and params become required string properties.

### Gap

No separate tool description; no per-parameter type, description, or optional flag.

## Design

### Model (`pypost/models/models.py`)

| Field | Type | Purpose |
| --- | --- | --- |
| `mcp_description` | `str` | Agent-visible tool description |
| `mcp_params` | `Dict[str, McpToolParam]` | Per-parameter metadata keyed by name |

`McpToolParam`: `type` (JSON Schema primitive), `description`, `required` (default `True`).

### Schema helpers (`mcp_server_impl.py`)

Pure functions (unit-tested):

- `_tool_description(req)` — `mcp_description.strip()` or `name`
- `_resolve_mcp_param_specs(req, discovered)` — merge template vars + explicit entries
- `_build_tool_input_schema(specs)` — JSON Schema object

### UI (`request_editor.py`)

New **MCP** tab:

- `QPlainTextEdit` for tool description
- `McpParamsTable` — Name, Type (combo), Description, Required (checkbox)

Wired through `load_data`, `update_request_data`, `get_request_data_from_ui`.

### Persistence

Add `mcp_description` and `mcp_params` to `_PERSISTED_FIELD_NAMES` in `request_sync.py`.
Pydantic defaults ensure old collection JSON loads without migration.

## Implementation plan

1. Add `McpToolParam` and `RequestData` fields.
2. Replace `_generate_schema` with helper-based builder; update `list_tools` description.
3. Add MCP tab + table widget.
4. Extend `test_mcp_server_impl.py`.
5. Update `doc/dev/mcp_integration.md`.

## Out of scope

- Auto-sync param table rows from template scan in UI (future UX polish).
- JSON Schema `enum` / nested object types.
