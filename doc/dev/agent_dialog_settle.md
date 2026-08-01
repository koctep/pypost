# Agent E2E Product Dialog Settle (PYPOST-919)

## Overview

One `agent_e2e` module (`tests/test_agent_dialog_settle_e2e.py`) includes a
**happy-path** proof and a **forced-timeout companion** (PYPOST-934) that
asserts `step` plus modal scalar keys on `UiWaitTimeoutError.diagnostics`.

The happy-path scenario proves that the shared settle/wait stack can wait for
a **real product dialog** after a UI action — not only synthetic delayed
widgets (`tests/test_ui_wait.py`) or the response panel after Send
([Agent Golden E2E](agent_golden_e2e.md)).

The proof opens Settings via `SETTINGS_BUTTON`, settles with
`wait_until` on `QApplication.activeModalWidget()`, then dismisses the modal
so `SettingsDialog.exec()` returns. It is a **composition** proof only: no
Settings save/apply assertions, no new wait subsystem, and no change to the
Send → response golden.

Source debt: [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) TD-1
(missing product-dialog settle under PYPOST-837 / PYPOST-838).

## Architecture

| Piece | Role |
| --- | --- |
| `tests/test_agent_dialog_settle_e2e.py` | Two tests: happy path + timeout companion |
| `test_agent_dialog_settle_after_settings_open` | Happy-path modal settle + dismiss |
| `…timeout_includes_step_and_modal_diag` | Forced settle timeout companion (934) |
| `SETTINGS_BUTTON` | Stable open control ([ui_identity](ui_identity.md)) |
| `session.ui_click` | Drives `MainWindow.open_settings` → `exec()` |
| `session.wait_until` | Bounded poll ([ui_wait](ui_wait.md)) |
| `QApplication.activeModalWidget()` | Presence signal (`objectName == SETTINGS_DIALOG`) |
| `QTimer.singleShot` | Runs wait + `reject()` inside nested `exec()` |
| `UiWaitTimeoutError` | Rewrap with `step=wait_dialog_after_settings_open` |

```mermaid
flowchart LR
  Pre[QTimer.singleShot callback] --> Click[ui_click SETTINGS_BUTTON]
  Click --> Exec[SettingsDialog.exec]
  Exec --> Wait[wait_until activeModalWidget]
  Wait --> Reject[modal.reject]
  Reject --> Return[ui_click returns]
```

### Why timer-before-click

`SettingsDialog` opens with application-modal `exec()`. `ui_click` (via
`QTest.mouseClick`) does **not** return until the dialog closes. A naïve
“click then `wait_until`” never reaches the wait under a live modal.

Schedule the settle + dismiss with `QTimer.singleShot` **before**
`ui_click`, so the nested event loop runs the callback while `exec()` is
active. Always `reject()`/`close()` in `finally` so offscreen CI cannot hang
on an undismissed modal ([gui_testing](gui_testing.md)).

### Why not `wait_for_snapshot` / `wait_for_widget`

- Snapshot walks the **main window** tree; the modal is not a reliable child
  for that root.
- `SettingsDialog` exposes `SETTINGS_DIALOG` (`pypost_settings_dialog`) via
  `set_widget_id` — presence uses `activeModalWidget().objectName()`, not
  `wait_for_widget`.
- Prefer typed / simple waits over full-tree snapshot polls on hot paths
  ([ui_wait](ui_wait.md), PYPOST-852).

### Placement

Sibling module under `@pytest.mark.agent_e2e`, not inside
`tests/test_agent_golden_e2e.py`, so the Send golden stays single-purpose.
Harness table row: [agent_e2e.md](agent_e2e.md).

## API / Usage

### How to run

```bash
make test-agent-e2e
make test-agent-e2e PYTEST_ARGS="tests/test_agent_dialog_settle_e2e.py -v"
```

### Scenario steps

1. Ready session via `agent_e2e_session`; pre-flight `find_widget(SETTINGS_BUTTON)`.
2. `QTimer.singleShot(0, _on_dialog)` where `_on_dialog`:
   - `session.wait_until(_settings_dialog_present, …)`
   - on `UiWaitTimeoutError`, rewrap with `diagnostics["step"]` + modal scalars
   - `finally`: `activeModalWidget().reject()` if still open
3. `session.ui_click(SETTINGS_BUTTON)` (blocks in `exec` until reject).
4. Re-raise any callback error; assert settle succeeded.

### Timeout companion (PYPOST-934)

`test_agent_dialog_settle_timeout_includes_step_and_modal_diag` mirrors the
golden Send timeout companion
(`test_agent_golden_settle_timeout_includes_step_and_excerpt`):

1. Same timer-before-click skeleton; use a `settle_error: list[BaseException]`
   because the callback runs async while `ui_click` blocks in `exec()`.
2. Inside `_on_forced_timeout`, call `wait_until(lambda: False, …)` with
   `FORCED_SETTLE_TIMEOUT_S` and `condition_name="forced_dialog_settle_timeout"`.
