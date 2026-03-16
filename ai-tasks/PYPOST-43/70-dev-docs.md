# PYPOST-43: Developer Documentation

## Overview

This document describes the presenter architecture introduced in PYPOST-43. It is written for
developers who need to understand, extend, or debug the UI layer of PyPost.

---

## Motivation

Before this change, `pypost/ui/main_window.py` was a 1041-line god-object that mixed layout,
event handling, business orchestration, persistence, keyboard shortcuts, and MCP/metrics status.
PYPOST-43 decomposed it into three focused presenter classes. `MainWindow` now acts as a thin
composition root (≤ 183 LOC) that instantiates presenters, places their widgets in the layout,
and wires cross-presenter signals.

---

## File Layout

```
pypost/ui/
  main_window.py                    # Composition root — ≤ 183 LOC
  presenters/
    __init__.py                     # Re-exports all three classes
    collections_presenter.py        # CollectionsPresenter (329 LOC)
    tabs_presenter.py               # TabsPresenter + RequestTab + TabBarWithAddButton (492 LOC)
    env_presenter.py                # EnvPresenter (236 LOC)

tests/
  test_collections_presenter.py     # 13+ unit tests
  test_tabs_presenter.py            # 22+ unit tests
  test_env_presenter.py             # 17+ unit tests
```

---

## Presenter Contracts

### CollectionsPresenter

**File:** `pypost/ui/presenters/collections_presenter.py`

**Responsibility:** Owns the collections tree view — loading, rendering, expand/collapse state,
context menu (rename, delete), and selection-driven tab opening.

**Constructor:**
```python
CollectionsPresenter(
    request_manager: RequestManager,
    state_manager: StateManager,
    metrics: MetricsManager,
    icons: dict[str, QIcon],
    parent: QObject | None = None,
)
```

**Public API:**

| Member | Kind | Description |
|---|---|---|
| `widget` | property → `QTreeView` | Root widget for `MainWindow` layout |
| `load_collections()` | method | Reloads from storage and rebuilds the tree model |
| `restore_tree_state()` | method | Re-expands nodes from `StateManager` |
| `open_request_in_tab` | Signal(object) | Emitted when user clicks a request; payload: `RequestData` |
| `collections_changed` | Signal() | Emitted after rename or delete |
| `request_renamed` | Signal(str, str) | Emitted on successful rename; payload: (request_id, new_name) |

**State:**
- `_pending_rename: dict | None` — tracks the in-progress rename so `_on_editor_closed` knows
  which item to commit.

---

### TabsPresenter

**File:** `pypost/ui/presenters/tabs_presenter.py`

**Responsibility:** Owns the `QTabWidget` — opening, closing, restoring, and naming tabs;
distributing environment variables and settings to each `RequestTab`; managing per-tab
`RequestWorker` lifecycle.

Also houses the `RequestTab` and `TabBarWithAddButton` helper classes.

**Constructor:**
```python
TabsPresenter(
    request_manager: RequestManager,
    state_manager: StateManager,
    settings: AppSettings,
    parent: QObject | None = None,
)
```

**Public API:**

