# PYPOST-43: Architecture — Decompose MainWindow into Presenters

## 1. Overview

`MainWindow` (`ui/main_window.py`, 1041 LOC) is a god-object mixing layout, event handling,
business orchestration, persistence, shortcuts, and MCP/metrics status. This document specifies
how to decompose it into three focused presenter classes, leaving `MainWindow` as a thin
composition root of ≤ 150 LOC.

**Approach:** Plain Python classes holding a root `QWidget`; they do **not** subclass `QMainWindow`
and need no real `QMainWindow` to be instantiated in tests — only a `QApplication` and injected
mocks.

---

## 2. New File Layout

```
pypost/ui/
  main_window.py                    (refactored, ≤ 150 LOC)
  presenters/
    __init__.py                     (re-exports the three classes)
    collections_presenter.py        (CollectionsPresenter)
    tabs_presenter.py               (TabsPresenter + RequestTab + TabBarWithAddButton)
    env_presenter.py                (EnvPresenter)
```

`RequestTab` and `TabBarWithAddButton` move from `main_window.py` into `tabs_presenter.py`
because they are implementation details of `TabsPresenter`.

---

## 3. Presenter Designs

### 3.1 `CollectionsPresenter`

**File:** `pypost/ui/presenters/collections_presenter.py`

#### Responsibility

Owns the collections tree view: loading, rendering, expand/collapse state,
context-menu (rename, delete), and selection-driven tab opening.

#### Constructor Signature

```python
class CollectionsPresenter(QObject):
    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        metrics: MetricsManager,
        icons: dict[str, QIcon],
        parent: QObject | None = None,
    ) -> None:
```

#### Signals (class-level)

```python
open_request_in_tab = Signal(object)   # payload: RequestData
collections_changed  = Signal()        # after create / delete / rename
```

#### Public Properties / Methods

| Name | Type | Description |
|---|---|---|
| `widget` | `QTreeView` | Root widget to embed in `MainWindow` layout |
| `load_collections()` | method | (Re)populates tree model from `request_manager` |
| `restore_tree_state()` | method | Re-expands nodes from `StateManager` state |
| `rename_request_tabs` | **Signal** | Not here — TabsPresenter listens to `collections_changed` and refreshes labels via its own logic |

#### Internal Methods (private)

- `_build_tree_model(collections)` → `QStandardItemModel`
- `_find_collection_item(item_id, item_type)` → `QStandardItem | None`
- `_resolve_collection_item_target(item)` → `tuple[str, Any]`
- `_on_collection_clicked(index)` — opens tab or toggles expand
- `_show_context_menu(pos)` — rename / delete menu
- `_start_rename(index)` — begins delegate edit
- `_on_editor_closed(_editor, hint)` — commits rename
- `_on_tree_expanded(index)` / `_on_tree_collapsed(index)` — persist state
- `_handle_delete(item_id, item_type, label)` — delete + metrics + reload

#### State

```python
_pending_rename: dict | None   # {item_id, item_type, old_name}
```

#### Dependencies Injected

- `RequestManager` — CRUD on collections/requests
- `StateManager` — persist/restore expanded IDs
- `MetricsManager` — track delete/rename metrics
- `icons: dict[str, QIcon]` — HTTP-method and collection icons

---

### 3.2 `TabsPresenter`

**File:** `pypost/ui/presenters/tabs_presenter.py`

#### Responsibility

Owns the `QTabWidget` — opening, closing, restoring, and naming tabs; distributing
environment variables and settings to each `RequestTab`; managing per-tab
`RequestWorker` lifecycle.

Also houses the `RequestTab` and `TabBarWithAddButton` helper classes (moved from
`main_window.py`).

#### Constructor Signature

```python
class TabsPresenter(QObject):
    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        settings: AppSettings,
        parent: QObject | None = None,
    ) -> None:
```

#### Signals (class-level)

```python
variable_set_requested = Signal(object, str)   # (key: str | None, value: str)
env_update_requested   = Signal(object)        # payload: dict  (from RequestWorker)
```

#### Public Properties / Methods

