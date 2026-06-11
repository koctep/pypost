# GUI Testing (Qt / PySide6)

## Overview

PyPost desktop UI tests run headlessly in CI and locally using Qt's **offscreen** platform and a
module-scoped `QApplication` fixture. The project does **not** depend on the `pytest-qt` package;
tests invoke widget methods and read properties directly.

## Prerequisites

- Virtualenv with app and test dependencies (`make install`).
- `QT_QPA_PLATFORM=offscreen` — set automatically in `tests/conftest.py` and `make test`.

On Linux CI without a display, offscreen is sufficient; Xvfb is optional and not required by this
project.

## Architecture

| Component | Role |
| --- | --- |
| `tests/conftest.py` | Sets offscreen platform; shared `qapp` fixture; enforces per-test timeouts |
| Module `pytestmark` | `pytest.mark.timeout(60)` (or 120 for heavy e2e) |
| `qapp` fixture | `QApplication.instance() or QApplication([])`, scope `module` |
| Widget under test | Constructed in test; closed in `finally` block |

Representative modules:

| Module | Focus |
| --- | --- |
| `tests/test_env_dialog.py` | Environment dialog widgets and MCP toggle |
| `tests/test_settings_dialog.py` | Settings form fields |
| `tests/test_settings_encryption_migration_ui.py` | Migration buttons and QMessageBox delegation |
| `tests/test_new_variable_flow_integration.py` | ResponseView → EnvPresenter signals |
| `tests/test_response_view_search.py` | Response body search bar (PYPOST-365) |

## Writing a GUI Test

```python
import pytest

pytestmark = pytest.mark.timeout(60)

from pypost.ui.widgets.response_view import ResponseView


class TestMyWidget:
    def test_behavior(self, qapp):
        widget = ResponseView()
        try:
            widget.body_view.setPlainText("sample")
            # assert on labels, models, or mocked dialogs
        finally:
            widget.close()
```

### Patterns

- **Dialogs**: patch `QMessageBox` / `QInputDialog` at the module that shows them.
- **Metrics**: pass `metrics=MagicMock()` and assert `track_*` calls.
- **Storage / services**: `MagicMock(spec=...)` or helpers under `tests/helpers/`.
- **Event loop**: prefer calling slot methods directly; for polling use bounded `QTimer` helpers
  (see `tests/test_env_storage_responsiveness.py`).

### Timeouts

Every test must declare `pytest.mark.timeout`. Use 30–60s for widget tests, 60–120s for
integration/e2e. Do not use `method="thread"` on Qt event-loop tests — see
[do-testing.md](../../.cursor/lsr/do-testing.md).

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `QT_QPA_PLATFORM` | `offscreen` | Headless Qt platform |

## Running Tests

Full suite:

```bash
make test
```

Focused GUI modules:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_response_view_search.py \
  tests/test_env_dialog.py \
  -v --tb=short
```

## Troubleshooting

| Issue | Solution |
| --- | --- |
| `QApplication` already exists | Use module-scoped `qapp`; do not create per-test `QApplication` |
| Segfault in CI | Ensure offscreen is set before any `PySide6` import |
| Test hangs | Add explicit timeout marker; bound internal waits with `QTimer` |
| Missing timeout marker | `conftest.py` fails setup — add `pytestmark` or per-function marker |

## References

- [testing.md](testing.md) — suite-wide timeout and MCP testing
- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md) — agent rules
- [PYPOST-365](https://pypost.atlassian.net/browse/PYPOST-365) — GUI patterns and search tests
