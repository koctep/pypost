# PYPOST-926: Dev Docs

## Overview

Documented lazy PySide6 import in shared conftest: module load sets offscreen platform
and pytest hooks only; `QApplication` imports inside the `qapp` fixture.

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/gui_testing.md` | Conftest table + lazy import note |
| `doc/dev/testing.md` | Headless Qt section: conftest defers PySide6 until `qapp` |

## Contract test command

```bash
make test PYTEST_ARGS='tests/test_conftest_lazy_qt_import.py -v'
```
