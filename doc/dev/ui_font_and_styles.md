# UI Font Size and Global Styles (PYPOST-106, PYPOST-112)

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

## Font inheritance investigation (PYPOST-112)

PYPOST-12 added manual `setFont` calls in `apply_settings` because inheritance appeared broken
after global stylesheet application. Investigation (PYPOST-112) identified these causes:

| Cause | Mitigation |
| --- | --- |
| `setStyleSheet()` re-polish resets `QApplication` font | Apply stylesheet before `app.setFont` (PYPOST-404) |
| Global QSS without explicit `font-size` | `StyleManager` appends `QWidget { font-size: Npt; }` (PYPOST-106) |
| Widget-local QSS with fixed `font-size` | Local rules win; optional per-widget audit |
| `CodeEditor` tab/gutter metrics | `_refresh_font_metrics` on `QEvent.FontChange` (PYPOST-107) |

`MainWindow.apply_settings` no longer loops over child widgets. Presenter `apply_settings`
methods handle indent and syntax colours only. No further refactor is required for main-window
font propagation.

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

## Body editor (`CodeEditor`)

Request body tabs use `CodeEditor`, which inherits application font size from global QSS and
`QApplication.setFont`. The editor does **not** receive manual `setFont` from
`TabsPresenter`.

When font metrics change (`QEvent.FontChange`), `CodeEditor._refresh_font_metrics` recalculates
tab-stop distance and the line-number gutter width from `document().defaultFont()` and the
current `indent_size`. Indent width alone is still updated via
`TabsPresenter.apply_settings` → `update_indent_size`.

## Related

- PYPOST-404 — startup font size bug (call-order fix)
- PYPOST-106 — removed manual per-widget `setFont` loop in `MainWindow`
- PYPOST-107 — body editor font metrics refresh on global theme change
- PYPOST-112 — font inheritance investigation; confirms PYPOST-106/107 close PYPOST-12 debt
- PYPOST-425 — removed redundant `EnvPresenter.apply_font` widget loop
- PYPOST-114 — `QToolTip` QSS hook for variable hover and widget tooltips
- `doc/dev/ui_mixins.md` — variable hover tooltip styling
- `doc/dev/tech-debt/PYPOST-11.md` — menu padding QSS for large fonts

## Tooltip styling

Variable hover tooltips (`QToolTip.showText` in `VariableHoverMixin`) and widget
`setToolTip` strings share the global `QToolTip` rule in `pypost/ui/styles/main.qss`.
Edit that block to change tooltip colors; use palette roles for theme compatibility.
