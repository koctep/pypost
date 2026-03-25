# PYPOST-404 — Observability

**Date**: 2026-03-25
**Author**: senior_engineer
**Jira**: PYPOST-404

---

## 1. Summary

This document records the observability review for the PYPOST-404 font-size-on-startup bug fix.
Two targeted `logger.debug` calls were added to `pypost/ui/main_window.py`. No metrics or
monitoring additions were required; the fix is a call-order correction with no async, network,
or performance-sensitive paths.

---

## 2. Pre-existing Logging (relevant to this bug)

| Location | Log message | Level | Notes |
|----------|-------------|-------|-------|
| `MainWindow.__init__` (line 73) | `main_window_initialized` | INFO | Confirms startup completed |
| `MainWindow.open_settings` (line 188) | `settings_applied font_size=%d indent_size=%d` | INFO | Logged after user changes settings via dialog |
| `main.py` `main()` | `PyPost starting up` / `PyPost shutting down` | INFO | Process lifecycle bookends |

**Gap identified**: `apply_settings` itself had no logging. The startup call path
(`__init__` → `apply_settings`) was entirely silent, making it impossible to confirm from
logs whether the correct font size was loaded and applied on startup — the exact scenario that
PYPOST-404 describes.

A second gap: the FR-4 `config_manager` injection path had no log, so there was no way to
confirm at runtime whether `MainWindow` used the injected instance or created a redundant one.

---

## 3. Changes Made

### 3.1 `apply_settings` entry and post-apply confirmation

**File**: `pypost/ui/main_window.py`
**Level**: `DEBUG`

```python
logger.debug("apply_settings_start font_size=%d", settings.font_size)
# … style_manager.apply_styles(app) — Qt re-polish happens here …
# … app.setFont(font) …
logger.debug("apply_settings_font_applied point_size=%d", app.font().pointSize())
```

**Why two lines instead of one**: The first records the *requested* size before the Qt
re-polish; the second records what `app.font().pointSize()` reports *after* `setFont`. If a
future Qt upgrade or stylesheet change re-introduces the override bug, the two values will
diverge in the log, making the regression immediately obvious without needing a debugger.

### 3.2 `config_manager` source logging

**File**: `pypost/ui/main_window.py` — `__init__`, around `self.config_manager` assignment
**Level**: `DEBUG`

```python
logger.debug("config_manager_source source=injected")   # when caller passes instance
logger.debug("config_manager_source source=new")        # when MainWindow creates its own
```

**Why**: FR-4 guarantees a single `ConfigManager` / `load_config()` call when `main.py`
passes its instance. This log confirms the injection is active in production without
requiring code inspection.

---

## 4. What Was Not Added (and Why)

| Candidate | Decision | Reason |
|-----------|----------|--------|
| Metrics counter for `apply_settings` calls | Not added | Font application is a synchronous UI operation, not a business metric. The existing `MetricsManager` targets HTTP/network observability. |
| WARNING on font mismatch (requested ≠ applied) | Not added | Would require a conditional comparison that adds complexity beyond the fix scope. The two DEBUG lines achieve the same diagnostic goal passively. |
| INFO-level log inside `apply_settings` | Used DEBUG | `apply_settings` is called on every settings dialog save and on startup; INFO would add noise to the default log output. The startup `main_window_initialized` INFO line already brackets the call. |

---

## 5. How to Use These Logs

Enable DEBUG logging to see the font lifecycle on startup:

```
logging.basicConfig(level=logging.DEBUG, ...)
```

Or filter to this module:

```
logging.getLogger("pypost.ui.main_window").setLevel(logging.DEBUG)
```

Expected startup output (normal case):

```
… pypost.ui.main_window DEBUG config_manager_source source=injected
… pypost.ui.main_window DEBUG apply_settings_start font_size=12
… pypost.ui.main_window DEBUG apply_settings_font_applied point_size=12
… pypost.ui.main_window INFO  main_window_initialized
```

Regression signature (if the Qt re-polish bug returns):

```
… pypost.ui.main_window DEBUG apply_settings_start font_size=12
… pypost.ui.main_window DEBUG apply_settings_font_applied point_size=9   ← mismatch
```

---

## 6. Files Modified

| File | Change |
|------|--------|
| `pypost/ui/main_window.py` | Added 2 `logger.debug` calls — one in `apply_settings`, one in `__init__` for `config_manager` source |
