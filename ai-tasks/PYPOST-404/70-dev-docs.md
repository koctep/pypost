# PYPOST-404 — Developer Documentation
# Bug: Font size settings not applied on application startup

**Date**: 2026-03-25
**Author**: team_lead
**Jira**: PYPOST-404

---

## 1. Overview

PYPOST-404 fixes a startup bug where the user-configured font size was silently overridden by Qt's
stylesheet re-polish mechanism. After the fix, the correct font size is applied and visible
application-wide on every launch.

---

## 2. Root Cause

`MainWindow.apply_settings` called `app.setFont(font)` **before**
`style_manager.apply_styles(app)`. In PySide6 / Qt 6, `QApplication.setStyleSheet()` (called
inside `apply_styles`) triggers a full widget re-polish that resets the application-level font to
the platform default. Any `app.setFont()` call made prior to `setStyleSheet()` is lost.

The fix is to call `style_manager.apply_styles(app)` first, then set the font.

---

## 3. Changes

### 3.1 `pypost/ui/main_window.py`

#### `apply_settings` — call order fix (FR-1, FR-2, FR-3)

**Before:**

```python
def apply_settings(self, settings) -> None:
    self.settings = settings
    app = QApplication.instance()
    if app:
        font = app.font()
        font.setPointSize(settings.font_size)
        app.setFont(font)                      # overridden by next line
        self.style_manager.apply_styles(app)   # resets app font via setStyleSheet
        for w in [...]:
            w.setFont(font)
```

**After:**

```python
def apply_settings(self, settings) -> None:
    self.settings = settings
    logger.debug("apply_settings_start font_size=%d", settings.font_size)
    app = QApplication.instance()
    if app:
        self.style_manager.apply_styles(app)   # stylesheet first
        font = app.font()                       # read font after re-polish
        font.setPointSize(settings.font_size)
        app.setFont(font)                       # survives; no further setStyleSheet call
        logger.debug("apply_settings_font_applied point_size=%d", app.font().pointSize())
        for w in [...]:
            w.setFont(font)
```

**Key point**: `app.font()` is now read *after* `apply_styles`, so any font properties set by the
stylesheet are captured before `pointSize` is overridden. This preserves stylesheet-defined font
family and weight while enforcing the user's size preference.

#### `__init__` — optional `config_manager` injection (FR-4)

`MainWindow.__init__` now accepts an optional `config_manager` parameter:

```python
def __init__(
    self,
    metrics: MetricsManager,
    template_service: TemplateService,
    config_manager: ConfigManager | None = None,
) -> None:
    ...
    if config_manager is not None:
        logger.debug("config_manager_source source=injected")
        self.config_manager = config_manager
    else:
        logger.debug("config_manager_source source=new")
        self.config_manager = ConfigManager()
```

When a `ConfigManager` instance is injected, `MainWindow` uses it directly. The `else` branch
preserves backward compatibility for any future callers that do not pass one (e.g. standalone tests
or tooling).

### 3.2 `pypost/main.py`

`main()` now passes its `config_manager` to `MainWindow`:

```python
window = MainWindow(
    metrics=metrics_manager,
    template_service=template_service,
    config_manager=config_manager,
)
```

This ensures `settings.json` is read exactly once on startup, by the `ConfigManager` created in
`main()`. `MainWindow` and `StateManager` both operate on the same loaded settings object.

### 3.3 `tests/test_apply_settings_font.py` (new)

Three regression tests confirm the fixed call order:

| Test | What it verifies |
|------|-----------------|
| `test_font_size_applied_after_stylesheet` | `apply_settings(font_size=16)` → `app.font().pointSize() == 16` even when `apply_styles` calls `setStyleSheet("")` |
| `test_font_size_min` | Same as above with `font_size=8` (boundary value) |
| `test_font_size_second_call_wins` | Calling `apply_settings` twice: the second font size is the one applied |

The tests use `patch.object(window.style_manager, "apply_styles", side_effect=lambda app: app.setStyleSheet(""))` to reproduce the Qt re-polish reset in isolation without requiring real `.qss` files on disk.

---

## 4. Observability

Two `logger.debug` calls were added (see `50-observability.md` for full context):

| Log message | Location | Purpose |
|-------------|----------|---------|
| `apply_settings_start font_size=%d` | `apply_settings` entry | Records the requested font size |
| `apply_settings_font_applied point_size=%d` | After `app.setFont(font)` | Confirms the size Qt applied |
| `config_manager_source source=injected\|new` | `__init__` | Confirms FR-4 injection is active |

To enable on startup:

```python
logging.getLogger("pypost.ui.main_window").setLevel(logging.DEBUG)
```

If a regression reintroduces the override bug, `apply_settings_start` and
`apply_settings_font_applied` will show mismatched values in the log.

---

## 5. Qt Behaviour Reference

> **Qt 6 / PySide6**: `QApplication.setStyleSheet(stylesheet)` triggers `QEvent::StyleChange`
> on all widgets and calls `QApplication::polish()` on each, which resets the application font
> to the platform default. Any `QApplication::setFont()` call made before `setStyleSheet()` is
> silently discarded.
>
> **Correct pattern**: always call `setStyleSheet()` before `setFont()` if both are needed.

This is a documented Qt quirk, not a PySide6 bug. The behaviour is consistent across Qt 6.x
versions.

---

## 6. Testing

Run the full test suite to verify no regressions:

```bash
pytest
```

Expected: **191+ passed, 0 failed**.

Run only the new font tests:

```bash
pytest tests/test_apply_settings_font.py -v
```

---

## 7. Related Files

| File | Role |
|------|------|
| `pypost/ui/main_window.py` | Primary fix — `apply_settings` reorder + `__init__` injection |
| `pypost/main.py` | Passes `config_manager` to `MainWindow` |
| `pypost/core/config_manager.py` | Reads/writes `~/.config/pypost/settings.json` |
| `pypost/core/style_manager.py` | Calls `app.setStyleSheet()` via `apply_styles` |
| `pypost/models/settings.py` | `AppSettings` data model; `font_size: int = 12` |
| `tests/test_apply_settings_font.py` | Regression tests for the font-size call order |
