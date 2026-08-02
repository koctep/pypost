# UI Settle / Wait Helpers (PYPOST-837)

## Overview

Agents and harnesses wait for asynchronous UI outcomes after actions via
`pypost.agent.ui_wait`. Helpers poll with `QCoreApplication.processEvents` until
a condition is true or a wall-clock timeout expires. Use them after Send, dialog
open, deferred enablement, or any flaky-prone async update — not as a
replacement for lifecycle ready (`is_ui_ready`).

This is an **in-process Python agent API**, not a network MCP tool. Call it from
tests or harnesses that already use [AgentAppSession](agent_lifecycle.md),
[UI action tools](ui_actions.md), and [UI state snapshot](ui_snapshot.md).

Production code must **not** import `tests.helpers`. The historic test helper
`tests.helpers.qt_wait.wait_until` re-exports the production poll loop
(PYPOST-837 / PYPOST-840). Regression locks live in
`tests/test_wait_until_dedup_lock.py`.

## Architecture

| Component | Role |
| --- | --- |
| `pypost/agent/ui_wait.py` | Poll loop, condition helpers, defaults, timeout error |
| `AgentAppSession.wait_*` | Convenience after `start()`; root = main window (or current tab when `in_current_tab=True` — PYPOST-949) |
| `capture_ui_snapshot` | Used by `wait_for_snapshot` |
| `find_widget` | Used by widget/enabled/text waits |
| Gate | `tests/test_ui_wait.py` under `make test` (multi-tab |
| | `in_current_tab` locks: text PYPOST-949; widget/enabled |
| | PYPOST-979) |
| Product dialog settle | [agent_dialog_settle.md](agent_dialog_settle.md) |
| | (`test_agent_dialog_settle_e2e`, PYPOST-919) |

```mermaid
flowchart LR
  Act[ui_click / ui_fill / …] --> Wait[wait_for_*]
  Wait --> Poll[processEvents + deadline]
  Poll -->|ok| Next[continue]
  Poll -->|timeout| Err[UiWaitTimeoutError]
```

## Timeouts

| Constant | Default | Meaning |
| --- | --- | --- |
| `DEFAULT_UI_WAIT_TIMEOUT_S` | `10.0` | Default budget for condition waits |
| `DEFAULT_UI_WAIT_INTERVAL_S` | `0.05` | Sleep between polls |

Lifecycle ready still uses `AgentAppSession(ready_timeout=30.0)` separately.
Override `timeout=` on any wait for slower dialogs or faster unit fixtures.

## API / Usage

### Errors

| Exception | When |
| --- | --- |
| `UiWaitTimeoutError` | Condition never true within `timeout` |

Attributes: `timeout_s`, `condition`, `diagnostics` (scalars / short strings).
Subclass of `TimeoutError` so existing `except TimeoutError` still works.

### `wait_until(condition, *, timeout=…, interval=…, message=…, …)`

Generic poll. Prefer the typed helpers below for common cases.

### `wait_for_widget(root, widget_id, *, timeout=…) -> QWidget`

Until a widget with that `objectName` exists under `root`.

### `wait_for_enabled(root, widget_id, *, timeout=…) -> QWidget`

Until the widget exists, is visible, and is enabled.

### `wait_for_text(root, widget_id, expected, *, timeout=…) -> QWidget`

Until text equals `expected` (string) or `expected(text)` is true. Supports
line/combo/label/button/plain/text edits. If the widget exists but has **no
text API**, fails immediately with `UiWaitTimeoutError`
(`condition=no_text_api`) instead of waiting out the timeout (PYPOST-852).

Golden Send → response settle prefers `wait_for_text` on
`RESPONSE_STATUS` / `RESPONSE_BODY` (display-form body; PYPOST-920) over a
panel-wide `wait_for_snapshot` predicate — see
[agent_golden_e2e.md](agent_golden_e2e.md). Sibling Send modules use
[agent_e2e_send_settle.md](agent_e2e_send_settle.md) (`wait_response_after_send`).

