# Blank-tab protocol picker (PYPOST-1157, PYPOST-1165, PYPOST-1180)

## Overview

`Ctrl+N` and the tab-bar **+** show a protocol picker **before** any new
workspace editor is created. The user chooses **HTTP Request** (default),
**WebSocket**, or **MCP Client**. Confirming HTTP opens a blank
`RequestTab`. Confirming WebSocket opens a blank `WebSocketTab` via
`add_blank_websocket_tab` (not the Collections/restore path). Confirming
**MCP Client** opens a draft `McpClientTab` via `add_blank_mcp_client_tab`
(not HTTP). Chrome (URL, Connect / Disconnect, empty tools, restore
omission, close teardown) is [mcp_client_draft_tab.md](mcp_client_draft_tab.md)
([PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)).
WebSocket draft persist and dirty-close:
[websocket_draft_tab.md](websocket_draft_tab.md)
([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)).
Dismissing the menu creates no tab and emits no new-tab
metric.

WS-TM-1 ([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157))
shipped the picker with two items. MCP-TM-1
([PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)) added
the third item. [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180)
closed verification debt: hermetic unit proofs that `prompt()` maps
HTTP / WebSocket / dismiss (same mocked-`exec` pattern as MCP Client).
Production mapping was already correct; no product change. The picker
is Option A: a popup `QMenu` with **HTTP Request** first and
`setActiveAction` so Enter still confirms HTTP.

User-facing copy of `Ctrl+N` / **+** is
[PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) (WebSocket)
and [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)
(MCP Client). Do not rewrite `doc/user/` here.

## Architecture

- **`NewTabProtocolPicker`**
  (`pypost/ui/widgets/new_tab_protocol_picker.py`):
  Option A `QMenu`. Labels **HTTP Request**, **WebSocket**, **MCP Client**.
  `prompt()` returns `TabProtocol | None`.
- **`TabProtocol`**: enum values `http` / `websocket` / `mcp_client` —
  the same strings used as metrics `protocol` labels.
- **`McpClientTab`** (`pypost/ui/widgets/mcp_client/mcp_client_tab.py`):
  draft workspace page (widget id `MCP_CLIENT_TAB_PAGE`). Factory wires
  `McpClientConnection` + `McpClientPresenter`. See
  [mcp_client_draft_tab.md](mcp_client_draft_tab.md).
- **`TabsPresenter.handle_new_tab(source)`**: logs
  `new_tab_action_triggered`, calls the injectable picker, then either
  returns (cancel) or `open_blank_tab(protocol, source)`.
- **`TabsPresenter.open_blank_tab(protocol, source)`**: single routing
  API. Records metrics, then HTTP → `add_new_tab()`, WebSocket →
  `add_blank_websocket_tab()`, MCP Client → `add_blank_mcp_client_tab()`.
  The MCP branch is **explicit and before** the HTTP fallback so
  `MCP_CLIENT` never falls through to `add_new_tab()`.
- **`RequestTabHeader`**: unchanged. **+** still emits
  `new_tab_requested` → `handle_new_tab("plus_button")`.
- **`MainWindow`**: `Ctrl+N` still calls `handle_new_tab("shortcut")`.

```mermaid
flowchart TB
    CtrlN["Ctrl+N → handle_new_tab shortcut"]
    PlusBtn["Tab-bar + → handle_new_tab plus_button"]
    LastTab["Close last tab → handle_new_tab last_tab"]
    HandleNew["handle_new_tab(source)"]
    Picker["NewTabProtocolPicker.prompt"]
    OpenBlank["open_blank_tab(protocol, source)"]
    Metrics["track_gui_new_tab_action(source, protocol)"]
    AddHTTP["add_new_tab() → RequestTab"]
    AddWS["add_blank_websocket_tab() → WebSocketTab"]
    AddMCP["add_blank_mcp_client_tab() → McpClientTab draft"]
    SavedWS["open_websocket_tab(conn) Collections/restore"]

    CtrlN --> HandleNew
    PlusBtn --> HandleNew
    LastTab --> HandleNew
    HandleNew --> Picker
    Picker -->|None cancel| HandleNew
    Picker -->|HTTP WS or MCP_CLIENT| OpenBlank
    OpenBlank --> Metrics
    OpenBlank -->|HTTP| AddHTTP
    OpenBlank -->|WEBSOCKET| AddWS
    OpenBlank -->|MCP_CLIENT| AddMCP
    SavedWS -.->|not the blank-tab path| AddWS
```

