# PYPOST-425: Architecture

## Current state (before)

- `MainWindow.apply_settings`: global QSS + `app.setFont` only (PYPOST-106).
- `EnvPresenter.apply_font`: loop over six env-bar widgets; called from `apply_settings`.

## Target state

Single propagation path for standard widgets:

1. `StyleManager.apply_styles(app, font_size=N)` — global QSS font-size rule.
2. `app.setFont(font)` after stylesheet — application default for inheritance.

Presenters store settings only; no per-widget font loops.

## Changes

| File | Change |
| --- | --- |
| `env_presenter.py` | Remove `apply_font`; `apply_settings` stores settings only |
| `test_env_presenter.py` | Remove `test_apply_font_sets_font_on_env_bar_widgets` |
| `test_apply_settings_font.py` | Remove stale `settings_btn` mock and comment |
| `doc/dev/*.md` | Update API references |

## Risks

- **Low**: Env bar widgets are standard `QWidget` descendants; global QSS + app font cover them.
- **Mitigation**: Existing `test_apply_settings_font.py` regression suite.
