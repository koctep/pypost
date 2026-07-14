# PYPOST-681: Code Cleanup

## Changes

| File | Action |
| --- | --- |
| `pypost/core/mcp_server_impl.py` | 5-line addition in `format_structured_tool_result` |
| `tests/test_mcp_server_impl.py` | Three unit tests + assertion on existing integration test |

## Notes

- No new modules or imports.
- Follows existing sanitizer pattern used for `body` and `logs`.
