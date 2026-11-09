# PYPOST-1535: MCP server impl RequestData identity failures

## Research

- Failures in `tests/test_mcp_server_impl.py` are `AssertionError` from
  `assertIs(passed_req, req)` / `assertIs(impl.tools_map[...], exposed)`.
  Printed objects match field-for-field (same `id`) but differ by Python
  identity.
- Root cause: commit `b10acf73` (PYPOST-1465) changed `MCPServerImpl.register_tools`
  from in-place `tools_map.clear()` + assign `item` to building `new_map` with
  `item.model_copy(deep=True)` then `self.tools_map = new_map`.
- Atomic map assignment is required so concurrent `list_tools` / `call_tool`
  never see a cleared map. Deep copy is not required for that property.
- Upstream isolation already copies:
  - `MCPServerRegistry` deep-copies collection requests before register/update.
  - Process workers decode tools into new model instances via IPC.
- `doc/dev/request_data_copy_policy.md` scopes deep copy to tab/editor isolation,
  not MCP `register_tools`.
- No tests assert that `register_tools` returns distinct copies; existing tests
  assert identity preservation.

## Implementation Plan

1. Keep atomic replacement: build `new_map`, assign `self.tools_map = new_map`.
2. Store the incoming `item` reference (no `model_copy`) when
   `expose_as_mcp` is true.
3. Leave call_tool, metrics, and IPC paths unchanged.
4. Document identity + atomic-swap contract in `doc/dev/mcp_process_isolation.md`.

**Failing Repro (Step 3):** Use the existing four red tests (no new fixture
needed). They already fail for the intended reason (identity after
`register_tools`). Repro command:

```bash
make test PYTEST_ARGS='tests/test_mcp_server_impl.py -k "register_tools_keeps or call_tool_invokes_request_service or call_tool_applies_mcp_param or call_tool_honors_explicit" --tb=short'
```

Sequencing: confirm red → remove deep copy → confirm green.

## Architecture

```mermaid
flowchart LR
  Caller["Caller tools list"] --> Register["register_tools"]
  Register --> NewMap["new_map[name] = item"]
  NewMap --> Swap["self.tools_map = new_map atomic"]
  Swap --> Call["call_tool uses tools_map entry"]
  Call --> Exec["RequestService.execute same RequestData"]
```

| Module | Responsibility |
| --- | --- |
| `pypost/core/mcp_server_impl.py` | Atomic `tools_map` replace; preserve tool object identity |
| Registry / IPC callers | Own isolation copies before register when needed |
| `tests/test_mcp_server_impl.py` | Contract tests for identity + execution wiring |

Pattern: atomic reference swap for concurrency safety; isolation at trust
boundaries (registry/IPC), not a second deep copy inside `register_tools`.

## Q&A

- **Q**: Why not keep deep copy and change tests to `assertEqual`?
  **A**: Double-copy is redundant with registry/IPC isolation and contradicts
  the documented identity contract in the unit tests. Atomic swap alone meets
  PYPOST-1465 concurrency needs.