| Name | Signature | Description |
|---|---|---|
| `widget` | `QTabWidget` | Root widget for `MainWindow` layout |
| `add_new_tab` | `(request_data=None, save_state=True)` | Opens a new request tab |
| `close_tab` | `(index: int)` | Closes tab; ensures ≥ 1 tab |
| `restore_tabs` | `()` | Restores tabs from `StateManager` |
| `save_tabs_state` | `()` | Persists open tab IDs |
| `on_env_variables_changed` | `(variables: dict)` | Pushes new env vars to all open tabs |
| `on_env_keys_changed` | `(keys: list[str] \| None)` | Pushes env key list to all `ResponseView` |
| `rename_request_tabs` | `(request_id: str, new_name: str)` | Updates tab labels after rename |
| `apply_settings` | `(settings: AppSettings)` | Updates font/indent in all tabs |
| `handle_new_tab` | `(source="unknown")` | New tab with logging + metrics |
| `handle_close_tab` | `()` | Closes current tab |
| `handle_next_tab` | `()` | Cycle forward |
| `handle_previous_tab` | `()` | Cycle backward |
| `handle_switch_to_tab` | `(index: int)` | Jump to tab by index |
| `handle_send_request_global` | `()` | Sends request on current tab |
| `handle_focus_url` | `()` | Focuses URL bar on current tab |
| `handle_switch_to_params_global` | `()` | Activates Params sub-tab |
| `handle_switch_to_headers_global` | `()` | Activates Headers sub-tab |
| `handle_switch_to_body_global` | `()` | Activates Body sub-tab |
| `handle_switch_to_script_global` | `()` | Activates Script sub-tab |

#### Internal Methods (private)

- `_current_tab()` → `RequestTab | None`
- `_handle_send_request(request_data)` — creates worker, wires signals
- `_on_request_finished(tab, response)` — displays response, stops worker
- `_on_request_error(tab, error_msg)` — shows error, resets UI
- `_on_headers_received(tab, status, headers)` — streaming partial update
- `_on_chunk_received(tab, chunk)` — streaming body append
- `_reset_tab_ui_state(tab)` — re-enables Send button
- `_position_add_tab_button()` — moves "+" button
- `_wire_tab_signals(tab)` — connects tab's internal signals to self

#### Helper Classes (in same module)

```python
class RequestTab(QWidget):
    """Container for a single RequestWidget + ResponseView pair."""
    request_data: RequestData
    request_editor: RequestWidget
    response_view: ResponseView
    worker: RequestWorker | None

class TabBarWithAddButton(QTabBar):
    """Tab bar that emits layout_changed so '+' button can be repositioned."""
    layout_changed = Signal()
```

---

### 3.3 `EnvPresenter`

**File:** `pypost/ui/presenters/env_presenter.py`

#### Responsibility

Owns the environment selector in the top bar: loading environments, propagating
variables to tabs, managing `MCPServerManager` lifecycle, and processing
variable mutations from scripts and context menus.

#### Constructor Signature

```python
class EnvPresenter(QObject):
    def __init__(
        self,
        storage: StorageManager,
        config_manager: ConfigManager,
        mcp_manager: MCPServerManager,
        settings: AppSettings,
        get_collections: Callable[[], list[Collection]],
        parent: QObject | None = None,
    ) -> None:
```

#### Signals (class-level)

```python
env_variables_changed = Signal(object)   # payload: dict[str, str]
env_keys_changed      = Signal(object)   # payload: list[str] | None
```

#### Public Properties / Methods

| Name | Signature | Description |
|---|---|---|
| `widget` | `QWidget` | Top-bar widget containing selector + buttons + MCP label |
| `load_environments` | `()` | Loads from storage, populates combo, emits current vars |
| `on_env_update` | `(vars: dict)` | Merges post-request variable updates into current env |
| `handle_variable_set_request` | `(key: str \| None, value: str)` | Prompts for key, saves to env |
| `handle_open_environments` | `()` | Shortcut handler — opens `EnvironmentDialog` |
| `current_variables` | `dict[str, str]` (property) | Returns currently active env vars |

#### Internal Methods (private)

- `_on_env_changed(index)` — resolves vars, starts/stops MCP, saves config, emits signals
- `_on_mcp_status_changed(is_running)` — updates MCP status label
- `_open_env_manager()` — opens `EnvironmentDialog`, saves, reloads
- `_get_mcp_tools()` — returns `expose_as_mcp` requests from current collections

