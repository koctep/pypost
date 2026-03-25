# PYPOST-404 — Requirements
# Bug: Font size settings not applied on application startup

**Date**: 2026-03-25
**Analyst**: analyst
**Jira**: PYPOST-404
**Priority**: High
**Type**: Bug

---

## 1. Problem Statement

After a user changes the font size in the Settings dialog and restarts the application, the
selected font size is not applied to the UI. The application starts with the system default
font size regardless of what was saved to disk.

**Steps to reproduce:**
1. Open Settings (Ctrl+, or F12).
2. Change the font size to any non-default value (e.g. 16).
3. Confirm and close the dialog.
4. Quit and relaunch the application.
5. Observe: font size is reset to the system default (not 16).

**Expected:** The application launches with the font size that was saved in settings.
**Actual:** The application launches with the system default font size.

---

## 2. Affected Components

| File | Class / Function | Role |
|------|-----------------|------|
| `pypost/models/settings.py` | `AppSettings` | Data model; `font_size: int = 12` |
| `pypost/core/config_manager.py` | `ConfigManager.load_config` / `save_config` | Reads/writes `~/.config/pypost/settings.json` |
| `pypost/core/state_manager.py` | `StateManager.__init__` | Loads settings on construction |
| `pypost/ui/main_window.py` | `MainWindow.__init__` / `apply_settings` | Loads settings and applies font at startup |
| `pypost/core/style_manager.py` | `StyleManager.apply_styles` | Calls `app.setStyleSheet()` |
| `pypost/main.py` | `main` | Application entry point |

---

## 3. Current Behaviour — Root Cause Analysis

### 3.1 Startup flow

1. `main.py` creates `QApplication`, then `ConfigManager`, loads settings (correct
   `font_size` from disk), then creates `MainWindow` — but does NOT pass the loaded settings
   or `ConfigManager` to `MainWindow`.
2. `MainWindow.__init__` creates its **own** `ConfigManager` and `StateManager`, which loads
   settings from disk a second time. `self.settings.font_size` is therefore correct.
3. At the end of `__init__`, `apply_settings(self.settings)` is called.

### 3.2 Bug in `apply_settings`

`MainWindow.apply_settings` (`main_window.py`, line 145) executes in this order:

```python
font = app.font()                       # 1. Get current app font
font.setPointSize(settings.font_size)   # 2. Set desired point size
app.setFont(font)                       # 3. Apply font app-wide  ← set here
self.style_manager.apply_styles(app)   # 4. Calls app.setStyleSheet() ← RESETS font
for w in [...]:
    w.setFont(font)                     # 5. Explicit widget loop (after reset, OK for these)
```

**Step 4** calls `StyleManager.apply_styles` → `app.setStyleSheet(stylesheet)`.
In PySide6 / Qt 6, calling `QApplication.setStyleSheet()` triggers a full re-polish of all
widgets and resets the application-level font to the platform default. This cancels the
effect of the `app.setFont(font)` call in step 3.

After step 4, `app.font()` returns the **system default** font size, not `settings.font_size`.

**Step 5** explicitly sets the font on a short list of named widgets, so those specific
widgets display correctly. However:
- Any widget **not** in the explicit list (e.g. `HistoryPanel`, `QTabWidget` sidebar,
  `QSplitter`, menu sub-items, future dialogs) inherits the application font — which was
  reset to the system default by step 4.
- At runtime (during the same session), after the user opens Settings and saves, the visible
  widgets are already polished, so the effect is partially masked. On a fresh startup all
  widgets are freshly created and inherit the reset app font.

### 3.3 Secondary observation — duplicate `ConfigManager`

`main.py` creates a `ConfigManager` and loads settings, but passes neither to `MainWindow`.
`MainWindow` creates a second `ConfigManager` and loads settings again. While functionally
harmless (both read the same file), it creates unnecessary duplication and could cause subtle
ordering issues if startup actions ever modify the config file before `MainWindow` loads it.

---

## 4. Functional Requirements

### FR-1 — Font size must be applied application-wide at startup

When the application starts, the font size stored in `settings.json` must be applied to the
entire application, including all widgets not explicitly enumerated in `apply_settings`.

**Acceptance criteria:**
- Launch the app after saving a non-default font size (e.g. 14 pt).
- All visible text in the main window (collections panel, tab bar, history panel, menu bar,
  environment selector, buttons, splitter contents) renders at the saved font size.
- The application-level font (`QApplication.instance().font().pointSize()`) equals the
  saved `font_size` value after startup completes.

### FR-2 — Font size persists across restarts

Changing font size in the Settings dialog and restarting must produce the same font size on
the next launch.

**Acceptance criteria:**
- Change font size → quit → relaunch → font size is the one saved, not the system default.

### FR-3 — `apply_settings` must set `app.setFont` after `setStyleSheet`

The stylesheet must be applied before the programmatic font is set, so that Qt's stylesheet
re-polish does not override the user-configured font.

**Acceptance criteria (code-level):**
- In `apply_settings`, `app.setFont(font)` is called **after** `style_manager.apply_styles(app)`.

### FR-4 — Settings loaded in `main.py` must be passed to `MainWindow` (optional clean-up)

To avoid loading `settings.json` twice on startup and to centralise the authoritative
settings instance, the `ConfigManager` (or pre-loaded `AppSettings`) created in `main.py`
should be injected into `MainWindow` rather than created again inside `MainWindow.__init__`.

> **Note:** This is a secondary clean-up requirement. It does not directly cause the bug but
> improves consistency. It may be deferred to a separate clean-up task if the team prefers
> minimal-change approach for FR-1 through FR-3.

---

## 5. Non-Functional Requirements

- **NFR-1 Regression safety:** Changing settings at runtime (within the same session, via
  the Settings dialog) must continue to work correctly after the fix.
- **NFR-2 No new dependencies:** The fix must not introduce new libraries or platform APIs.
- **NFR-3 Test coverage:** A unit or integration test must verify that `apply_settings` sets
  `app.font().pointSize()` to `settings.font_size` after the call returns, even when
  `style_manager.apply_styles` is invoked.

---

## 6. Out of Scope

- Changing the supported font size range (currently 8–48 pt via the settings dialog).
- Persisting font family or weight.
- Per-widget font size overrides beyond the global setting.
- Migrating the config file format.

---

## 7. Files to Change

| File | Expected change |
|------|----------------|
| `pypost/ui/main_window.py` | Reorder `apply_settings`: call `app.setFont(font)` after `apply_styles(app)` |
| `pypost/main.py` | (Optional FR-4) Pass `config_manager` / `settings` to `MainWindow` |
| `pypost/ui/main_window.py` | (Optional FR-4) Accept injected `ConfigManager` instead of creating one |
| `tests/` | Add test for `apply_settings` font persistence after stylesheet application |
