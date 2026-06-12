# Keyboard shortcuts and Hotkeys dialog

## Overview

Application shortcuts are registered on `QAction` instances with metadata properties consumed by
**Help → Hotkeys** (`HotkeysDialog`). Registration helpers live in `pypost/ui/hotkeys.py`.

## Registering a shortcut

```python
from pypost.ui.hotkeys import register_hotkey, tag_action

# New action + shortcuts
register_hotkey(
    self,
    section="Tabs",
    label="New Tab",
    keys=("Ctrl+N",),
    slot=lambda: self.tabs.handle_new_tab("shortcut"),
    order=1,
)

# Existing menu QAction (e.g. Quit)
tag_action(
    quit_action,
    section="General",
    order=1,
    keys=("Ctrl+Q",),
    label="Quit Application",
)
```

### Multiple keys, one handler

Pass all keys in `keys`. The first is set on the `QAction`; alternates use `QShortcut`:

```python
register_hotkey(
    self,
    section="Request Editor",
    label="Send Request",
    keys=("F5", "Ctrl+Return"),
    slot=self.tabs.handle_send_request_global,
    order=1,
)
```

### Multiple keys, different handlers (one help row)

Use `register_hotkey_group` (e.g. Alt+1 … Alt+9 tab switch):

```python
register_hotkey_group(
    self,
    section="Tabs",
    label="Switch to Tab 1-9",
    bindings=tuple(
        (f"Alt+{i}", lambda idx=i - 1: self.tabs.handle_switch_to_tab(idx))
        for i in range(1, 10)
    ),
    order=5,
)
```

## QAction metadata properties

| Property | Purpose |
| --- | --- |
| `pypost_hotkey_section` | Section header (General, Tabs, Request Editor) |
| `pypost_hotkey_order` | Sort order within section |
| `pypost_hotkey_alt_keys` | Extra key strings for display / alternate bindings |
| `pypost_hotkey_collapse_keys` | Display as `Alt+1 ... Alt+9` when true |
| `pypost_hotkey_label` | Help text override when menu text differs |

## Hotkeys dialog

`HotkeysDialog(parent)` calls `collect_hotkey_rows(parent)` and renders a read-only table.
The parent must be `MainWindow` (or a widget subtree containing tagged actions).

## Tests

`tests/test_hotkeys.py` covers formatting, collection order, and dialog population.

## Out of scope for help dialog

Shortcuts not registered via these helpers (e.g. F2 rename in environment list, Ctrl+F in
response search) do not appear in Help → Hotkeys unless adopted later.