3. On `UiWaitTimeoutError`, rewrap with the same `step` + `_modal_diag()` as
   the happy path.
4. After `ui_click` returns, assert `len(settle_error) == 1`, type is
   `UiWaitTimeoutError`, `diagnostics["step"] == SETTLE_STEP`, and keys
   `dialog_title` / `active_modal_type` are present (values may be `None`).

### Pattern sketch (do not redefine APIs)

```python
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pypost.agent import UiWaitTimeoutError, find_widget
from pypost.ui.widget_ids import SETTINGS_BUTTON

# inside agent_e2e_session test:
find_widget(session.window, SETTINGS_BUTTON)

def _on_dialog() -> None:
    try:
        session.wait_until(
            _settings_dialog_present,
            timeout=DIALOG_SETTLE_TIMEOUT_S,
            condition_name="settings_dialog_present",
        )
    except UiWaitTimeoutError as exc:
        raise UiWaitTimeoutError(
            f"dialog settle failed: {exc}",
            timeout_s=exc.timeout_s,
            condition=exc.condition,
            diagnostics={**exc.diagnostics, "step": SETTLE_STEP, ...},
        ) from exc
    finally:
        modal = QApplication.activeModalWidget()
        if modal is not None:
            modal.reject()

QTimer.singleShot(0, _on_dialog)
session.ui_click(SETTINGS_BUTTON)
```

Public surfaces consumed: `AgentAppSession` / `ui_click` / `wait_until`,
`find_widget`, `SETTINGS_BUTTON`, `UiWaitTimeoutError`. Predicate helpers and
`SETTLE_STEP` stay **test-local** in
`tests/test_agent_dialog_settle_e2e.py`.

### Presence predicate

`_settings_dialog_present()` requires:

1. `QApplication.activeModalWidget()` is not `None`
2. `modal.objectName() == SETTINGS_DIALOG` (see [ui_identity](ui_identity.md))

## Configuration

| Setting | Value |
| --- | --- |
| Module `pytest.mark.timeout` | 60 s |
| `DIALOG_SETTLE_TIMEOUT_S` | 10.0 (happy-path `wait_until` budget) |
| `FORCED_SETTLE_TIMEOUT_S` | 0.05 (companion near-zero budget) |
| Timer delay | `QTimer.singleShot(0, …)` |
| Happy-path `condition_name` | `settings_dialog_present` |
| Companion `condition_name` | `forced_dialog_settle_timeout` |
| `SETTLE_STEP` | `wait_dialog_after_settings_open` |

No extra environment variables. Prefer `make test-agent-e2e` for
`QT_QPA_PLATFORM=offscreen`.

## Troubleshooting

| Failure | What to do |
| --- | --- |
| Hang / module timeout on Settings click | You waited **after** `ui_click` with a |
| | live `exec()` modal. Schedule settle + dismiss |
| | **before** the click. |
| Dialog settle `UiWaitTimeoutError` | Look for |
| | `step=wait_dialog_after_settings_open`. Check |
| | `dialog_title` / `dialog_object_name` / `active_modal_type` on |
| | `err.diagnostics`; confirm `dialog_object_name` is |
| | `pypost_settings_dialog`. |
| `UiTargetNotFoundError` on Settings | Confirm `SETTINGS_BUTTON` and `is_ui_ready` |
| | ([ui_identity](ui_identity.md)). |
| Undismissed modal hangs teardown | Ensure `reject()`/`close()` in `finally` |
| | inside the timer callback. |
| Confused with Settings unit e2e | Those often **patch** `SettingsDialog.exec`. |
| | This scenario keeps a real modal to prove settle. |
| Companion diag assertion failure | Confirm rewrap still sets `step` and |
| | `_modal_diag()` keys. Near-zero budget may leave |
| | `dialog_title` / `active_modal_type` as `None`; asserts |
| | check key **presence**, not values. |

Observability reuses DEBUG `ui_wait_settled` / `ui_wait_timeout` with
`condition=settings_dialog_present`. Failure context is primarily the
exception path (`step` + modal scalars), not new production metrics. Catalog:
[logging.md](logging.md).

## Related

- [Agent UI E2E](agent_e2e.md) — umbrella, harness table, `make test-agent-e2e`
- [Agent Golden E2E](agent_golden_e2e.md) — Send → response (sibling proof)
- [UI Settle / Wait Helpers](ui_wait.md) — `wait_until` / `UiWaitTimeoutError`
- [UI Widget Identity](ui_identity.md) — `SETTINGS_BUTTON`
- [UI Action Tools](ui_actions.md) — `ui_click`
- [Settings Dialog](settings_dialog.md) — product Settings surface
- [GUI Testing](gui_testing.md) — offscreen Qt, modal hang pitfalls
- [Logging Event Naming Convention](logging.md) — `ui_wait_*` events