| Path | API | Tab kind | Metric |
| --- | --- | --- | --- |
| `Ctrl+N` / **+**, HTTP | `open_blank_tab(HTTP, source)` | Blank `RequestTab` | `source` + `protocol=http` |
| `Ctrl+N` / **+**, WebSocket | `open_blank_tab(WEBSOCKET, source)` | Blank `WebSocketTab` | `source` + `protocol=websocket` |
| `Ctrl+N` / **+**, MCP Client | `open_blank_tab(MCP_CLIENT, source)` | Draft `McpClientTab` | `source` + `protocol=mcp_client` |
| `Ctrl+N` / **+**, cancel | `handle_new_tab` returns | Unchanged | None |
| Collections / restore WS | `open_websocket_tab(conn)` | Saved `WebSocketTab` | Unchanged |
| Collections **New tab** HTTP | `add_new_tab(copy)` | Isolated `RequestTab` | `collections_context` + `protocol=unknown` |
| Close last tab | `handle_new_tab("last_tab")` → `open_blank_tab` | HTTP / WS / MCP draft, or none on cancel | `source=last_tab` + `protocol` |
| Collections legacy `method: "MCP"` | `open_legacy_mcp_request_tab` | `McpClientTab` (convert-on-open) | Unchanged |

`add_blank_websocket_tab` builds `WebSocketConnection()` +
`WebSocketPresenter` + `WebSocketTab` and inserts before the plus tab.
It must **not** call `open_websocket_tab` (that API dedups by saved
connection id and is the Collections/restore path). Unsaved draft ids
are omitted from `save_tabs_state`; dirty close prompts Discard / Keep:
[websocket_draft_tab.md](websocket_draft_tab.md).

`add_blank_mcp_client_tab` constructs `McpClientConnection()` +
`McpClientPresenter` + `McpClientTab` and inserts before the plus tab
with title `"New MCP Client"`. It must **not** call `add_new_tab` or
`open_websocket_tab`. `_request_tab_count` includes `McpClientTab` so
close-last-tab does not treat an MCP-only strip as empty. Unsaved drafts
are omitted from `save_tabs_state` until MCP-TM-7
([mcp_client_draft_tab.md](mcp_client_draft_tab.md)).

### Out of scope

| Topic | Owner |
| --- | --- |
| Blank WebSocket draft persist, dirty-close | [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) (shipped) |
| Close-last-tab / empty-workspace picker | [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159) (shipped — [last_tab_protocol_picker.md](last_tab_protocol_picker.md)) |
| MCP Client draft shell (URL, Connect, tools) | [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) (shipped) |
| MCP Client Headers + `execute_outbound` | [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) (shipped) |
| User documentation rewrite (MCP Client) | [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168) |

PYPOST-1158 lifecycle details:
[websocket_draft_tab.md](websocket_draft_tab.md).

## API / Usage

### `TabProtocol`

```python
class TabProtocol(str, Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"
    MCP_CLIENT = "mcp_client"
```

### `NewTabProtocolPicker.build_menu(parent=None) -> QMenu`

Constructs the menu without showing it.

- Actions in order: **HTTP Request**, **WebSocket**, **MCP Client**.
- First action is `setActiveAction` so Enter confirms HTTP.
- Widget id: `NEW_TAB_PROTOCOL_MENU` (`pypost_new_tab_protocol_menu`)
  via `set_widget_id`.
- Action `data()` is `TabProtocol.HTTP` / `WEBSOCKET` / `MCP_CLIENT`.

Unit-test chrome here. Do **not** call live `exec()` in CI.

### `NewTabProtocolPicker.prompt(parent=None, *, anchor=None) -> TabProtocol | None`

Shows the menu at `anchor`, or under the plus button when `parent`
contains `PLUS_TAB_BUTTON`, else `QCursor.pos()`. Passes the HTTP
action as `exec(pos, http_action)` so the default stays highlighted
when a third item is present.

- **Returns**: chosen `TabProtocol` (`HTTP`, `WEBSOCKET`, or
  `MCP_CLIENT`), or `None` if Esc / click-away / unmatched action.

`prompt()` maps action `data()` via `TabProtocol(data)`. Unmapped data
returns `None` (looks like cancel).

`handle_new_tab` calls `_protocol_picker(self._tabs)` (parent only).

### `TabsPresenter.handle_new_tab(source: str = "unknown")`

Shared entry for `Ctrl+N` (`shortcut`), **+** (`plus_button`), and
last-tab empty-workspace replacement (`last_tab`).

1. INFO `new_tab_action_triggered source=<source> tabs_before=<count>`.
1. `protocol = self._protocol_picker(self._tabs)`.
1. If `None`: INFO `new_tab_action_cancelled source=<source>`; return
   (no tab, no metric).
1. Else `open_blank_tab(protocol, source)`.

### `TabsPresenter.open_blank_tab(protocol: TabProtocol, source: str)`

Single routing API after a completed choice.

