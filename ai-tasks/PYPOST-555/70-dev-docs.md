# PYPOST-555: Dev Docs

## Updated

- `doc/dev/mcp_integration.md` — agent contract preview section under Tool metadata authoring.

## Summary for developers

- `pypost/core/mcp_tool_contract.py` is the single source for tool name normalization,
  description fallback, param spec merge, JSON Schema build, and UI preview.
- `RequestWidget` MCP tab shows `format_mcp_tool_contract_preview` output when **MCP Tool** is
  checked.
- Preview uses `TabsPresenter`-injected `TemplateService` and active `hidden_keys` from
  `set_hidden_keys`.
