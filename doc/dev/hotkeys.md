# Keyboard shortcuts and Hotkeys dialog

## Overview

Application shortcuts are registered on `QAction` instances with metadata properties consumed by
**Help → Hotkeys** (`HotkeysDialog`). Registration helpers live in `pypost/ui/hotkeys.py`.

## Registering a shortcut

```python
from pypost.ui.hotkeys import register_hotkey, tag_action

# New action + shortcuts
register_hotkey(
    self,
    section="Tabs",
    label="New Tab",
    keys=("Ctrl+N",),
    slot=lambda: self.tabs.handle_new_tab("shortcut"),
    order=1,
)

# Existing menu QAction (e.g. Quit)
tag_action(
    quit_action,
    section="General",
    order=1,
    keys=("Ctrl+Q",),
    label="Quit Application",
)
```

`handle_new_tab("shortcut")` shows the blank-tab protocol picker before
creating a tab. See [new_tab_protocol_picker.md](new_tab_protocol_picker.md).
User-facing hotkey copy is
[PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).

### Multiple keys, one handler

Pass all keys in `keys`. The first is set on the `QAction`; alternates use `QShortcut`:

```python
register_hotkey(
    self,
    section="Request Editor",
    label="Focus URL Bar",
    keys=("Ctrl+L", "Alt+D"),
    slot=self.tabs.handle_focus_url,
    order=4,
)
```

### Multiple keys, different handlers (one help row)

Use `register_hotkey_group` when each key needs its own slot but the Help dialog should show a
single row. Every key gets its own `QShortcut`; the `QAction` only carries display metadata.
Pass `collapse_keys=False` unless the keys form a range (default `True` renders
`Alt+1 ... Alt+9`).