#### State

```python
_environments: list[Environment]
_current_env_index: int
```

---

## 4. Refactored `MainWindow`

`MainWindow` shrinks to a composition root. It:

1. Instantiates core services.
2. Instantiates the three presenters.
3. Places presenter widgets into the layout.
4. Wires cross-presenter signals.
5. Sets up the menu bar and keyboard shortcuts (dispatching to presenters).
6. Orchestrates `apply_settings()`.

### Skeleton

```python
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyPost")
        self.resize(1200, 800)

        # --- Core services ---
        self.storage       = StorageManager()
        self.config_manager = ConfigManager()
        self.request_manager = RequestManager(self.storage)
        self.state_manager  = StateManager(self.config_manager)
        self.style_manager  = StyleManager()
        self.mcp_manager    = MCPServerManager()
        self.settings       = self.state_manager.settings
        self.icons          = self._load_icons()

        # --- Presenters ---
        self.collections = CollectionsPresenter(
            self.request_manager, self.state_manager,
            MetricsManager(), self.icons,
        )
        self.tabs = TabsPresenter(
            self.request_manager, self.state_manager, self.settings,
        )
        self.env = EnvPresenter(
            self.storage, self.config_manager, self.mcp_manager,
            self.settings, self.request_manager.get_collections,
        )

        # --- Layout ---
        self._build_layout()

        # --- Cross-presenter wiring ---
        self._wire_signals()

        # --- Menu, shortcuts, initial state ---
        self._create_menu_bar()
        self._setup_shortcuts()
        self.apply_settings(self.settings)

    def _build_layout(self) -> None:
        """Places presenter widgets into the QSplitter + top bar."""

    def _wire_signals(self) -> None:
        """Connects signals between presenters."""
        self.collections.open_request_in_tab.connect(self.tabs.add_new_tab)
        self.collections.collections_changed.connect(self.env.load_environments)
        self.env.env_variables_changed.connect(self.tabs.on_env_variables_changed)
        self.env.env_keys_changed.connect(self.tabs.on_env_keys_changed)
        self.tabs.variable_set_requested.connect(self.env.handle_variable_set_request)
        self.tabs.env_update_requested.connect(self.env.on_env_update)

    def apply_settings(self, settings: AppSettings) -> None:
        """Propagates font/indent/timeout to all presenters."""

    def handle_exit(self) -> None:
        """Persists state and quits."""

    def keyPressEvent(self, event) -> None:
        """Delegates Ctrl+Return to TabsPresenter."""
```

**Methods retained in `MainWindow`:**

| Method | Reason |
|---|---|
| `__init__` | Composition root |
| `_load_icons()` | Returns `dict[str, QIcon]` used by `CollectionsPresenter` |
| `_build_layout()` | Places widgets from presenters |
| `_wire_signals()` | Cross-presenter wiring |
| `_create_menu_bar()` | Window-level menu (delegates actions to presenters) |
| `_setup_shortcuts()` | Window-level shortcuts (delegates to presenters) |
| `apply_settings()` | Thin orchestrator across all three presenters |
| `handle_exit()` | Saves state, calls `QApplication.quit()` |
| `keyPressEvent()` | Delegates to `tabs.handle_send_request_global()` |

---

## 5. Cross-Presenter Signal Map

```
Emitter                              Signal                        Receiver
────────────────────────────────────────────────────────────────────────────────
CollectionsPresenter    open_request_in_tab(RequestData)  TabsPresenter.add_new_tab
CollectionsPresenter    collections_changed()             EnvPresenter.load_environments
EnvPresenter            env_variables_changed(dict)       TabsPresenter.on_env_variables_changed
EnvPresenter            env_keys_changed(list|None)       TabsPresenter.on_env_keys_changed
TabsPresenter           variable_set_requested(obj, str)  EnvPresenter.handle_variable_set_request
TabsPresenter           env_update_requested(dict)        EnvPresenter.on_env_update
```

`MainWindow` owns all six `connect()` calls above (in `_wire_signals()`). No presenter holds a
direct reference to another presenter.

---

## 6. Extraction Order (Incremental, Each Step Keeps App Green)

### Step 1 — Extract `CollectionsPresenter`

