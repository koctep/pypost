# PYPOST-719: Architecture

## Test Strategy

Two complementary layers in `tests/test_mcp_server_manager.py`:

| Layer | Class | Approach |
|-------|-------|----------|
| Unit (pure) | `TestMCPServerManagerUnit` | Mock `create_app`, `uvicorn.Server.serve`; call internal methods directly |
| Integration | `TestMCPServerManagerStartup`, `TestMCPServerManagerUpdateTools` | Real uvicorn on ephemeral ports |

## New Tests Added

| Test | Covers |
|------|--------|
| `test_activity_log_property_returns_same_instance` | `activity_log` property (line 66) |
| `test_emit_activity_emits_activity_recorded_signal` | `_emit_activity` (line 69) |
| `test_set_hidden_keys_supplier_forwards_to_impl` | `set_hidden_keys_supplier` (lines 80–81) |
| `test_init_with_template_service_logs_debug` | TemplateService propagation log (line 54) |
| `test_generic_exception_in_run_uvicorn_emits_start_failed` | `except Exception` handler (lines 189–191) |
| `test_start_server_stops_existing_server_when_already_running` | restart path (line 85) |
| `test_unexpected_server_exit_emits_false_and_warns` | unexpected exit warning (lines 197–199) |
