# Architecture: PYPOST-1084

## Overview

Refactor `McpServerSettingsController` constructor signature and internal collaborator wiring to directly accept and forward `collection_lookup: Callable[[str], Collection | None]`.

## Component Changes

### 1. `pypost/ui/mcp_server_controller.py`

#### Constructor
```python
def __init__(
    self,
    *,
    settings_provider: Callable[[], AppSettings],
    config_manager: ConfigManager,
    collection_lookup: Callable[[str], Collection | None],
    environment_lookup: Callable[[str], Environment | None],
    metrics: MetricsTrackerProtocol,
    template_service: TemplateService,
    mcp_manager: MCPServerManager | None = None,
    registry: MCPServerRegistry | None = None,
) -> None:
    self._settings_provider = settings_provider
    self._config_manager = config_manager
    ...
    if registry is not None:
        self.registry = registry
    else:
        self.registry = MCPServerRegistry(
            collection_lookup=collection_lookup,
            environment_lookup=environment_lookup,
            metrics=metrics,
            template_service=template_service,
        )
```

#### Composition Root Factory (`for_window`)
```python
@classmethod
def for_window(
    cls,
    window: MainWindow,
    *,
    mcp_manager: MCPServerManager | None = None,
    registry: MCPServerRegistry | None = None,
) -> McpServerSettingsController:
    return cls(
        settings_provider=lambda: window.settings,
        config_manager=window.config_manager,
        collection_lookup=lambda collection_id: window.collections.collection_by_id(
            collection_id
        ),
        environment_lookup=lambda environment_id: window.env.environment_by_id(
            environment_id
        ),
        metrics=window.metrics,
        template_service=window.template_service,
        mcp_manager=mcp_manager,
        registry=registry,
    )
```

#### Removal of Dead Code
- Remove `self._collections_provider`
- Remove `self._get_collections`
- Remove `_collection_by_id(self, collection_id: str) -> Collection | None`

### 2. Test Updates

- In `tests/test_main_window.py`:
  - `_make_mcp_controller`: pass `collection_lookup=lambda _id: None`.
- In `tests/test_mcp_server_controller.py`:
  - Update test fixtures / helper / inline calls from `collections_provider=lambda: None, get_collections=lambda: []` to `collection_lookup=lambda _id: None`.
  - Update `test_collection_by_id_uses_presenter_and_fallback` to verify `collection_lookup` wiring.
