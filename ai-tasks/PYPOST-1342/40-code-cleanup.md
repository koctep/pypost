# PYPOST-1342: Code Cleanup

## Static analysis

- Production modules changed (`pypost/models/models.py`,
  `pypost/core/mcp_tool_contract.py`, `pypost/ui/widgets/request_editor.py`): flake8 clean
  (line length ≤ 100, no unused imports).
- `make lint` currently fails in `lint-tests` on a **pre-existing** E501 in
  `tests/test_mcp_server_registry.py:308` (confirmed with our changes stashed). Not
  introduced by this task; tracked context matches PYPOST-1303 / registry test churn.

## Formatting and cleanup

- New `McpToolParam` helpers stay short; enum/items validation kept on the model and in
  `validate_mcp_argument_values`.
- UI Enum/Items cells reuse JSON serialize/parse with debug logs on coerce failure (same
  pattern as Default).
- No debug `print`s; no commented-out dead code added.

## Tests

- Module `pytestmark` timeouts retained (`test_mcp_tool_contract.py` 30s;
  `test_request_editor_mcp_params.py` 60s; GitHub/GitLab collection modules 30s).
- Focused suites green: MCP contract (incl. PYPOST-1342 repros), GitHub MCP, GitLab MCP,
  request-editor MCP params.

## Notes

- Collection JSON rewritten with `json.dumps(indent=2)` for the enum/items patches; key
  order may differ from prior hand formatting but content is valid import shape.
