# PYPOST-68: Architecture — EnvPresenter widget encapsulation

## Before

```
MainWindow.apply_settings (PYPOST-106 removed loop, properties remain)
  └─ env.env_selector.setFont(font)  ← via property leak

Tests / e2e
  └─ presenter.env_selector.*  ← direct widget access
```

## After

```
MainWindow.apply_settings
  └─ env.apply_settings(settings)
       └─ apply_font(QApplication.font())

Tests / e2e
  └─ presenter.select_environment_index(1)
  └─ presenter.environment_at(1)
  └─ presenter.mcp_status_text()
```

## Changes

| Component | Change |
|-----------|--------|
| `env_presenter.py` | Remove 6 widget properties; add `apply_font`, query/intent methods |
| `test_env_presenter.py` | Use public API; unit setup uses `_env_selector` where needed |
| E2E tests | Use `select_environment_index`, `environment_at`, etc. |

## Public API added

- `apply_font(font: QFont) -> None`
- `select_environment_index(index: int) -> None`
- `current_environment_index() -> int`
- `environment_count() -> int`
- `environment_display_name_at(index: int) -> str`
- `environment_at(index: int) -> Environment | None`
- `mcp_status_text() -> str`
- `mcp_tools_button_text() -> str`
- `mcp_activity_button_text() -> str`

## Backward compatibility

- User-visible behavior unchanged.
- `widget` property retained for top-bar layout.
