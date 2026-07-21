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

### Shared `qapp` — two valid consumers (PYPOST-830)

All Qt tests must obtain the process singleton from `tests/conftest.py`. Do **not**
create a module-local `QApplication` in `setUpClass` (or a duplicate local
`def qapp()`). Two request styles are supported:

| Style | When to use | Examples |
| --- | --- | --- |
| Fixture parameter `qapp` | Plain pytest / non-`TestCase` | Responsiveness, widgets |
| `@pytest.mark.usefixtures("qapp")` | `unittest.TestCase` | Gateway units + H3 stress |

Gateway surface aligned onto `usefixtures` (PYPOST-830):

- `tests/test_environment_storage_gateway.py`
- `tests/test_collection_storage_gateway.py`
- `tests/test_storage_gateway_h3_stress.py`

```python
import unittest

import pytest

pytestmark = pytest.mark.timeout(120)


@pytest.mark.usefixtures("qapp")
class TestEnvironmentStorageGateway(unittest.TestCase):
    def test_load_async_emits_load_completed(self):
        # QApplication already provided by shared fixture
        ...
```

Plain pytest class (parameter style):

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
  second module-local `QApplication` (including via `setUpClass`).

### Bounded nested `QEventLoop` waits (PYPOST-823 / PYPOST-827 / PYPOST-828)

Waiting for `QThread` queued signals with a nested `QEventLoop.exec()` is fine **only** if the
wait is guaranteed to return to Python on a wall-clock deadline. A QTimer-only timeout is not
enough: if timer slots never run, `exec()` stays in Qt C++ and `pytest-timeout` SIGALRM cannot
interrupt it (multi-minute stalls past the module timeout until SIGTERM).

Shared hang-resistant wait: `tests.helpers.process_until.process_until`
(`tests/helpers/process_until.py`). Use it for any nested-`exec()` wait that must finish on a
wall-clock deadline.

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
4. Prefer shared `qapp` from `tests/conftest.py` (parameter or
   `usefixtures("qapp")` on `TestCase` — see § Shared `qapp` above).

#### Timeout diagnostics (PYPOST-828)

On deadline with the predicate still false, `process_until` raises `AssertionError` with a
**neutral** reason (no env-biased signal names) plus an optional lazy snapshot:

```text
condition not met within {timeout_ms}ms
(wall-clock deadline; predicate still false)[; <timeout_detail>]
```

| API | Role |
| --- | --- |
| `timeout_detail: Callable[[], str] \| None` | Evaluated **only on timeout**; appended after `; ` |
| `format_storage_async_timeout_detail(...)` | Formats `busy=` / `pending=` and optional |
| | `worker_running=` / `worker_operation=` (omit `None`) |
| `gateway_timeout_detail(gateway)` | One-liner lazy snapshot for gateway waits |

Rules:

- **Gateway** load/save waits: pass busy/pending (use `gateway_timeout_detail`).
- **Worker-only** waits: optional `worker_running` (busy/pending omitted).
- **Hang-regression** / no domain context: omit `timeout_detail`; default text is enough.
- Detail failures never mask the timeout (`timeout_detail failed: ...` note) and never
  extend the hang-defense deadline.

Example (gateway wait):

```python
from tests.helpers.process_until import gateway_timeout_detail, process_until

process_until(
    lambda: spy.count() >= 1 or fail_spy.count() >= 1,
    timeout_ms=10_000,
    timeout_detail=gateway_timeout_detail(gateway),
)
```

Example failure text:

```text
condition not met within 10000ms (wall-clock deadline; predicate still false);
busy=True pending=True worker_running=True
```

Focused diagnostic tests: `tests/test_process_until_diagnostics.py`.

Hang-regression coverage in `tests/test_env_storage_responsiveness.py`:

- `test_process_until_exits_on_wall_clock_deadline`
- `test_process_until_exits_via_posted_quit_without_poll_timer`

Modules that use the shared helper (PYPOST-827 / PYPOST-828 / PYPOST-877):

- `tests/test_env_storage_responsiveness.py` — `qapp` parameter
- `tests/test_environment_storage_gateway.py` — `usefixtures("qapp")`
- `tests/test_collection_storage_gateway.py` — `usefixtures("qapp")`
- `tests/test_collection_storage_worker.py` — still module-local `setUpClass`
  (follow-up; not gateway surface)
- `tests/test_env_presenter.py` — still module-local `setUpClass` qapp
  (suite-wide migration: PYPOST-886); async-load encryption refresh wait and
  hang-exit proof use shared `process_until` (PYPOST-877)

H3 worker-lifecycle canary (PYPOST-829): `tests/test_storage_gateway_h3_stress.py`
(≥200 rapid cycles + GC per gateway; shared `qapp` via `usefixtures`, PYPOST-830).
Prefer isolation when triaging native crashes.

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
| `QApplication` already exists | Use shared `qapp` (param or `usefixtures`); no `setUpClass` app |
| Segfault in CI | Ensure offscreen is set before any `PySide6` import |
| Segfault in storage gateway finish | Historical H3 — run `tests/test_storage_gateway_h3_stress.py` in isolation (PYPOST-829) |
| Hang past module timeout | SIGALRM cannot cut stuck `exec()` — use § Bounded nested waits |
| Timeout assert hard to triage | Pass `timeout_detail` / `gateway_timeout_detail` (PYPOST-828) |
| Test hangs (general) | Add timeout marker; bound waits; prefer `wait_until` (no nested `exec()`) |
| Missing timeout marker | `conftest.py` fails setup — add `pytestmark` or per-function marker |
| ELF `core` file in repo root | Native crash (SIGSEGV), not a Python exception. Delete the file; do not commit. Repo-root `/core` is gitignored. Run tests via `make test` or set `QT_QPA_PLATFORM=offscreen`. If it recurs, capture `lldb -c core --batch -o bt` and file a ticket with Python/PySide6 versions. See [PYPOST-429 investigation](../../ai-tasks/PYPOST-429/investigation-report.md). |

## Agent UI e2e (in-process)

Umbrella guide (setup, tools, identity, golden, `make test-agent-e2e`):
[Agent UI E2E](agent_e2e.md). Environment pack contract (seed, isolation,
fixtures inventory): [Agent E2E Environment Contract](agent_e2e_env.md).

Prefer shared fixtures `agent_e2e_session` / `seeded_agent_e2e_session`
(mark modules `@pytest.mark.agent_e2e`). For launch → ready → shutdown
without `app.exec()`, those fixtures wrap
[`AgentAppSession`](agent_lifecycle.md) (`pypost.agent.lifecycle`). Direct
construction remains valid for multi-session isolation proofs. Smoke
coverage is `tests/test_agent_lifecycle_smoke.py`.

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
- [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) — shared `process_until` for siblings
- [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) — richer timeout diagnostics
- [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) —
  gateway `TestCase` shared `qapp` via `usefixtures`
- [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877) —
  env-presenter async-load wait on shared `process_until`
