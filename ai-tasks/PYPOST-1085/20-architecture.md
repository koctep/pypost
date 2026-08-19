# Architecture: PYPOST-1085

## Design Changes

### 1. `McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`)

- Remove `from pypost.ui.main_window import MainWindow` in `TYPE_CHECKING`.
- Remove `for_window(cls, window: MainWindow, ...)` classmethod.
- Controller is now completely decoupled from `MainWindow`.

### 2. `MainWindow` (`pypost/ui/main_window.py`)

- Replace `McpServerSettingsController.for_window(...)` with direct constructor call:
```python
self.mcp_controller = McpServerSettingsController(
    settings_provider=lambda: self.settings,
    config_manager=self.config_manager,
    collection_lookup=lambda collection_id: self.collections.collection_by_id(
        collection_id
    ),
    environment_lookup=lambda environment_id: self.env.environment_by_id(
        environment_id
    ),
    metrics=self.metrics,
    template_service=self.template_service,
    mcp_manager=mcp_manager,
    registry=mcp_registry,
)
```
- Remove `self.mcp_manager = self.mcp_controller.manager` and `self.mcp_registry = self.mcp_controller.registry`.
- Pass `self.mcp_controller.manager` and `mcp_registry=self.mcp_controller.registry` into `EnvPresenter`.

### 3. Composition Root (`pypost/main.py`)

- Update `composed.mcp_registry` assignment to `window.mcp_controller.registry`.

### 4. Tests and Dev Docs

- In `tests/test_main_window.py`: assert `window.mcp_controller.manager` and verify `hasattr(window, 'mcp_manager')` is `False`.
- Update `doc/dev/` references.