1. INFO `new_tab_action_completed source=<source> protocol=<value>`.
1. `track_gui_new_tab_action(source, protocol=protocol.value)`.
1. `TabProtocol.WEBSOCKET` → `add_blank_websocket_tab()`.
1. `TabProtocol.MCP_CLIENT` → `add_blank_mcp_client_tab()`.
1. Otherwise → `add_new_tab()` (HTTP blank `RequestTab`).

HTTP remains the final fallback for `TabProtocol.HTTP` only. Do not
treat every non-WebSocket confirm as HTTP.

Last-tab close (`last_tab`) and future entry points should call this
after a choice, not duplicate factories. See
[last_tab_protocol_picker.md](last_tab_protocol_picker.md).

### `TabsPresenter.add_blank_websocket_tab(*, save_state: bool = True) -> WebSocketTab`

Blank WebSocket workspace tab. Fresh `WebSocketConnection()` (unique
UUID, name `"New WebSocket"`, empty URL). Inserts before the plus tab,
same as `add_new_tab`. Persist omit and dirty-close:
[websocket_draft_tab.md](websocket_draft_tab.md).

### `TabsPresenter.add_blank_mcp_client_tab(*, save_state: bool = True) -> McpClientTab`

Blank MCP Client **draft** workspace tab. Fresh `McpClientConnection()` +
`McpClientPresenter` + `McpClientTab`. Inserts before the plus tab with
title `"New MCP Client"`. No MCP SDK. Draft chrome, restore omission, and
`close_tab` teardown:
[mcp_client_draft_tab.md](mcp_client_draft_tab.md).

### `McpClientTab`

```python
class McpClientTab(QWidget):
    def __init__(
        self,
        connection: McpClientConnection,
        presenter: McpClientPresenter,
        parent: QWidget | None = None,
    ) -> None: ...
```

Re-exported from `pypost.ui.widgets.mcp_client`. Page widget id:
`MCP_CLIENT_TAB_PAGE` (`pypost_mcp_client_tab_page`).

### Injectable `protocol_picker`

```python
TabsPresenter(
    ...,
    protocol_picker: Callable[..., TabProtocol | None] | None = None,
)
```

Default is `NewTabProtocolPicker().prompt`. Tests pass a lambda and
**never** call live `QMenu.exec()` (it blocks the Qt event loop).

Presenter and plus-click tests inject HTTP:

```python
TabsPresenter(
    ...,
    protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
)
```

Cancel / WebSocket / MCP Client:

```python
protocol_picker=lambda *_a, **_k: None
protocol_picker=lambda *_a, **_k: TabProtocol.WEBSOCKET
protocol_picker=lambda *_a, **_k: TabProtocol.MCP_CLIENT
```

Golden plus-click e2e patches after session ready (constructor is
already live):

```python
session.window.tabs._protocol_picker = (
    lambda *_a, **_k: TabProtocol.HTTP
)
```

Picker unit tests (`tests/test_new_tab_protocol_picker.py`) cover
`build_menu()` chrome and hermetic `prompt()` outcome mapping. They
mock instance `menu.exec` after `build_menu` (via `_install_fake_exec`)
and never call live `QMenu.exec()`.

### `track_gui_new_tab_action(source, protocol="unknown")`

Counter `gui_new_tab_actions_total` with labels `source` and
`protocol`. Prometheus serializes labels alphabetically:

```text
gui_new_tab_actions_total{protocol="http",source="plus_button"}
gui_new_tab_actions_total{protocol="mcp_client",source="shortcut"}
```

| Label | Allowed values |
| --- | --- |
| `source` | `plus_button`, `shortcut`, `last_tab`, `collections_context`, `unknown` |
| `protocol` | `http`, `websocket`, `mcp_client`, `unknown` |

Normalization: any other string becomes `unknown`. Picker confirm
passes `protocol.value` (`http` / `websocket` / `mcp_client`). Without
`mcp_client` on `_NEW_TAB_PROTOCOLS`, that label would collapse to
`unknown`. Collections **New tab** calls
`track_gui_new_tab_action("collections_context")` and keeps the
default `protocol=unknown`. Cancel does not increment.

No payload fields (URL, headers, body) — there is no URL yet. Outbound
MCP Client Connect / Refresh / Invoke counters live on the draft tab
(see [mcp_client_draft_tab.md](mcp_client_draft_tab.md)).

See [Prometheus Monitoring](../prometheus_monitoring.md) for the
operator inventory.

## Configuration

No picker-specific settings or environment variables.

Observability host/port remain global:

- `settings.metrics_host`
- `settings.metrics_port`

Widget ids (`pypost/ui/widget_ids.py`):