"Send Request" binds F5 and Ctrl+Return to different routers
([PYPOST-1285](https://pypost.atlassian.net/browse/PYPOST-1285)):

```python
register_hotkey_group(
    self,
    section="Request Editor",
    label="Send Request",
    bindings=(
        ("F5", self.tabs.handle_f5_global),
        ("Ctrl+Return", self.tabs.handle_ctrl_return_global),
    ),
    order=1,
    collapse_keys=False,
)
```

Alt+1 … Alt+9 tab switch:

```python
register_hotkey_group(
    self,
    section="Tabs",
    label="Switch to Tab 1-9",
    bindings=tuple(
        (f"Alt+{i}", lambda idx=i - 1: self.tabs.handle_switch_to_tab(idx))
        for i in range(1, 10)
    ),
    order=5,
)
```

### Documentation-only rows (display, never bind)

`register_hotkey_documentation` adds a Help row for a key that is **already bound elsewhere**
(for example the WebSocket Session and MCP Client sections, registered in
`main_window_protocol_hotkeys.py`). Rules:

- The row's `QAction` never receives a `QKeySequence`. Every key is stored as platform-native
  text (`QKeySequence.SequenceFormat.NativeText`) in `pypost_hotkey_alt_keys`
  (`ALT_KEYS_PROPERTY`).
- Never build a display-only row with `register_hotkey`, `register_hotkey_group`,
  `tag_action(keys=...)` or `QAction.setShortcut`.

Why: when two enabled `QAction` / `QShortcut` objects in the same window share a key sequence,
Qt treats the shortcut as ambiguous. It emits `activatedAmbiguously` and fires **no** slot.
Before PYPOST-1285 the protocol session rows bound F5, Ctrl+Return and Ctrl+L. Those keys then
silently did nothing on every tab, and nothing was logged.

Guard tests:

- `tests/test_hotkeys.py`: `test_documentation_row_does_not_make_bound_shortcut_ambiguous`,
  `test_documentation_row_displays_native_text`,
  `test_focus_url_ctrl_l_not_ambiguous_with_protocol_doc_rows`
- `tests/test_main_window_hotkeys.py::TestProtocolSessionHelpRows`:
  `test_documentation_rows_bind_no_shortcut`, `test_no_key_listed_twice_within_session_sections`
- `tests/test_main_window_hotkeys.py::TestMainWindowSendKeyWiring` (real `MainWindow`, real
  key events; includes `test_no_documentation_row_binds_a_key`)

These guards cover display-only rows only. A window-wide check that every live key sequence is
bound once is tracked in [PYPOST-1290](https://pypost.atlassian.net/browse/PYPOST-1290).
Showing every Help key as native text is tracked in
[PYPOST-1294](https://pypost.atlassian.net/browse/PYPOST-1294).

## Send key routing (F5 / Ctrl+Return)

F5 and Ctrl+Return are bound once, on `MainWindow` (Help row "Request Editor → Send Request").
They go through `TabsPresenter` to `pypost/ui/presenters/tabs_presenter_hotkeys.py`:

- `handle_f5_global` → `_dispatch("f5", presenter, _F5_ROUTES)`
- `handle_ctrl_return_global` → `_dispatch("ctrl_return", presenter, _CTRL_RETURN_ROUTES)`

The route tables map the active tab kind (`TabProtocol`) to a `(log label, handler)` pair:

| Active tab | F5 (`_F5_ROUTES`) | Ctrl+Return (`_CTRL_RETURN_ROUTES`) |
| --- | --- | --- |
| HTTP | `_send_http_request` (`send_request`) | `_send_http_request` (`send_request`) |
| WebSocket | `handle_websocket_connect_global` (`connect_toggle`) | `handle_websocket_send_message_global` (`send_message`) |
| MCP Client | `handle_mcp_client_connect_global` (`connect_toggle`) | `handle_mcp_client_invoke_global` (`invoke_tool`) |
| none | no-op | no-op |

- Routing depends **only** on `active_tab_kind`. Keyboard focus does not matter (the old
  composer / invoke-form focus checks were removed).
- Each handler returns `True` when it ran and `False` when it returned early (target tab or
  presenter missing). Session guards are unchanged and live in the tab presenters. For example,
  a WebSocket send while not `OPEN` logs `websocket_send_blocked_not_open`.
- After the handler runs, `_dispatch` logs `hotkey_routed` at DEBUG (see
  [logging.md](logging.md)). No tab → `action=noop`. Early return →
  `action=noop reason=target_unavailable`.
- To add a protocol, add an entry to both route tables.
  `TestHotkeyRoutedLogging::test_route_tables_cover_every_tab_kind` fails if a `TabProtocol` is
  missing.

The WebSocket "connect" handler calls the private `_on_connect_clicked`, and the
`*_connect_global` names actually toggle. A public toggle API and a rename are tracked in
[PYPOST-1296](https://pypost.atlassian.net/browse/PYPOST-1296).

### Behavior change (PYPOST-1285)

For release notes:

- F5, Ctrl+Return and Ctrl+L work again. Before, they were ambiguous and did nothing.
- On WebSocket / MCP Client tabs, F5 always toggles Connect / Disconnect. It no longer sends from
  the WS composer or invokes from the MCP invoke form. Ctrl+Return always sends / invokes. It
  never connects or disconnects, wherever focus is.

## QAction metadata properties

| Property | Purpose |
| --- | --- |
| `pypost_hotkey_section` | Section header (General, Tabs, Request Editor) |
| `pypost_hotkey_order` | Sort order within section |
| `pypost_hotkey_alt_keys` | Extra key strings for display / alternate bindings |
| `pypost_hotkey_collapse_keys` | Display as `Alt+1 ... Alt+9` when true |
| `pypost_hotkey_label` | Help text override when menu text differs |

## Hotkeys dialog

`HotkeysDialog(parent)` calls `collect_hotkey_rows(parent)` and renders a read-only table.
The parent must be `MainWindow` (or a widget subtree containing tagged actions).

## Tests

`tests/test_hotkeys.py` covers formatting, collection order, dialog population, and the
documentation-row guards. `tests/test_main_window_hotkeys.py` covers send-key routing per tab
kind, `hotkey_routed` logging and `MainWindow` wiring:

```bash
make test PYTEST_ARGS='tests/test_hotkeys.py tests/test_main_window_hotkeys.py -v'
```

## Out of scope for help dialog

Shortcuts not registered via these helpers (e.g. F2 rename in environment list, Ctrl+F in
response search) do not appear in Help → Hotkeys unless adopted later.
