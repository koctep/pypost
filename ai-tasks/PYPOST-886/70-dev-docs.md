# PYPOST-886: Developer Documentation

## Updates

| File | Change |
| --- | --- |
| `doc/dev/gui_testing.md` | Shared-`qapp` section now covers suite-wide PYPOST-886 alignment; env presenter listed as `usefixtures`; troubleshooting + references updated |
| `doc/dev/testing.md` | GUI/Qt section notes suite inventory guard and PYPOST-886 |
| `doc/dev/environment_storage_async.md` | Removed “presenters still on local setUpClass” deferral; points to shared fixture |

## Overview

Qt tests obtain `QApplication` only from `tests/conftest.py` (`qapp` parameter
or `@pytest.mark.usefixtures("qapp")`). Local `setUpClass` / `def qapp()` /
`_get_app()` ownership is forbidden; `tests/test_suite_qapp_alignment.py`
enforces the inventory.

## User docs

N/A — harness-only.
