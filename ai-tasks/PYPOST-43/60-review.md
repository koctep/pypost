# PYPOST-43: Tech Debt Review

## Summary

The decomposition of `MainWindow` into three focused presenters is functionally complete and
a significant improvement over the previous god-object. The architecture is sound and the
presenter pattern is well-applied. The items below are genuine tech-debt findings — none are
blockers for shipping, but they should be addressed in follow-up tickets to prevent the new
presenter layer from accumulating its own cruft.

---

## Findings

### TD-1 — `main_window.py` exceeds the ≤ 150 LOC target (LOW)

**File:** `pypost/ui/main_window.py`
**Actual:** 183 LOC (175 non-blank)
**Target:** ≤ 150 LOC (requirement + architecture spec)

The overage comes from `open_settings` (22 lines) and `apply_settings` (17 lines) which each
contain more logic than a pure composition root should hold. `open_settings` performs
metrics-change detection inline rather than delegating it to a service; `apply_settings`
iterates a hard-coded list of per-presenter widgets to set fonts.

**Recommendation:** Extract metrics-restart logic into `MetricsManager.restart_if_changed(old,
new)` and introduce a thin `apply_font(font)` method on each presenter so `MainWindow`
calls `self.{collections,tabs,env}.apply_font(font)` instead of reaching into their internal
widgets.

---

### TD-2 — `MainWindow.open_settings` calls a private method on `EnvPresenter` (HIGH)

**File:** `pypost/ui/main_window.py:166`
**Code:** `self.env._on_env_changed(self.env.env_selector.currentIndex())`

This is a direct call to a private method from outside the class. The code-cleanup report
acknowledges it as a known gap. If `EnvPresenter` is ever refactored, this call will silently
become stale or break.

**Recommendation:** Add a public method `EnvPresenter.reload_current_env()` that delegates to
`_on_env_changed` internally, and update the call-site in `MainWindow`.

---

### TD-3 — `EnvPresenter` leaks internal widget references via properties (MEDIUM)

**File:** `pypost/ui/presenters/env_presenter.py:81-95`
**Properties:** `env_selector`, `manage_btn`, `mcp_status_label`, `env_label`

These four properties exist solely so `MainWindow.apply_settings` can call `setFont` on each
one. Exposing internal `QLabel` / `QComboBox` / `QPushButton` instances breaks the encapsulation
that the presenter pattern is meant to provide.

**Recommendation:** Add `EnvPresenter.apply_font(font: QFont)` and have it set the font on all
internal widgets itself. Remove the four widget-exposure properties.

---

### TD-4 — `Environment` import is unused in `tabs_presenter.py` (LOW)

**File:** `pypost/ui/presenters/tabs_presenter.py:17`
**Code:** `from pypost.models.models import RequestData, Environment`

`Environment` is never referenced in that module. It is an import artefact from the original
`main_window.py` extraction.

**Recommendation:** Remove `Environment` from the import.

---

### TD-5 — `RequestTab.layout` shadows the inherited `QWidget.layout()` method (MEDIUM)

**File:** `pypost/ui/presenters/tabs_presenter.py:29`
**Code:** `self.layout = QVBoxLayout(self)`

`QWidget` exposes a `layout()` method. Assigning `self.layout = ...` on an instance replaces
it with a data attribute, making `tab.layout()` (called by Qt internally for widget queries)
unreachable. The code works by accident today because the layout is passed to the constructor
`QVBoxLayout(self)`, which registers it with Qt's C++ ownership. However, name-shadowing
`layout` is dangerous and will confuse any reader expecting the Qt API.

**Recommendation:** Rename to `self._layout` or `self.main_layout`.

---

### TD-6 — `_handle_send_request` locates the sending tab via `self.sender()` (MEDIUM)

**File:** `pypost/ui/presenters/tabs_presenter.py:270-277`
**Pattern:**
```python
for i in range(self._tabs.count()):
    tab = self._tabs.widget(i)
    if isinstance(tab, RequestTab) and tab.request_editor == self.sender():
```

`QObject.sender()` is fragile: it returns `None` if called outside a signal-slot invocation
context, and it couples the presenter to Qt's internal signal dispatch. The same
`send_requested` signal is already connected per-tab in `_wire_tab_signals`, so the sender
is always known at connection time.

**Recommendation:** Use a closure to capture the tab reference at wire-time:
```python
tab.request_editor.send_requested.connect(
    lambda data, t=tab: self._handle_send_request(t, data)
)
```
Then change the signature to `_handle_send_request(self, sender_tab, request_data)`.

---

### TD-7 — `MetricsManager` singleton called inside presenters rather than injected (LOW)

**File:** `pypost/ui/presenters/tabs_presenter.py:204, 293, 320, 402, 435`
**Code:** `MetricsManager().track_*(...)`

`TabsPresenter` creates new `MetricsManager()` instances inline. While `MetricsManager` is
a singleton, this pattern hides the dependency, makes the presenter harder to test without
patching the singleton, and was explicitly flagged as R2 out of scope in the requirements.

**Recommendation:** Inject `MetricsManager` via the constructor (same as
`CollectionsPresenter` already does), eliminating the inline instantiation calls.

---

### TD-8 — `_handle_save_request` uses `currentIndex()` after a modal dialog (LOW)

**File:** `pypost/ui/presenters/tabs_presenter.py:443`
**Code:** `current_index = self._tabs.currentIndex()`

The current tab index is read *after* the save dialog closes. If the user switches tabs via
a shortcut while the dialog is open (possible on some platforms), the wrong tab gets its label
updated.

**Recommendation:** Capture `current_index = self._tabs.currentIndex()` before
`dialog.exec()` and use the captured value throughout the method.

---

## Severity Summary

| ID | Severity | Description |
|---|---|---|
| TD-2 | HIGH | Private method called from outside class |
| TD-3 | MEDIUM | Presenter leaks internal widget references |
| TD-5 | MEDIUM | `self.layout` shadows Qt `layout()` method |
| TD-6 | MEDIUM | `sender()` used to locate signal origin tab |
| TD-1 | LOW | `main_window.py` 183 LOC vs 150 target |
| TD-4 | LOW | Unused `Environment` import |
| TD-7 | LOW | `MetricsManager` not injected in `TabsPresenter` |
| TD-8 | LOW | Tab index captured after modal dialog |

---

## Not Tech Debt (Intentional Decisions)

- `request_renamed` and `request_saved` signals were added beyond the architecture spec to
  avoid presenter-to-presenter references — this is the correct design choice.
- `TabsPresenter` retaining `StateManager` access for expand-state persistence in
  `_handle_save_request` is intentional (it is the only place where a new collection must be
  auto-expanded after save).
- `_on_script_output` was a no-op stub in the junior implementation; it is now properly
  implemented as part of the observability step.
