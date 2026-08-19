# PYPOST-1080: Developer Documentation Report

## Documentation Updates

1. **`doc/dev/testing.md`**:
   - Added section `### MCP controller and presenter unit tests (PYPOST-1080)`.
   - Documented `tests/test_mcp_server_controller.py` coverage: deep copies, status delegation, activity logs (including KeyError fallback), create/update persist flows, running-server reconfigure, and lifecycle methods.
   - Documented `tests/test_mcp_controls_presenter.py` coverage: widget hierarchy, missing controller warning, `mcp_servers_dialog_opened` INFO log with count, 13 injected callables contract for `McpServersDialog`, activity dialog lifecycle, and legacy environment selection.
   - Documented module-level 30s timeout markers (`pytestmark = pytest.mark.timeout(30)`).

## Verification
- Ran `make lint` — markdown formatting and relative link checks passed cleanly.
