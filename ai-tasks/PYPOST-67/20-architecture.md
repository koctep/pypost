# PYPOST-67: Architecture — public env refresh API

## Current flow (before)

```
MainWindow.open_settings()
  └─ apply_settings(...)
  └─ env._on_env_changed(env.env_selector.currentIndex())  ← private + widget leak
```

## Target flow

```
MainWindow.open_settings()
  └─ apply_settings(...)
  └─ env.reload_current_env()  ← public API

EnvPresenter.reload_current_env()
  └─ _on_env_changed(self._env_selector.currentIndex())  ← internal only
```

## Changes

| Component | Change |
|-----------|--------|
| `env_presenter.py` | Add `reload_current_env() -> None` |
| `main_window.py` | Replace private call with `reload_current_env()` |
| `test_env_presenter.py` | Unit test for public method |
| E2E settings tests | Patch `reload_current_env` instead of `_on_env_changed` |

## Backward compatibility

- Behavior identical: same index resolution, MCP start/stop, signal emissions, config save.
- `_on_env_changed` remains the internal handler for combo `currentIndexChanged` and other
  in-class call sites.