- `NEW_TAB_PROTOCOL_MENU` = `pypost_new_tab_protocol_menu`
- `PLUS_TAB_BUTTON` = `pypost_plus_tab_button` (anchor lookup)
- `MCP_CLIENT_TAB_PAGE` = `pypost_mcp_client_tab_page` (draft page)

## Troubleshooting

### Tests hang after `Ctrl+N` or **+**

Live `QMenu.exec()` blocks the Qt event loop. Inject `protocol_picker`
(or patch `_protocol_picker` on a live session). Never call live
`exec()` in CI. Hermetic `prompt()` tests mock instance `menu.exec`
after `build_menu` instead (see `tests/test_new_tab_protocol_picker.py`).

The same hang appears when a unit test closes the **last** workspace tab
without injecting `protocol_picker` on `TabsPresenter` construction
(PYPOST-1159 / PYPOST-1181). Always pass a hermetic picker in
`tests/test_websocket_client_ui_repro.py` and similar modules. See
[websocket_ui_client.md](websocket_ui_client.md) and
[last_tab_protocol_picker.md](last_tab_protocol_picker.md).

### Cancel appears to be a bug (no tab)

Dismissing the menu (Esc or click away) is FR-3: no tab, no metric.
Look for INFO `new_tab_action_cancelled source=...`.

### WebSocket confirm opens an HTTP `RequestTab`

Routing must use `add_blank_websocket_tab()`, not `add_new_tab()` and
not `open_websocket_tab()`. Assert current page is `WebSocketTab`.

### MCP Client confirm opens an HTTP `RequestTab`

Routing must use the explicit `TabProtocol.MCP_CLIENT` branch →
`add_blank_mcp_client_tab()`, **before** the HTTP `add_new_tab()`
fallback. Assert current page is `McpClientTab`, not `RequestTab` or
`WebSocketTab`. Also confirm `prompt()` maps the third action; unmapped
data returns `None` (looks like cancel).

### Two blank WebSocket tabs collapse into one

`open_websocket_tab` dedups by `connection.id`. Blank tabs must use
`add_blank_websocket_tab` (fresh UUID each time). Draft persist and
dirty-close: [websocket_draft_tab.md](websocket_draft_tab.md).

### New-tab metric missing after a picker confirm

Expect both labels. Example scrape text:

```text
gui_new_tab_actions_total{protocol="http",source="shortcut"} 1
gui_new_tab_actions_total{protocol="mcp_client",source="plus_button"} 1
```

Cancel never increments. Collections **New tab** uses
`protocol="unknown"`, not `http`. If MCP Client confirm scrapes as
`protocol="unknown"`, `_NEW_TAB_PROTOCOLS` is missing `mcp_client`.

### Close-last-tab does not show the picker

Should not happen after PYPOST-1159. Empty strip must call
`handle_new_tab("last_tab")` via `close_workspace_tab`. See
[last_tab_protocol_picker.md](last_tab_protocol_picker.md). The MCP
draft **is** counted so an MCP-only strip is not treated as empty.

### MCP Client tab has no URL bar / Connect

Should not happen after PYPOST-1166. Chrome, widget ids, and teardown:
[mcp_client_draft_tab.md](mcp_client_draft_tab.md).

### User docs still omit **MCP Client**

User Guide rewrite is PYPOST-1168. Developer docs in `doc/dev/` are
the source of truth for the three-item picker until that story lands.

## Tests

| Test | Behavior verified |
| --- | --- |
| `tests/test_new_tab_protocol_picker.py` | Three labels, HTTP first + active, third is MCP Client; hermetic `prompt()` maps HTTP (`actions()[0]`), WebSocket (`actions()[1]`), MCP Client (`actions()[2]`), and dismiss → `None` via mocked `menu.exec` (PYPOST-1180); no live `exec()` |
| `TestHandleNewTabProtocolPicker` in `tests/test_tabs_presenter.py` | Picker before editor; HTTP/WS/MCP confirm; MCP ≠ HTTP; cancel; metrics `protocol=mcp_client` |
| Plus-click tests in `tests/test_tabs_presenter.py` | Inject HTTP picker so **+** does not hang |
| `test_track_gui_new_tab_action_records_mcp_client_protocol` | Prometheus + OTel allow-list records `mcp_client`, not `unknown` |
| `test_agent_golden_plus_tab_create_when_no_blank_tab` | Patches `_protocol_picker` before `ui_click(PLUS_TAB_BUTTON)` |

Run:

```bash
make test PYTEST_ARGS="tests/test_new_tab_protocol_picker.py tests/test_tabs_presenter.py tests/test_metrics_manager.py tests/test_metrics_otel.py -k 'HandleNewTabProtocolPicker or plus_tab or new_tab or mcp_client' -v"
```
