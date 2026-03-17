# PYPOST-41 Tech Debt Review

## Summary

The PYPOST-41 implementation is solid overall. It is consistent with the established
constructor-injection pattern, all functional requirements are met, and the new code ships with
good unit-test coverage and observability. The items below are genuine improvement opportunities,
none of which block the current delivery.

---

## TD-1 — Test infrastructure bypasses `HistoryManager` constructor (HIGH)

**File:** `tests/test_history_manager.py`, `_manager_at()` helper (line 143)

**Issue:** Tests use `HistoryManager.__new__(HistoryManager)` and manually populate internal
attributes to avoid the `platformdirs` path lookup. This is fragile: adding any new instance
variable to `__init__` will silently break the helper without a test failure until runtime.

**Recommended fix:** Add an optional `history_path: Path | None = None` parameter to
`HistoryManager.__init__`. When provided it overrides the `platformdirs` resolution. Tests can
then call `HistoryManager(history_path=Path(tmp_dir) / "history.json")` directly, and
`_manager_at` becomes a thin one-liner.

---

## TD-2 — Repeated `import tempfile` inside every test method (LOW)

**File:** `tests/test_history_manager.py` (lines 28, 33, 44, 54, 65, 79, 94, 104, 120)

**Issue:** `import tempfile` appears at the top of nine individual test methods. Module-level
imports are the Python convention and eliminate the repeated overhead (minor but noisy).

**Recommended fix:** Move `import tempfile` to the module-level import block at the top of the
file.

---

## TD-3 — Vestigial `tmp_path=None` parameter on `test_load_missing_file` (LOW)

**File:** `tests/test_history_manager.py`, line 26

**Issue:** `def test_load_missing_file(self, tmp_path=None):` has a leftover `tmp_path` default
argument, a residue from an earlier pytest fixture approach. `unittest.TestCase` methods must
not have extra parameters; this only works because the default is `None`.

**Recommended fix:** Remove the `tmp_path=None` parameter.

---

## TD-4 — Deferred `QTabWidget` import inside method body (LOW)

**File:** `pypost/ui/main_window.py`, `_build_layout()` (line 78)

**Issue:** `from PySide6.QtWidgets import QTabWidget` is imported inside `_build_layout()` while
all other Qt imports are at module level. The inconsistency makes the import graph harder to
read and tools like `pyflakes` / `ruff` may not catch issues in the deferred import.

**Recommended fix:** Move the import to the top-level `from PySide6.QtWidgets import (...)` block
in `main_window.py`.

---

## TD-5 — `_selected_entry()` performs a linear scan (LOW)

**File:** `pypost/ui/widgets/history_panel.py`, `_selected_entry()` (line 178)

**Issue:** On every selection-change event, `_selected_entry()` iterates `self._entries`
(up to 500 items) to find the entry by ID. While 500 items is negligible today, the lookup cost
grows linearly if `DEFAULT_MAX_ENTRIES` is ever raised.

**Recommended fix:** Build an `{id: HistoryEntry}` dict alongside `self._entries` in `refresh()`
and use it for O(1) lookups in `_selected_entry()`.

---

## TD-6 — Duplicate template rendering for HTTP requests (LOW)

**File:** `pypost/core/request_service.py`, `execute()` (lines 126–132)

**Issue:** For HTTP requests, `TemplateService.render_string()` is called twice — once inside
`HTTPClient.send_request()` and again in the history-recording block. This is documented as an
acceptable trade-off in the architecture doc (D2), but it wastes CPU for requests with
large headers or bodies.

**Recommended fix (future):** Return resolved fields from `HTTPClient.send_request()` in an
extended result object, and reuse them in the history block instead of re-rendering. This
requires a `HTTPClient` interface change and is best deferred until a refactoring story.

---

## TD-7 — Fixed heights on detail-pane text fields prevent flexible resizing (LOW)

**File:** `pypost/ui/widgets/history_panel.py`, lines 69, 71

**Issue:** `_detail_headers.setFixedHeight(60)` and `_detail_body.setFixedHeight(80)` hard-code
pixel heights that ignore font size or DPI scaling. Users with larger fonts or high-DPI displays
may see truncated content with no way to resize.

**Recommended fix:** Remove `setFixedHeight` calls and let the detail `QFormLayout` expand
naturally inside the lower half of the `QSplitter`. Alternatively, set `minimumHeight` instead
of `fixedHeight` so the user can still drag the splitter.

---

## TD-8 — Duplicate `QPoint` import (LOW)

**File:** `pypost/ui/widgets/history_panel.py`, line 9

**Issue:** `from PySide6.QtCore import QPoint` appears as a second `from PySide6.QtCore import`
statement after the main one on line 4. `QPoint` should be merged into the existing import.

**Recommended fix:**
```python
from PySide6.QtCore import Qt, Signal, QPoint
```

---

## Positive Observations

- Constructor-injection pattern applied consistently across all new and modified classes.
- `threading.Lock` (not `QMutex`) keeps `HistoryManager` Qt-independent and fully unit-testable.
- All mutations wrapped in `try/except` at the service layer; history failures cannot surface to
  the caller.
- Observability is complete: DEBUG logging on every mutation, INFO on user-intent events, and two
  Prometheus counters tracking throughput.
- `datetime.utcnow()` deprecation was caught and fixed proactively during code cleanup.
