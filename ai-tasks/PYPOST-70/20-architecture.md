# PYPOST-70: Architecture — rename shadowing layout attribute

## Current (before)

```python
class RequestTab(QWidget):
    def __init__(...):
        self.layout = QVBoxLayout(self)  # shadows QWidget.layout()
        ...
        self.layout.addWidget(self.splitter)
```

## Target (after)

```python
class RequestTab(QWidget):
    def __init__(...):
        self._content_layout = QVBoxLayout(self)
        ...
        self._content_layout.addWidget(self.splitter)
```

`QVBoxLayout(self)` still registers the layout with Qt; `_content_layout` is a private handle
for `addWidget` only. External code and Qt use `tab.layout()`.

## Changes

| Component | Change |
|-----------|--------|
| `tabs_presenter.py` | Rename `self.layout` → `self._content_layout` (2 sites) |
| `test_tabs_presenter.py` | Add `test_request_tab_layout_method_not_shadowed` |

## Backward compatibility

- No public API change; visual layout unchanged.
- No callers referenced `RequestTab.layout` as an attribute (grep confirmed).