### `wait_for_snapshot(root, predicate, *, timeout=…) -> dict`

Until `predicate(capture_ui_snapshot(root))` is true. **Prefer
`wait_for_widget` / `wait_for_text` / `wait_for_enabled` on hot paths** —
snapshot polls re-walk the full visible tree each interval (PYPOST-852).

### Session helpers

`wait_for_widget`, `wait_for_enabled`, and `wait_for_text` accept optional
`in_current_tab=False`. When `True`, the search root is `current_request_tab()`
(same as [UI action tools](ui_actions.md) — PYPOST-851 / PYPOST-949). Default
window root preserves first-match behaviour for single-tab flows. Multi-tab
regression proofs:
`test_session_wait_for_text_in_current_tab_after_multi_tab_send` (PYPOST-949),
`test_session_wait_for_widget_in_current_tab_multi_tab` and
`test_session_wait_for_enabled_in_current_tab_multi_tab` (PYPOST-979).

```python
from pypost.agent import AgentAppSession
from pypost.ui.widget_ids import (
    RESPONSE_BODY,
    RESPONSE_STATUS,
    SEND_BUTTON,
    URL_INPUT,
)

with AgentAppSession(offscreen=True) as session:
    session.ui_fill(URL_INPUT, "https://example.com")
    session.wait_for_text(URL_INPUT, "https://example.com")
    session.ui_click(SEND_BUTTON)
    session.wait_for_enabled(SEND_BUTTON)  # example settle
    # Multi-tab Send on active tab:
    session.wait_for_text(
        RESPONSE_STATUS,
        "Status: 200",
        in_current_tab=True,
        timeout=15.0,
    )
    session.wait_for_text(
        RESPONSE_BODY,
        '{"ok": true}',
        in_current_tab=True,
        timeout=15.0,
    )
    session.wait_for_snapshot(
        lambda snap: snap.get("role") == "window",
        timeout=15.0,
    )
```

Golden Send → response flows prefer session helpers with
`in_current_tab=True`: `wait_response_after_send` for success settle, and
`session.wait_for_text(..., in_current_tab=True)` for direct text waits
(including the golden timeout companion). Module-level free functions still
accept any root for unit proofs or low-level harnesses — pass
`current_request_tab()` when you need a tab root without the session API.

## Configuration

No environment variables. Requires a started Qt app / `AgentAppSession`.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `UiWaitTimeoutError` with `found=False` | Wrong id, wrong root (try `in_current_tab=True` for multi-tab), or widget never created |
| `visible=False` / `enabled=False` | Widget exists but not interactable yet (or ever) |
| `actual_text=…` mismatch | Expected string/predicate wrong; text not updated |
| Snapshot wait slow / times out | Predicate too strict; prefer `wait_for_widget`/`text` |
| Hang without timeout | Do not nest `QEventLoop.exec()`; always pass a timeout |
| Modal dialog blocks click | Schedule `wait_until` + dismiss with
  `QTimer.singleShot` *before* `ui_click` — see
  [agent_dialog_settle.md](agent_dialog_settle.md) |

On timeout, read `err.diagnostics` and the exception message (includes key=value
pairs). DEBUG logs `ui_wait_settled` / `ui_wait_timeout` with timing scalars only.

## Related

- [Agent UI E2E](agent_e2e.md) — umbrella, `make test-agent-e2e`
- [Agent E2E Product Dialog Settle](agent_dialog_settle.md) — Settings modal
  settle (PYPOST-919)
- [Agent lifecycle](agent_lifecycle.md) — launch → ready → shutdown
- [UI action tools](ui_actions.md) — click / fill / select / send key
- [UI state snapshot](ui_snapshot.md) — observation tree for predicates
- [UI widget identity](ui_identity.md) — stable `objectName` catalog
- [Agent golden e2e](agent_golden_e2e.md) — composed Send → response proof
- [GUI testing](gui_testing.md) — offscreen Qt / bounded waits
- [Logging](logging.md) — `ui_wait_settled` / `ui_wait_timeout`
