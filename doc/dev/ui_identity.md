# UI Widget Identity (PYPOST-834)

## Overview

Agents and automated harnesses locate key PyPost controls by stable Qt
**`objectName`** values. These identities are English snake_case constants
prefixed with `pypost_`. They do **not** change with theme, and they are not
derived from visible labels (so future locale changes will not break lookup).

Canonical constants live in `pypost/ui/widget_ids.py`. Apply them with
`set_widget_id(widget, widget_id)`, which sets `objectName` and mirrors the
same string on `accessibleIdentifier` when the widget is a `QWidget`.

Do **not** use `accessibleName`, `windowTitle`, or button/label `text()` as the
sole automation identity.

## Architecture

| Component | Role |
| --- | --- |
| `pypost/ui/widget_ids.py` | Canonical id strings + `set_widget_id` |
| Key UI constructors | Call `set_widget_id` once when widgets are created |
| `AgentAppSession` | Ensures UI ready before agents look up widgets |
| Spot-check | `tests/test_ui_identity_spotcheck.py` under `make test`
  (includes theme/`apply_settings` identity lock — PYPOST-844) |

```mermaid
flowchart LR
  Consts[widget_ids] --> Apply[set_widget_id]
  Apply --> Surfaces[Key widgets]
  Ready[is_ui_ready] --> Lookup[findChild by objectName]
  Surfaces --> Lookup
```

Production UI must not import `pypost.agent`. Agents import constants from
`widget_ids` and resolve widgets on `session.window` after ready.

## Naming convention

| Rule | Detail |
| --- | --- |
| Form | `pypost_<surface>` — ASCII snake_case |
| Prefix | Always `pypost_` |
| Primary API | `QObject.objectName` |
| Mirror | `QWidget.accessibleIdentifier` = same string |
| Not identity | Localized or cosmetic display strings |
| Per-tab controls | Same role name on every tab; **scope lookup to the current tab** |

## Key identities

| Constant | `objectName` | Surface |
| --- | --- | --- |
| `MAIN_WINDOW` | `pypost_main_window` | Main window |
| `COLLECTION_TREE` | `pypost_collection_tree` | Collections tree |
| `REQUEST_TABS` | `pypost_request_tabs` | Request tab widget |
| `METHOD_COMBO` | `pypost_method_combo` | HTTP method combo (per tab) |
| `URL_INPUT` | `pypost_url_input` | URL field (per tab) |
| `SEND_BUTTON` | `pypost_send_button` | Send button (per tab) |
| `REQUEST_BODY_EDIT` | `pypost_request_body_edit` | Request body editor (per tab) |
| `REQUEST_DETAIL_TABS` | `pypost_request_detail_tabs` | Params/Headers/Body/… tab widget |
| `RESPONSE_PANEL` | `pypost_response_panel` | Response panel (per tab) |
| `ENV_BAR` | `pypost_env_bar` | Environments top-bar container |
| `ENV_SELECTOR` | `pypost_env_selector` | Environment combo |
| `ENV_MANAGE_BUTTON` | `pypost_env_manage_button` | Manage environments |
| `SETTINGS_BUTTON` | `pypost_settings_button` | Settings entry |
| `PLUS_TAB_PLACEHOLDER` | `pypost_plus_tab_placeholder` | Trailing + tab chrome (not in KEY catalog) |

## API / Usage

### `set_widget_id(widget, widget_id)`

Sets `objectName` to `widget_id`. If `widget` is a `QWidget`, also sets
`accessibleIdentifier` to the same string when the Qt API is available.

### Lookup after UI ready

Use [AgentAppSession](agent_lifecycle.md) and wait until `is_ui_ready` before
resolving widgets:

```python
from PySide6.QtWidgets import QPushButton, QTreeView

from pypost.agent import AgentAppSession
from pypost.ui.widget_ids import COLLECTION_TREE, SEND_BUTTON, SETTINGS_BUTTON

with AgentAppSession(offscreen=True) as session:
    window = session.window
    tree = window.findChild(QTreeView, COLLECTION_TREE)
    settings = window.findChild(QPushButton, SETTINGS_BUTTON)
    tab = window.tabs.widget.currentWidget()
    send = tab.findChild(QPushButton, SEND_BUTTON)
```

Window-level chrome (tree, tabs, env, settings) can be found from `MainWindow`.
URL / method / Send / response must be found from the **current** `RequestTab`
(or an equivalent scoped parent); shared role names would otherwise resolve to
the first tab in the tree.

## Configuration

No environment variables. Identity strings are compile-time constants in
`widget_ids.py`. Theme and settings apply must not rewrite them.

## Spot-check

`tests/test_ui_identity_spotcheck.py` asserts key identities after ready
(run via `make test`).

## Troubleshooting

- **`findChild` returns `None`** — Wrong parent scope (use the current tab for
  per-tab ids), or the UI is not ready yet.
- **First tab Send instead of current** — Lookup used `MainWindow`; scope to
  `tabs.widget.currentWidget()`.
- **Identity changed after theme switch** — Should not happen; file a bug if
  `objectName` was cleared.
- **Adding a new key surface** — Add a constant to `widget_ids.py`, call
  `set_widget_id` at construction, then update this doc and the spot-check.


## Related

- [Agent UI E2E](agent_e2e.md) — umbrella + `make test-agent-e2e`
- [Agent lifecycle](agent_lifecycle.md) — launch → ready → shutdown
- [UI state snapshot](ui_snapshot.md) — visible-UI tree keyed by these names
- [UI action tools](ui_actions.md) — click / fill / select / send key by id
- [UI settle / wait helpers](ui_wait.md) — wait for conditions after actions
- [Agent golden e2e](agent_golden_e2e.md) — composed Send → response proof
- [GUI testing](gui_testing.md) — offscreen Qt test patterns
