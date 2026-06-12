# PYPOST-65: Architecture — dedupe QPoint import

## Change

Single-line import consolidation in `pypost/ui/widgets/history_panel.py`:

```python
# Before (PYPOST-41)
from PySide6.QtCore import Qt, Signal
...
from PySide6.QtCore import QPoint

# After
from PySide6.QtCore import Qt, Signal, QPoint
```

## Components affected

| File | Change |
|------|--------|
| `pypost/ui/widgets/history_panel.py` | Merge duplicate QtCore import |

## No behavioral impact

`_on_context_menu(self, pos: QPoint)` and all Qt signal/slot wiring are unchanged.
