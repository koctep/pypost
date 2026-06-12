# UI Font Size and Global Styles (PYPOST-106)

## Overview

Application font size is a user setting (`AppSettings.font_size`, default 12). It must apply
across the main window after startup and whenever Settings are saved.

## Architecture

Two mechanisms work together:

1. **Global QSS** — `StyleManager.apply_styles(app, font_size=N)` appends
   `QWidget { font-size: Npt; }` to the loaded stylesheets before
   `QApplication.setStyleSheet()`.
2. **Application default font** — `MainWindow.apply_settings` then reads `app.font()`, sets
   point size, and calls `app.setFont(font)`.

Call order matters: **stylesheet first, then `setFont`** (see PYPOST-404). Qt's
`setStyleSheet()` re-polish resets the application font if `setFont` ran earlier.

## API / Usage

### `StyleManager.apply_styles(app_or_widget, font_size=None)`

Loads `pypost/ui/styles/*.qss`, optionally appends the global font-size rule, and applies the
combined sheet to the given `QApplication` or widget.

### `MainWindow.apply_settings(settings: AppSettings)`

Delegates font work to `style_manager.apply_styles(app, font_size=settings.font_size)` and
`app.setFont`. Does **not** call `setFont` on individual child widgets.

## Configuration

- Settings UI: Settings dialog → Application Font Size (8–48).
- Persisted in user config via `ConfigManager` / `StateManager`.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Font size wrong on startup | `setFont` called before `apply_styles` — check call order |
| One widget ignores size | Widget has local `setStyleSheet` with fixed `font-size` |
| Font resets after show | `showEvent` re-applies settings via `QTimer.singleShot(0, ...)` — intentional |

## Related

- PYPOST-404 — startup font size bug (call-order fix)
- PYPOST-106 — removed manual per-widget `setFont` loop in `MainWindow`
- PYPOST-425 — removed redundant `EnvPresenter.apply_font` widget loop
- PYPOST-114 — `QToolTip` QSS hook for variable hover and widget tooltips
- `doc/dev/ui_mixins.md` — variable hover tooltip styling
- `doc/dev/tech-debt/PYPOST-11.md` — menu padding QSS for large fonts

## Tooltip styling

Variable hover tooltips (`QToolTip.showText` in `VariableHoverMixin`) and widget
`setToolTip` strings share the global `QToolTip` rule in `pypost/ui/styles/main.qss`.
Edit that block to change tooltip colors; use palette roles for theme compatibility.