| Member | Kind | Description |
|---|---|---|
| `widget` | property → `QTabWidget` | Root widget for `MainWindow` layout |
| `add_new_tab(request_data, save_state)` | method | Opens a new request tab |
| `close_tab(index)` | method | Closes tab; ensures ≥ 1 tab always exists |
| `restore_tabs()` | method | Restores tabs from `StateManager` on startup |
| `save_tabs_state()` | method | Persists open tab request IDs via `StateManager` |
| `on_env_variables_changed(variables)` | method | Pushes new env vars to all open tabs |
| `on_env_keys_changed(keys)` | method | Pushes env key list to all `ResponseView` widgets |
| `rename_request_tabs(request_id, new_name)` | method | Updates tab labels after a rename |
| `apply_settings(settings)` | method | Updates font/indent in all open tabs |
| `handle_new_tab(source)` | method | Opens tab with logging + metrics |
| `handle_close_tab()` | method | Closes the currently active tab |
| `handle_next_tab()` | method | Cycles to the next tab |
| `handle_previous_tab()` | method | Cycles to the previous tab |
| `handle_switch_to_tab(index)` | method | Jumps to tab by zero-based index |
| `handle_send_request_global()` | method | Triggers send on the active tab |
| `handle_focus_url()` | method | Focuses the URL bar on the active tab |
| `handle_switch_to_params_global()` | method | Activates the Params sub-tab |
| `handle_switch_to_headers_global()` | method | Activates the Headers sub-tab |
| `handle_switch_to_body_global()` | method | Activates the Body sub-tab |
| `handle_switch_to_script_global()` | method | Activates the Script sub-tab |
| `variable_set_requested` | Signal(object, str) | Forwarded from `ResponseView`; (key or None, value) |
| `env_update_requested` | Signal(object) | Forwarded from `RequestWorker`; payload: dict |
| `request_saved` | Signal() | Emitted after a successful save or save-as |

**Helper classes in the same module:**

- `RequestTab(QWidget)` — wraps a `RequestWidget` + `ResponseView` pair. Holds
  `request_data`, `request_editor`, `response_view`, and `worker`.
- `TabBarWithAddButton(QTabBar)` — emits `layout_changed` so the floating `+` button can be
  repositioned after tab layout changes.

---

### EnvPresenter

**File:** `pypost/ui/presenters/env_presenter.py`

**Responsibility:** Owns the top-bar environment selector — loading environments, propagating
variables to tabs, managing `MCPServerManager` lifecycle, and processing variable mutations
from scripts and context menus.

**Constructor:**
```python
EnvPresenter(
    storage: StorageManager,
    config_manager: ConfigManager,
    mcp_manager: MCPServerManager,
    settings: AppSettings,
    get_collections: Callable[[], list[Collection]],
    parent: QObject | None = None,
)
```

**Public API:**

| Member | Kind | Description |
|---|---|---|
| `widget` | property → `QWidget` | Top-bar widget (selector + Manage button + MCP label) |
| `current_variables` | property → `dict` | Returns the active environment's variables |
| `load_environments()` | method | Loads from storage, rebuilds the combo, emits current vars |
| `on_env_update(vars)` | method | Merges post-request script variable updates into current env |
| `handle_variable_set_request(key, value)` | method | Prompts for key if needed, saves to env |
| `handle_open_environments()` | method | Keyboard shortcut handler — opens `EnvironmentDialog` |
| `env_variables_changed` | Signal(object) | Emitted when active env vars change; payload: dict |
| `env_keys_changed` | Signal(object) | Emitted when active env key set changes; payload: list or None |

**Note:** `env_selector`, `manage_btn`, `mcp_status_label`, and `env_label` are also exposed as
properties so `MainWindow.apply_settings` can set fonts on them. This is a known encapsulation
gap (see TD-3 in `60-review.md`).

---

## Cross-Presenter Signal Map

`MainWindow._wire_signals()` owns all six connections between presenters. No presenter holds
a direct reference to another presenter.

```
Emitter                            Signal                        Receiver
────────────────────────────────────────────────────────────────────────────────────────────
CollectionsPresenter  open_request_in_tab(RequestData)   TabsPresenter.add_new_tab
CollectionsPresenter  collections_changed()              EnvPresenter.load_environments
CollectionsPresenter  request_renamed(str, str)          TabsPresenter.rename_request_tabs
EnvPresenter          env_variables_changed(dict)        TabsPresenter.on_env_variables_changed
EnvPresenter          env_keys_changed(list|None)        TabsPresenter.on_env_keys_changed
TabsPresenter         variable_set_requested(obj, str)   EnvPresenter.handle_variable_set_request
TabsPresenter         env_update_requested(dict)         EnvPresenter.on_env_update
TabsPresenter         request_saved()                    CollectionsPresenter.load_collections
TabsPresenter         request_saved()                    CollectionsPresenter.restore_tree_state
```

