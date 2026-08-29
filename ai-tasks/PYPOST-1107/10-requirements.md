# PYPOST-1107: Retire EnvPresenter.set_mcp_server_controller and Direct Controller Wiring

## Goals

Ensure clean boundary separation and direct configuration between application lifecycle coordinators and MCP UI controls by removing redundant legacy passthrough shims from `EnvPresenter`.

From a maintenance and design perspective:
- Eliminates dual-path controller configuration ambiguity during application initialization.
- Enforces single-responsibility principle: `EnvPresenter` manages environment selection and variables, while `McpControlsPresenter` directly receives its lifecycle/server controller from the main window coordinator.
- Simplifies test doubles and verification harnesses by removing unnecessary shim methods.

## User Stories

- **As a maintainer**, I want `MainWindow` and related test doubles to configure `McpControlsPresenter` directly rather than through `EnvPresenter`, so that the environment presenter is not polluted with unrelated MCP controller passthrough methods.
- **As a developer**, I want clean and unambiguous API surfaces on presenters so that future refactorings (such as top-bar composition decoupling) can proceed with minimal coupling.

## Definition of Done

1. `EnvPresenter.set_mcp_server_controller` is completely removed.
2. `MainWindow` configures the server controller directly via `self.mcp_controls.set_server_controller(self.mcp_controller)`.
3. Test doubles and test suites (including encrypted startup tests and verification artifact contracts) are updated to configure / expect `mcp_controls.set_server_controller` without relying on `set_mcp_server_controller` on environment presenters.
4. Developer documentation (`doc/dev/`) is updated to reflect direct MCP controls configuration.
5. All automated checks (`make check`) pass cleanly.

## Task Description

In previous refactorings (PYPOST-1082), `McpControlsPresenter` was extracted from `EnvPresenter`, but `EnvPresenter.set_mcp_server_controller` was temporarily preserved as a backward-compatibility passthrough shim for `MainWindow` initialization and deferred test doubles.

This task completes the retirement of this passthrough shim:
- Remove `set_mcp_server_controller` from `EnvPresenter`.
- Update `MainWindow.__init__` to wire `self.mcp_controls.set_server_controller(self.mcp_controller)` directly.
- Update test doubles (such as `_DeferredEnvPresenter` / encrypted startup test fixtures) and verification artifact tests to reflect the direct wiring.
- Update developer docs referencing the legacy wiring pattern.

## Non-Functional Requirements & Constraints

- **Language**: Python
- **Quality Gates**: All flake8, doc linter, mypy type checks, and pytest suites must pass via `make check`.
- **Backward Compatibility / Regression**: Application startup and MCP server management lifecycle in `MainWindow` must remain fully operational without regression.
- **Top-Down Step Boundaries**: Requirements phase establishes scope and acceptance criteria without implementing code changes prior to Steps 2–4.

## Main Entities

- **MainWindow Coordinator**: Coordinates top-level application startup, presenters, and service controllers.
- **EnvPresenter**: Manages environment variables, environment selection, and top bar environment selector UI.
- **McpControlsPresenter**: Manages MCP server status, tools button, and MCP server management lifecycle dialog interactions.
- **McpServerController**: Coordinates MCP server management persistence and lifecycle operations.

## Q&A

- **Q**: Why was `set_mcp_server_controller` on `EnvPresenter` in the first place?
  - **A**: Historically `EnvPresenter` contained all MCP controls logic. During presenter separation in PYPOST-1082, the method was kept as a delegator shim to avoid touching multiple startup test doubles at once.
- **Q**: Does retiring this method affect environment variable injection or switching?
  - **A**: No. MCP server controller wiring is purely for server management and tool discovery lifecycle; environment variable management remains untouched.
