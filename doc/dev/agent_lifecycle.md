# Agent App Lifecycle (PYPOST-833)

## Overview

Agents and automated harnesses start PyPost **in-process** via
`pypost.agent.lifecycle.AgentAppSession`. This is the project-supported automation
entry point for launch → ready → shutdown. Interactive humans keep `make run` →
`pypost.main.main()` (blocking `QApplication.exec()`).

Epic-wide `make agent-*` packaging is deferred to PYPOST-839.

## Entry point

```python
from pypost.agent import AgentAppSession

with AgentAppSession(offscreen=True) as session:
    # session.window.is_ui_ready is True here
    window = session.window
# shutdown runs on context exit
```

| Concern | API |
| --- | --- |
| Launch | `AgentAppSession.start()` / context manager |
| Ready | poll `session.window.is_ui_ready` (wait is inside `start()`) |
| Shutdown | `session.shutdown()` / context `__exit__` |
| Offscreen | `offscreen=True` (default) sets `QT_QPA_PLATFORM=offscreen` |

## Event-loop model

| Path | Event loop | Ready wait |
| --- | --- | --- |
| Interactive `main()` | Blocks on `app.exec()` | N/A (human) |
| `AgentAppSession` | Never calls `app.exec()`; pumps via `processEvents` | Until `is_ui_ready` or `TimeoutError` |

## Ready condition

`MainWindow.is_ui_ready` becomes true after startup collections and environments
loads complete and the existing restore gate
(`_maybe_complete_startup_restore`) has run. It does **not** wait for deferred
history load or all background work forever.

## Isolation

Agent sessions default to temporary `config_dir` / `data_dir` and an ephemeral
metrics port so parallel/CI runs do not contend with user dirs or fixed ports.

## Smoke

`tests/test_agent_lifecycle_smoke.py` covers launch → ready → shutdown under
`make test` (offscreen).
