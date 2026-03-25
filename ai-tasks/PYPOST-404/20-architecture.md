# PYPOST-404 — Architecture
# Bug: Font size settings not applied on application startup

**Date**: 2026-03-25
**Author**: senior_engineer
**Jira**: PYPOST-404

---

## 1. Summary

The bug is a two-line ordering error in `MainWindow.apply_settings`. The fix is surgical:
move `app.setFont(font)` to execute **after** `style_manager.apply_styles(app)`. A secondary
clean-up (FR-4) eliminates the duplicate `ConfigManager` instantiation by injecting the one
created in `main.py` into `MainWindow`.

No new classes, files, or dependencies are required beyond a new test module.

---

## 2. Root Cause (confirmed in code)

`MainWindow.apply_settings` (`main_window.py:145`):

```
line 151  app.setFont(font)              ← sets user font
line 152  self.style_manager.apply_styles(app)  ← setStyleSheet() resets app font
lines 153-160  explicit widget loop      ← partial repair only
```

`StyleManager.apply_styles` calls `app.setStyleSheet(stylesheet)`. In Qt 6 / PySide6, any
call to `QApplication.setStyleSheet()` triggers a full widget re-polish and resets the
application-level font to the platform default. This silently undoes the `app.setFont(font)`
executed one line earlier.

The explicit widget loop (lines 153-160) patches only the widgets it enumerates; all others
(`HistoryPanel`, sidebar `QTabWidget`, `QSplitter` children, future dialogs) inherit the
system-default font.

---

## 3. Affected Files

| File | Change type |
|------|-------------|
| `pypost/ui/main_window.py` | **Primary fix** — reorder calls in `apply_settings`; optional constructor signature change for FR-4 |
| `pypost/main.py` | **Optional FR-4** — pass `config_manager` to `MainWindow` |
| `tests/test_apply_settings_font.py` | **New** — unit test for NFR-3 |

---

## 4. Design

### 4.1 Primary Fix — `apply_settings` reordering (FR-1, FR-2, FR-3)

**Current order** (`main_window.py:145-161`):

```python
def apply_settings(self, settings) -> None:
    self.settings = settings
    app = QApplication.instance()
    if app:
        font = app.font()
        font.setPointSize(settings.font_size)
        app.setFont(font)                      # ← BUG: overridden by next line
        self.style_manager.apply_styles(app)   # ← resets app font
        for w in [...]:
            w.setFont(font)
        if self.menuBar():
            self.menuBar().setFont(font)
    self.tabs.apply_settings(settings)
```

**Fixed order**:

```python
def apply_settings(self, settings) -> None:
    self.settings = settings
    app = QApplication.instance()
    if app:
        self.style_manager.apply_styles(app)   # ← stylesheet first
        font = app.font()
        font.setPointSize(settings.font_size)
        app.setFont(font)                      # ← font set after, survives re-polish
        for w in [...]:
            w.setFont(font)
        if self.menuBar():
            self.menuBar().setFont(font)
    self.tabs.apply_settings(settings)
```

Key change: `app.font()` is now called **after** `apply_styles`, so any font properties that
the stylesheet might set are captured before we override `pointSize`. The `font.setPointSize`
call then overwrites only the size, preserving any stylesheet-specified family or weight.

### 4.2 Optional Clean-up — ConfigManager injection (FR-4)

**Problem**: `main.py` creates a `ConfigManager` and loads settings, but passes neither to
`MainWindow`. `MainWindow.__init__` creates a second `ConfigManager` and calls `load_config()`
again (via `StateManager`).

**Solution**: Extend `MainWindow.__init__` to accept an optional `config_manager` parameter.
When provided, use it instead of constructing a new one. `main.py` passes its instance.

`MainWindow.__init__` signature change:

```python
def __init__(
    self,
    metrics: MetricsManager,
    template_service: TemplateService,
    config_manager: ConfigManager | None = None,
) -> None:
    ...
    self.config_manager = config_manager or ConfigManager()
```

`main.py` call-site change:

```python
window = MainWindow(
    metrics=metrics_manager,
    template_service=template_service,
    config_manager=config_manager,
)
```

This eliminates the second `load_config()` call and ensures a single authoritative
`AppSettings` instance flows from startup through to `MainWindow`.

---

## 5. Test Design (NFR-3)

**File**: `tests/test_apply_settings_font.py`

**Approach**: Use `pytest` with `unittest.mock`. Create a minimal `QApplication` (or reuse one
if already initialised), instantiate a real `StyleManager` (or mock `apply_styles` to avoid
needing `.qss` files on disk), call `apply_settings` with a custom `font_size`, and assert
`QApplication.instance().font().pointSize() == font_size`.

**Test cases**:

