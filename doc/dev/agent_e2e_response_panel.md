# Agent E2E Response-Panel Snapshot Helpers (PYPOST-869)

## Overview

Shared helpers for inspecting the **response panel** subtree of an agent
UI snapshot after Send. Env-pack Send, double-body lock, and
presentation-matrix scenarios import these instead of copying walk /
subtree / excerpt logic.

Golden (PYPOST-920) and sibling Send modules (PYPOST-948) settle readiness
with `wait_for_text` on `RESPONSE_STATUS` / `RESPONSE_BODY` (siblings via
[Send settle helper](agent_e2e_send_settle.md)). These panel helpers remain
for post-settle walks, cardinality locks, joined-value asserts, and timeout
excerpts — not for Send readiness predicates.

## Architecture

| Piece | Role |
| --- | --- |
| `tests/helpers/agent_e2e_response_panel.py` | Pure helpers on snapshot dict trees |
| `tests/test_agent_e2e_response_panel.py` | Unit proof + no-local-duplicate guard |
| Send scenario modules | Local ready predicates; import helpers |

```mermaid
flowchart LR
  Snap[ui_snapshot dict] --> RP[agent_e2e_response_panel]
  RP --> Assert[cardinality / joined asserts]
  RP --> Diag[timeout response_excerpt]
  Send[Send settle] --> TextWait[agent_e2e_send_settle]
  TextWait --> Diag
```

Send readiness uses identity text waits (see
[agent_e2e_send_settle.md](agent_e2e_send_settle.md)). Scenario-specific
expected tokens stay in each test module; only tree walk / panel extract /
join / excerpt are shared here.

## API / Usage

```python
from tests.helpers.agent_e2e_response_panel import (
    joined_panel_values,
    response_panel_excerpt,
    subtree_by_name,
    walk_values,
)
from pypost.ui.widget_ids import RESPONSE_PANEL

panel = subtree_by_name(snap, RESPONSE_PANEL)
joined = joined_panel_values(snap)
assert joined.count("pypost-887-lock-body-once") == 1
excerpt = response_panel_excerpt(snap)  # truncated " | "-join for messages
```

### `walk_values(node)`

Depth-first list of non-empty string `value` fields under `node`.

### `subtree_by_name(node, name)`

First matching subtree by `name`, or `None`.

### `response_panel_excerpt(snap, *, max_len=400)`

`RESPONSE_PANEL` values joined with ` | `, truncated with `…` when longer
than `max_len`. Missing panel → `"<response panel not in snapshot>"`.

### `joined_panel_values(snap)`

`RESPONSE_PANEL` values joined with newlines, or `""` if missing.

## Configuration

None. Helpers are pure functions; they import `RESPONSE_PANEL` from
`pypost.ui.widget_ids`.

## Running the unit proof

```bash
make test PYTEST_ARGS="tests/test_agent_e2e_response_panel.py -v"
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Import error for helpers | Module path is `tests.helpers.agent_e2e_response_panel` |
| Duplicate `_walk_values` in a Send module | Remove local copy; import shared helpers (unit guard fails otherwise) |
| Excerpt empty / “not in snapshot” | Confirm Send settled; panel id is `RESPONSE_PANEL` |

## See also

- [Agent E2E Send Settle Helpers](agent_e2e_send_settle.md)
- [Agent UI E2E](agent_e2e.md)
- [Agent Golden E2E](agent_golden_e2e.md)
- [Agent E2E HTTP Fixture Layer](agent_e2e_http.md)
- [UI State Snapshot](ui_snapshot.md)
