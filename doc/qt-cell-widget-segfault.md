# Segfault: QTableWidget cell widget, repeated clicks, wayland

Written up for an upstream report. Not filed yet.

## Summary

Clicking repeatedly into a `QTableWidget` cell crashes the process when the row
holds a cell widget set with `setCellWidget`. The crash is in C++ with no Python
frame below the event loop, reproduces with no application code involved, and
happens only under the `wayland` platform plugin.

PyPost hit this in its environment manager, where the Hidden column used a
`QCheckBox` inside a container widget. The fix on our side was to carry the
state on a checkable `QTableWidgetItem` instead; see
`pypost/ui/dialogs/env_dialog.py`.

## Environment

| | |
|---|---|
| PySide6 | 6.11.2 |
| Qt | 6.11.2 |
| Python | 3.11.16 |
| Platform plugin | `wayland` (WSLg, `WAYLAND_DISPLAY=wayland-0`) |
| OS | Linux 6.18.33.2-microsoft-standard-WSL2 |

`xcb` could not be tested on this machine: the plugin fails to load without
`libxcb-cursor0`.

## Reproducer

Roughly 30 lines, no application code. Run it as
`QT_QPA_PLATFORM=wayland python qt_repro.py`.

```python
"""Minimal reproducer: QTableWidget + setCellWidget segfaults on repeated clicks."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QHBoxLayout, QHeaderView,
    QTableWidget, QVBoxLayout, QWidget,
)

app = QApplication(sys.argv)
dialog = QDialog()
table = QTableWidget(0, 3)
table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
QVBoxLayout(dialog).addWidget(table)
dialog.show()
QTest.qWait(250)

table.setRowCount(1)
holder = QWidget()
box = QHBoxLayout(holder)
box.addWidget(QCheckBox())
box.setContentsMargins(0, 0, 0, 0)
table.setCellWidget(0, 2, holder)
QTest.qWait(200)

# Three single clicks in an empty cell, then a double-click.
pos = table.visualRect(table.model().index(0, 0)).center()
for _ in range(3):
    QTest.mouseClick(table.viewport(), Qt.LeftButton, Qt.NoModifier, pos)
    QTest.qWait(120)
QTest.mouseDClick(table.viewport(), Qt.LeftButton, Qt.NoModifier, pos)
QTest.qWait(250)
print("SURVIVED")
```

**Expected:** prints `SURVIVED`.
**Actual under wayland:** `Segmentation fault (core dumped)`, no output.

The three single clicks before the double-click are load-bearing. Four earlier
attempts that went straight to a double-click all survived.

## What was tried

Platform plugin, same script:

| Plugin | Result |
|---|---|
| `wayland` | **crash** |
| `offscreen` | survives |
| `minimal` | survives |

Variations, all under `wayland`:

| Variation | Result |
|---|---|
| As above | **crash** |
| Cell widget parented to the table | **crash** |
| Checkbox with no signal connected | **crash** |
| Python reference to the widget kept alive | **crash** |
| `gc.disable()` for the whole run | **crash** |
| Without `ResizeToContents` on the column | **crash** |
| With every other cell populated by items | **crash** |
| No cell widget at all | survives |
| Checkable `QTableWidgetItem` instead of the widget | survives |

Keeping a Python reference, reparenting and disabling the collector all leave
the crash unchanged, which argues against a PySide ownership problem in the
calling code.

## Faulthandler output

With `PYTHONFAULTHANDLER=1`, the deepest Python frame is the `exec()` call that
opened the dialog -- so the crash happens in C++ while no Python handler is on
the stack:

```
Fatal Python error: Segmentation fault

Current thread ... (most recent call first):
  File ".../pypost/ui/presenters/env_presenter.py", line 234 in _open_env_manager
  File ".../pypost/main.py", line 59 in main
```

## Workaround

Replace the cell widget with a checkable item. The same script with

```python
item = QTableWidgetItem()
item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
item.setCheckState(Qt.Unchecked)
table.setItem(0, 2, item)
```

prints `SURVIVED` under `wayland`.

## Note for whoever files this

Confirm whether it reproduces under `xcb` and on a non-WSL wayland compositor
before reporting; both are untested here. A backtrace from a debug build of Qt
would be worth attaching -- this write-up has none, since the crash was
diagnosed from the Python side.