1. Create `pypost/ui/presenters/__init__.py` and `collections_presenter.py`.
2. Move all tree-related methods and `_pending_rename` from `MainWindow` into
   `CollectionsPresenter`.
3. In `MainWindow.__init__`, replace tree setup with:
   ```python
   self.collections = CollectionsPresenter(...)
   self.splitter.addWidget(self.collections.widget)
   self.collections.open_request_in_tab.connect(self.add_new_tab)
   self.collections.collections_changed.connect(self.load_environments)
   ```
4. Run tests; fix any import errors.

### Step 2 — Extract `TabsPresenter`

1. Create `tabs_presenter.py`; move `RequestTab`, `TabBarWithAddButton`, all tab methods,
   and worker-lifecycle methods.
2. In `MainWindow.__init__`, replace tab setup with:
   ```python
   self.tabs = TabsPresenter(...)
   self.splitter.addWidget(self.tabs.widget)
   self.collections.open_request_in_tab.connect(self.tabs.add_new_tab)
   ```
3. Update shortcut handlers in `MainWindow` to delegate to `self.tabs.*`.
4. Run tests; fix any issues.

### Step 3 — Extract `EnvPresenter`

1. Create `env_presenter.py`; move environment-selector and MCP methods.
2. In `MainWindow.__init__`, replace env top-bar setup with:
   ```python
   self.env = EnvPresenter(...)
   self.top_bar.addWidget(self.env.widget)
   self.env.env_variables_changed.connect(self.tabs.on_env_variables_changed)
   ...
   ```
3. Run tests; fix any issues.

### Step 4 — Slim `MainWindow`

1. Remove now-empty helper stubs.
2. Add `_wire_signals()`, `_build_layout()`, `_load_icons()` as clean private methods.
3. Verify `main_window.py` ≤ 150 LOC.
4. Run all tests.

---

## 7. Testing Strategy

Each presenter is independently testable with `QApplication` + mocks:

```python
class TestCollectionsPresenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.request_manager = FakeRequestManager()
        self.state_manager   = FakeStateManager()
        self.metrics         = FakeMetricsManager()
        self.presenter = CollectionsPresenter(
            self.request_manager, self.state_manager, self.metrics, icons={}
        )

    def test_load_collections_populates_model(self):
        self.request_manager.collections = [make_collection("col-1", "My API")]
        self.presenter.load_collections()
        model = self.presenter.widget.model()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.item(0).text(), "My API")
```

Fake classes mirror the real manager APIs with in-memory state. The pattern follows
`tests/helpers.py` (`FakeStorageManager`).

Test files to create:

| File | Covers |
|---|---|
| `tests/test_collections_presenter.py` | Load, click, rename, delete, expand/collapse |
| `tests/test_tabs_presenter.py` | add_new_tab, close_tab, restore, env propagation, worker lifecycle |
| `tests/test_env_presenter.py` | load_environments, on_env_changed, variable_set, MCP lifecycle |

---

## 8. Constraints & Rules

- **Line length:** Max 100 characters (project rule).
- **Language:** Python 3.11, PySide6.
- **No new external dependencies.**
- **No behaviour change** — all existing features must work identically.
- **Existing tests must pass** after each extraction step.
- `MetricsManager` remains a singleton (R2 is out of scope); inject via `MetricsManager()`
  at construction site in `MainWindow`.
- `template_service` global remains untouched (R3 out of scope).
- `RequestTab` and `TabBarWithAddButton` move to `tabs_presenter.py` — they are not
  independently presented.

---

## 9. Definition of Done Checklist

- [ ] `pypost/ui/presenters/` exists with `__init__.py`, `collections_presenter.py`,
      `tabs_presenter.py`, `env_presenter.py`.
- [ ] `MainWindow` contains no business logic beyond composition and window setup.
- [ ] `main_window.py` is ≤ 150 LOC.
- [ ] All existing unit and integration tests pass.
- [ ] `tests/test_collections_presenter.py`, `tests/test_tabs_presenter.py`,
      `tests/test_env_presenter.py` exist and pass.
- [ ] No new lint errors; line length ≤ 100 characters throughout.
- [ ] Each presenter can be instantiated in a test with mocked dependencies.