| ID | Description |
|----|-------------|
| T-1 | `apply_settings` with `font_size=16` results in `app.font().pointSize() == 16` after the call |
| T-2 | `apply_settings` with `font_size=8` (min) results in `app.font().pointSize() == 8` |
| T-3 | Calling `apply_settings` twice with different sizes: second size wins |

**Isolation strategy**:

- Mock `StyleManager.apply_styles` to call a real `app.setStyleSheet("")` (mimics the Qt
  re-polish reset without needing real `.qss` files), confirming the fix survives the reset.
- Mock `TabsPresenter.apply_settings` to avoid requiring a full UI hierarchy.
- Use `QApplication.instance() or QApplication([])` to avoid duplicate `QApplication` errors
  across the test suite.

**Skeleton**:

```python
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from pypost.models.settings import AppSettings


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_window(qapp):
    """Build a MainWindow with all heavy dependencies mocked."""
    metrics = MagicMock()
    template_service = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.ConfigManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.main_window.MCPServerManager"),
        patch("pypost.ui.main_window.HistoryManager"),
        patch("pypost.ui.main_window.CollectionsPresenter"),
        patch("pypost.ui.main_window.TabsPresenter"),
        patch("pypost.ui.main_window.EnvPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
    ):
        mock_sm.return_value.settings = AppSettings()
        from pypost.ui.main_window import MainWindow
        window = MainWindow(metrics=metrics, template_service=template_service)
    return window


class TestApplySettingsFont:

    def test_font_size_applied_after_stylesheet(self, qapp):
        window = _make_window(qapp)
        settings = AppSettings(font_size=16)
        # apply_styles will call setStyleSheet("") which resets app font — this is the
        # real-world condition the fix must survive.
        with patch.object(
            window.style_manager, "apply_styles",
            side_effect=lambda app: app.setStyleSheet(""),
        ):
            window.apply_settings(settings)
        assert qapp.font().pointSize() == 16

    def test_font_size_min(self, qapp):
        window = _make_window(qapp)
        settings = AppSettings(font_size=8)
        with patch.object(
            window.style_manager, "apply_styles",
            side_effect=lambda app: app.setStyleSheet(""),
        ):
            window.apply_settings(settings)
        assert qapp.font().pointSize() == 8

    def test_font_size_second_call_wins(self, qapp):
        window = _make_window(qapp)
        with patch.object(
            window.style_manager, "apply_styles",
            side_effect=lambda app: app.setStyleSheet(""),
        ):
            window.apply_settings(AppSettings(font_size=14))
            window.apply_settings(AppSettings(font_size=20))
        assert qapp.font().pointSize() == 20
```

---

## 6. Sequence Diagram — Fixed Startup Flow

```
main()
  │
  ├─ QApplication()
  ├─ ConfigManager()  ────────────────────────────────── single instance
  ├─ settings = config_manager.load_config()
  ├─ MetricsManager.start_server(...)
  ├─ TemplateService()
  ├─ app.setStyle(PyPostStyle())
  └─ MainWindow(metrics, template_service, config_manager)  ← FR-4: injected
         │
         ├─ self.config_manager = config_manager  ← no second load_config()
         ├─ StateManager(self.config_manager)      ← uses same instance
         ├─ ... (build layout, wire signals)
         └─ apply_settings(self.settings)
                │
                ├─ style_manager.apply_styles(app)  ← setStyleSheet() → re-polish
                ├─ font = app.font()                 ← read after re-polish
                ├─ font.setPointSize(settings.font_size)
                ├─ app.setFont(font)                 ← survives, no further setStyleSheet
                └─ explicit widget loop (belt-and-suspenders for known widgets)
```

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `app.font()` called after `apply_styles` picks up a stylesheet-defined font family different from before | Low — current `.qss` files do not set a global font family | Acceptable; existing explicit widget loop still sets `font` on key widgets |
| FR-4 signature change breaks other call sites | Low — `MainWindow` is only instantiated in `main.py` | Grep confirms single instantiation site; parameter is optional (defaults to `None`) |
| Test isolation: multiple `QApplication` instances across test suite | Medium | Module-scoped `qapp` fixture; `QApplication.instance() or QApplication([])` guard |

---

## 8. Implementation Checklist (for junior_engineer)

- [ ] `pypost/ui/main_window.py` — move `style_manager.apply_styles(app)` before `font = app.font()`
- [ ] `pypost/ui/main_window.py` — add optional `config_manager` param (FR-4)
- [ ] `pypost/main.py` — pass `config_manager` to `MainWindow` (FR-4)
- [ ] `tests/test_apply_settings_font.py` — implement T-1, T-2, T-3 as above
- [ ] Run full test suite; confirm no regressions
