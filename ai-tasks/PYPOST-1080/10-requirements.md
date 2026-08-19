# PYPOST-1080: Add Dedicated Test Modules for mcp_server_controller.py and mcp_controls_presenter.py

## Goals

When `pypost/ui/mcp_server_controller.py` and `pypost/ui/presenters/mcp_controls_presenter.py` were extracted from `MainWindow` and `EnvPresenter` (PYPOST-1071), they were covered only indirectly through integration tests. Specific branches and error handling paths remained without dedicated test coverage.

This task aims to:
1. Create `tests/test_mcp_server_controller.py` to directly test all controller behaviors, state queries, error flows, and lifecycle methods.
2. Create `tests/test_mcp_controls_presenter.py` to directly test toolbar wiring, presenter event handling, dialog launching, and logging.
3. Explicitly verify uncovered branches identified in PYPOST-1071 tech debt:
   - `mcp_server_activity` KeyError branch (`mcp_server_controller.py:126-135`) returning `[]` and logging debug.
   - `upsert_mcp_server` create vs update persist path (`mcp_server_controller.py:148-156`).
   - `_open_mcp_servers` (`mcp_controls_presenter.py:283-311`) including missing controller warning, `McpServersDialog` construction with 13 injected callables, and the `mcp_servers_dialog_opened` INFO log assertion.
4. Ensure all new test modules include explicit timeout markers per project testing standards.

## User Stories

- **As a Developer/Maintainer**, I want dedicated unit test modules for `McpServerController` and `McpControlsPresenter` so that regression bugs in MCP server lifecycle, persistence, and UI wiring are caught early and precisely.
- **As a System Architect**, I want full branch coverage over MCP controller error paths (such as missing activity log instances) and presenter dialog invocations.

## Definition of Done

1. **`tests/test_mcp_server_controller.py` created and passing**:
   - Tests `mcp_server_configurations` (deep copies, independence from settings mutations).
   - Tests `mcp_server_status` delegation to registry.
   - Tests `mcp_server_activity` when manager exists vs when `KeyError` is raised (returns `[]` and logs debug).
   - Tests `upsert_mcp_server` for new server (create path), existing stopped server (update path), and running server (`reconfigure` path).
   - Tests `remove_mcp_server`, `start_mcp_server`, `stop_mcp_server`.
   - Tests save failure error handling and callback dispatch.
2. **`tests/test_mcp_controls_presenter.py` created and passing**:
   - Tests presenter initialization and toolbar control attachments.
   - Tests `_open_mcp_servers` when `_mcp_server_controller` is None (logs warning) and when present (logs INFO `mcp_servers_dialog_opened` with server count, constructs dialog with 13 callables).
   - Tests `_open_mcp_activity` and dialog lifecycle.
   - Tests activity recording badge updates and legacy environment filtering.
3. **Explicit Timeout Markers**:
   - Both test modules define `pytestmark = pytest.mark.timeout(...)`.
4. **Code Quality**:
   - All tests pass cleanly without regressions. `make lint` passes.

## Task Description

- **Problem**: Key branches in `McpServerController` and `McpControlsPresenter` lacked dedicated test assertions, leaving UI lifecycle and error recovery untested in isolation.
- **Business Objective**: Complete test coverage and maintainability for extracted MCP UI architecture.
- **Constraints**: No production code changes required unless a genuine defect is discovered during test writing.

## Q&A

- **Q: Are Qt dependencies needed in the presenter test module?**
  - A: Yes, `McpControlsPresenter` interacts with Qt toolbar actions and dialogs, so `QApplication` fixture support is used as standard in UI tests.
- **Q: Should log emissions be asserted?**
  - A: Yes, `caplog` / log assertions verify `mcp_servers_dialog_opened` and `mcp_servers_dialog_no_controller`.
