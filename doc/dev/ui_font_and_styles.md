# UI Font Size, Themes, and Global Styles (PYPOST-106, PYPOST-112, PYPOST-792, PYPOST-793)

## Overview

PyPost applies appearance through a single entry point:
**`StyleManager.apply_appearance`**. It runs three steps in a fixed order:

1. **Qt style and palette** — `apply_theme` installs either the platform-native `PyPostStyle`
   (`theme=system`) or Fusion with a light/dark palette.
2. **Global QSS** — `apply_styles` loads every `pypost/ui/styles/*.qss` file, optionally
   appends a global font-size rule, and calls `setStyleSheet` on the application.
3. **Application default font** — reads `app.font()`, sets point size, and calls `setFont`.

Production code must call `apply_appearance`; do not reimplement this sequence elsewhere.
Low-level `apply_theme` and `apply_styles` remain for unit tests and internal use.

Application font size is a user setting (`AppSettings.font_size`, default 12). It must apply
across the main window after startup and whenever Settings are saved.

Tab bars (sidebar, request tabs, editor sub-tabs) rely on native `QTabBar` layout. Shipped QSS
and `PyPostStyle` metrics must not override tab geometry; see [Tab bar styling policy](#tab-bar-styling-policy-pypost-792).

## Architecture

`StyleManager` lives in `pypost/ui/styles/style_manager.py` (moved from `core/` in
[PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)). It colocates theme/QSS
orchestration with `custom_style.py` and bundled `.qss` assets.

### Appearance pipeline

Startup, first show, and every settings save follow the same path:

```text
main() → MainWindow.__init__ / showEvent / open_settings
  → MainWindow.apply_settings(settings)
    → StyleManager.apply_appearance(app, theme=..., font_size=...)
      → apply_theme(app, theme)
      → apply_styles(app, font_size=...)
      → app.setFont(...)
    → tabs.apply_settings / env.apply_settings
```

`StyleManager.apply_appearance` owns the full sequence (PYPOST-793). `MainWindow.apply_settings`
delegates appearance to it and then applies presenter-specific settings only.

Inside `apply_appearance`:

1. **`apply_theme(app, theme)`** — sets the active `QStyle` and palette:
   - `system` → `PyPostStyle()` (wraps the platform style; native tab chrome on macOS).
   - `light` / `dark` → Fusion with a standard or dark custom palette.
2. **`apply_styles(app, font_size=...)`** — loads sorted `*.qss` files from
   `pypost/ui/styles/`, replaces the `%ICONS_DIR%` placeholder with the resolved icons path,
   appends `QWidget { font-size: Npt; }` when `font_size` is set, and replaces the application
   stylesheet (no accumulation on reload).
3. **Application default font** — reads `app.font()`, sets point size, and calls
   `app.setFont(font)`.

`pypost/main.py` does not configure appearance; the first `apply_appearance` runs from
`MainWindow.__init__` via `apply_settings`.

`StyleManager` logs structured events at DEBUG (`apply_appearance_start`,
`apply_appearance_font_applied`, `styles_loaded`, `theme_applied`) and WARNING
(`styles_directory_missing`, `style_file_read_failed`, `styles_directory_scan_failed`). See
`ai-tasks/PYPOST-792/50-observability.md` and `ai-tasks/PYPOST-793/50-observability.md`
for field names.

### Font size propagation

Two mechanisms work together for font size:

1. **Global QSS** — the font-size rule appended by `apply_styles` before
   `QApplication.setStyleSheet()`.
2. **Application default font** — `setFont` after the stylesheet is applied.

Call order matters: **stylesheet first, then `setFont`** (see PYPOST-404). Qt's
`setStyleSheet()` re-polish resets the application font if `setFont` ran earlier. This order
is enforced inside `apply_appearance`; callers must not invoke `apply_styles` and `setFont`
independently in production code.

### `PyPostStyle` and close-indicator metrics

`PyPostStyle` (`pypost/ui/styles/custom_style.py`) is a `QProxyStyle` used for the `system`
theme. It forwards almost all painting and metrics to the platform base style so tabs render
with native chrome (segmented control on macOS).

**Close-indicator policy (PYPOST-792):**

- `close_button_size` defaults to `None`.
- `pixelMetric` returns the base style's `PM_TabCloseIndicatorWidth` /
  `PM_TabCloseIndicatorHeight` unless `set_close_button_size(size)` was called explicitly
  (opt-in override; no production caller sets it today).
- Do **not** reintroduce a global 48px close-indicator override: `QTabBar` sizes per-tab close
  buttons from these metrics; an oversized value draws the close control over tab titles while
  native tab padding is intact.

Bundled `close.svg` / `close-hover.svg` icons in `main.qss` scale into the metric rectangle;
only the close-button sub-control is styled, not `::tab`.

Default close icon (`close.svg`) uses `#999999` stroke (PYPOST-796) for better contrast on dark
native tab chrome. Hover icon (`close-hover.svg`) uses a light pill background with `#333333`
stroke — unchanged.

### Tab bar styling policy (PYPOST-792)

**Do not add `QTabBar::tab` rules to shipped QSS.**

Qt's stylesheet model treats sub-control customization as all-or-nothing: setting **any**
box-model property on `QTabBar::tab` (padding, margin, width, border, background, etc.)
disables native tab rendering for that sub-control. Unset properties fall back to bare defaults,
so a rule like `padding: 0` collapses each tab to its text width. Adjacent labels then abut
("CollectionsHistory", "ParamsHeadersBodyScriptMCP") and close buttons misalign.

Allowed in `main.qss`:

- `QTabBar::close-button` and `:hover` — icon images only; geometry comes from
  `PM_TabCloseIndicator*` via the active style.

Regression coverage: `tests/test_tab_layout_regression.py` (QSS guard + tab geometry +
close-indicator metrics).

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

### `StyleManager.apply_appearance(app, *, theme, font_size)`

**Authoritative production entry point.** Applies theme, global QSS (with font-size rule), and
application default font in the correct order. Called from `MainWindow.apply_settings` on
startup, first show, and settings save.

- **theme**: `system`, `light`, or `dark` (invalid values fall back to `system` inside
  `apply_theme`).
- **font_size**: point size from `AppSettings.font_size`.

### `StyleManager.apply_theme(app, theme="system")`

Installs the Qt style and palette for the requested theme. Used internally by
`apply_appearance` and by unit tests (`tests/test_style_manager_theme.py`).

### `StyleManager.apply_styles(app_or_widget, font_size=None)`

Loads `pypost/ui/styles/*.qss`, optionally appends the global font-size rule, and applies the
combined sheet to the given `QApplication` or widget. Used internally by `apply_appearance`
and by unit tests (`tests/test_style_manager_font.py`, tab layout regression fixtures).

### `StyleManager.load_styles() -> str`

Returns the concatenated QSS from all `*.qss` files (sorted alphabetically) with
`%ICONS_DIR%` resolved. Used by tests and by `apply_styles`.

### `PyPostStyle.set_close_button_size(size: int)`

Opt-in override for tab close-button width and height metrics. Prefer leaving
`close_button_size` at `None` so native platform metrics apply.

### `MainWindow.apply_settings(settings: AppSettings)`

Delegates appearance to `style_manager.apply_appearance`, then calls `tabs.apply_settings` and
`env.apply_settings`. Does **not** call `setFont` on individual child widgets.

## Configuration

- Settings UI: Settings dialog → Application Font Size (8–48) and Theme (`system` / `light` /
  `dark`).
- Persisted in user config via `ConfigManager` / `StateManager`.

## Troubleshooting

### Font size

| Symptom | Likely cause |
| --- | --- |
| Font size wrong on startup | Appearance bypasses `apply_appearance` or reimplements pipeline with wrong order |
| One widget ignores size | Widget has local `setStyleSheet` with fixed `font-size` |
| Font resets after show | `showEvent` re-applies settings via `QTimer.singleShot(0, ...)` — intentional |

### Tab layout (PYPOST-792)

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Sidebar or editor tab labels run together ("CollectionsHistory") | Active `QTabBar::tab` rule in QSS (any box-model property) | Remove the rule; keep only `QTabBar::close-button` icon rules |
| Request tab close button overlaps title | `PyPostStyle.set_close_button_size` called globally, or default forced to a large pixel value | Leave `close_button_size` as `None`; use native `PM_TabCloseIndicator*` metrics |
| Tabs look correct on Fusion but broken on macOS with `system` theme | Native tab chrome disabled by QSS while platform style is active | Same as first row — native renderer requires an unstylized `::tab` sub-control |
| `+` new-tab control cramped | Consequence of zero-padding `::tab` rule stripping chrome around the pseudo-tab | Restore native tab rendering (remove `::tab` styling) |
| Close icon hard to see in dark mode | Outdated `close.svg` stroke (`#666666`) vs native dark tab chrome | Fixed in PYPOST-796 (`#999999` default stroke); verify with macOS dark appearance; hover icon unchanged |

**Verify locally:**

```bash
make test PYTEST_ARGS=tests/test_tab_layout_regression.py
```

All seven tests must pass. The QSS guard (`test_loaded_styles_do_not_customize_tab_geometry`)
runs without a display; geometry tests need the production stylesheet applied to a
`QApplication`.

**Qt references:** [Style Sheets overview](https://doc.qt.io/qt-6/stylesheet.html) (sub-control
customization disables native rendering); see also `ai-tasks/PYPOST-792/20-architecture.md`.

## Body editor (`CodeEditor`)

Request body tabs use `CodeEditor`, which inherits application font size from global QSS and
`QApplication.setFont`. The editor does **not** receive manual `setFont` from
`TabsPresenter`.

When font metrics change (`QEvent.FontChange`), `CodeEditor._refresh_font_metrics` recalculates
tab-stop distance and the line-number gutter width from `document().defaultFont()` and the
current `indent_size`. Indent width alone is still updated via
`TabsPresenter.apply_settings` → `update_indent_size`.

## Related

- PYPOST-793 — `StyleManager.apply_appearance` as single appearance entry point
- PYPOST-792 — macOS tab layout: no `QTabBar::tab` QSS; native close-indicator metrics
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