---

## Startup Sequence

`MainWindow.__init__` runs the following steps in order:

1. Instantiate core services: `StorageManager`, `ConfigManager`, `RequestManager`,
   `StateManager`, `StyleManager`, `MCPServerManager`.
2. Load icons from `pypost/ui/resources/icons/`.
3. Instantiate `CollectionsPresenter`, `TabsPresenter`, `EnvPresenter`.
4. `_build_layout()` — places presenter widgets into the `QSplitter` + top bar.
5. `_wire_signals()` — connects all cross-presenter signals (see table above).
6. `_create_menu_bar()` — adds File and Help menus.
7. `_setup_shortcuts()` — registers all keyboard shortcuts, delegating to presenter methods.
8. `collections.load_collections()` — populates the tree from storage.
9. `env.load_environments()` — populates the env combo and starts MCP if configured.
10. `tabs.restore_tabs()` — restores previously open tabs from `StateManager`.
11. `collections.restore_tree_state()` — re-expands previously expanded tree nodes.
12. `apply_settings(settings)` — applies font and indent to all widgets.

---

## How to Add a New UI Feature

### Feature that belongs to an existing presenter

1. Add the logic inside the relevant presenter class.
2. If `MainWindow` needs to trigger it (via menu or shortcut), add a public method to the
   presenter and wire the action in `_create_menu_bar` or `_setup_shortcuts`.
3. If the feature emits a new cross-presenter signal, declare it at class level, add a
   `connect` call in `MainWindow._wire_signals`, and update this document.

### Feature that requires a new presenter

1. Create `pypost/ui/presenters/<name>_presenter.py`.
2. Export it in `pypost/ui/presenters/__init__.py`.
3. Instantiate in `MainWindow.__init__` with injected dependencies.
4. Add its widget to `_build_layout`.
5. Wire any signals in `_wire_signals`.
6. Add unit tests in `tests/test_<name>_presenter.py`.

---

## Testing Presenters

Each presenter can be unit-tested without a real `QMainWindow`. Only a `QApplication`
instance is required.

```python
import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

class TestCollectionsPresenter(unittest.TestCase):
    def setUp(self):
        from pypost.ui.presenters import CollectionsPresenter
        self.request_manager = MagicMock()
        self.state_manager = MagicMock()
        self.metrics = MagicMock()
        self.request_manager.get_collections.return_value = []
        self.state_manager.get_expanded_collections.return_value = []
        self.presenter = CollectionsPresenter(
            self.request_manager, self.state_manager, self.metrics, icons={}
        )
```

Test files:
- `tests/test_collections_presenter.py`
- `tests/test_tabs_presenter.py`
- `tests/test_env_presenter.py`

---

## Known Limitations and Follow-Up Tickets

| Ref | Description | Severity |
|---|---|---|
| TD-2 | `open_settings` calls `env._on_env_changed` (private method) | HIGH |
| TD-3 | `EnvPresenter` exposes internal widgets via properties | MEDIUM |
| TD-5 | `RequestTab.layout` shadows `QWidget.layout()` | MEDIUM |
| TD-6 | `_handle_send_request` uses `self.sender()` to locate the tab | MEDIUM |
| TD-1 | `main_window.py` is 183 LOC vs 150 target | LOW |
| TD-4 | Unused `Environment` import in `tabs_presenter.py` | LOW |
| TD-7 | `MetricsManager` not injected in `TabsPresenter` | LOW |
| TD-8 | Tab index captured after modal dialog in `_handle_save_request` | LOW |

See `60-review.md` for full descriptions and recommended fixes.

Out-of-scope items deferred to separate tickets:
- R2: Replace `MetricsManager` singleton with injected interface.
- R3: Replace `template_service` global.
- R4: Introduce `HTTPClientInterface` for the worker.
- R5: Unify collection loading via `RequestManager.reload_collections()`.
