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
| `tests/test_settings_dialog.py` | Settings form fields, alert auth, retryable codes save validation (PYPOST-444) |
| `tests/test_settings_encryption_migration_ui.py` | Migration buttons and QMessageBox delegation |
| `tests/test_new_variable_flow_integration.py` | ResponseView → EnvPresenter signals |
| `tests/test_response_view_search.py` | Response body search bar (PYPOST-365) |
| `tests/test_response_view_context_menu.py` | Response body context menu (PYPOST-164) |
| `tests/test_response_search_flow_integration.py` | RequestTab search flow (PYPOST-357) |

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
- **Event loop**: prefer calling slot methods directly; for polling use bounded waits (see
  § Bounded nested `QEventLoop` waits below). Use the shared `qapp` fixture — do not create a
  second module-local `QApplication`.

### Bounded nested `QEventLoop` waits (PYPOST-823)

Waiting for `QThread` queued signals with a nested `QEventLoop.exec()` is fine **only** if the
wait is guaranteed to return to Python on a wall-clock deadline. A QTimer-only timeout is not
enough: if timer slots never run, `exec()` stays in Qt C++ and `pytest-timeout` SIGALRM cannot
interrupt it (multi-minute stalls past the module timeout until SIGTERM).

Reference implementation: `_process_until` in `tests/test_env_storage_responsiveness.py`.

| Defense | Role |
| --- | --- |
| Qt poll `QTimer` (10 ms) | Checks the predicate and pumps the nested loop |
| `time.monotonic()` deadline | Deadline independent of timer tick delivery |
| Daemon Timer + posted quit | `singleShot(0, loop, loop.quit)` on GUI thread if poll dies |

Contract:

1. Exit when `predicate()` is true **or** the wall-clock deadline passes.
2. Assert with a clear message on deadline (do not hang).
3. Keep `pytest.mark.timeout` (default signal method). Do **not** use `method="thread"` for
   Qt event-loop tests.
4. Prefer shared `qapp` from `tests/conftest.py`.

Hang-regression coverage in the same module:

- `test_process_until_exits_on_wall_clock_deadline`
- `test_process_until_exits_via_posted_quit_without_poll_timer`

Sibling gateway/worker tests still use older QTimer-only `_process_until` copies; porting them
is tracked as [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827).

### Timeouts

Every test must declare `pytest.mark.timeout`. Use 30–60s for widget tests, 60–120s for
integration/e2e. Do not use `method="thread"` on Qt event-loop tests — see
[do-testing.md](../../.cursor/lsr/do-testing.md). Nested `QEventLoop` waits still need an
internal wall-clock + posted-quit defense (PYPOST-823); the outer timeout is only a backstop
once Python runs again.

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
| Hang past module timeout | SIGALRM cannot cut stuck `exec()` — use § Bounded nested waits |
| Test hangs (general) | Add timeout marker; bound waits; prefer `wait_until` (no nested `exec()`) |
| Missing timeout marker | `conftest.py` fails setup — add `pytestmark` or per-function marker |
| ELF `core` file in repo root | Native crash (SIGSEGV), not a Python exception. Delete the file; do not commit. Repo-root `/core` is gitignored. Run tests via `make test` or set `QT_QPA_PLATFORM=offscreen`. If it recurs, capture `lldb -c core --batch -o bt` and file a ticket with Python/PySide6 versions. See [PYPOST-429 investigation](../../ai-tasks/PYPOST-429/investigation-report.md). |

## Agent UI e2e (in-process)

Umbrella guide (setup, tools, identity, golden, `make test-agent-e2e`):
[Agent UI E2E](agent_e2e.md). Environment pack contract (seed, isolation,
fixtures inventory): [Agent E2E Environment Contract](agent_e2e_env.md).

For launch → ready → shutdown without `app.exec()`, use
[`AgentAppSession`](agent_lifecycle.md) (`pypost.agent.lifecycle`). See that doc for
the contract; smoke coverage is `tests/test_agent_lifecycle_smoke.py`.

After ready, locate key controls by stable `objectName` values — see
[UI widget identity](ui_identity.md) (`pypost/ui/widget_ids.py`).

Capture a structured visible-UI tree for post-action checks — see
[UI state snapshot](ui_snapshot.md) (`capture_ui_snapshot` /
`AgentAppSession.ui_snapshot()`).

Drive named controls (click / fill / select / send key) — see
[UI action tools](ui_actions.md) (`pypost.agent.ui_actions`).

Wait for async settle conditions after actions — see
[UI settle / wait helpers](ui_wait.md) (`pypost.agent.ui_wait`). Test-only
`tests.helpers.qt_wait.wait_until` re-exports the production poll helper.

Composed golden product flow (Send → response UI) — see
[Agent golden e2e](agent_golden_e2e.md) (`tests/test_agent_golden_e2e.py`).

Run the harness set with:

```bash
make test-agent-e2e
```

## References

- [testing.md](testing.md) — suite-wide timeout and MCP testing
- [testability.md](testability.md) — RequestService / HTTPClient / MainWindow seams (PYPOST-382)
- [environment_storage_async.md](environment_storage_async.md) — encrypted load/save tests
- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md) — agent rules
- [PYPOST-365](https://pypost.atlassian.net/browse/PYPOST-365) — GUI patterns and search tests
- [PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823) — nested `QEventLoop` hang defense
