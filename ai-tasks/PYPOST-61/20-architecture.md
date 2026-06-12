# PYPOST-61: Architecture — module-level QTabWidget import

## Current state (before)

```
main_window.py (top)
  from PySide6.QtWidgets import (QApplication, QHBoxLayout, ...)

main_window._build_layout()
  from PySide6.QtWidgets import QTabWidget  ← deferred
  sidebar = QTabWidget()
```

## Target state

```
main_window.py (top)
  from PySide6.QtWidgets import (..., QTabWidget, ...)

main_window._build_layout()
  sidebar = QTabWidget()  ← uses module-level import
```

## Changes

| Component | Change |
|-----------|--------|
| `pypost/ui/main_window.py` | Add `QTabWidget` to top-level import tuple; remove method-body import |
| `tests/test_main_window.py` | Add test asserting sidebar is `QTabWidget` with expected tab labels |

## Backward compatibility

Runtime behavior unchanged — import location only.
