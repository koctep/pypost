# PYPOST-43: Decompose MainWindow into Presenters

## Background

From PYPOST-40 audit finding R1 (P1 priority). `MainWindow` (`ui/main_window.py`, 1040 LOC)
is a "god object" with low cohesion: it mixes layout, event handling, business orchestration,
persistence calls, shortcut management, and MCP/metrics status. This violates the Single
Responsibility Principle and makes the class hard to test, extend, and reason about.

The audit recommends decomposing `MainWindow` into focused presenter/controller classes so
that `MainWindow` becomes a thin composition root.

---

## Goals

- Restore SRP: each presenter owns exactly one concern.
- `MainWindow` becomes thin: instantiates presenters and wires them together; contains no
  business logic of its own.
- No visible behaviour change for the end user.
- New structure is unit-testable without a full `QMainWindow`.

---

## User Stories

- As a developer, I want `MainWindow` to be a thin composition root so that I can understand
  each concern in isolation without reading 1040 lines.
- As a developer, I want each presenter to be independently testable so that I can add tests
  without launching the full application.
- As a maintainer, I want future UI features to be added inside a focused presenter so that
  changes do not ripple across unrelated concerns.

---

## Presenters to Extract

### 1. `CollectionsPresenter`

**File:** `pypost/ui/presenters/collections_presenter.py`

**Responsibility:** Owns the collections tree view — loading, rendering, expand/collapse state,
context menu (rename, delete), and selection-driven tab opening.

**Owns these current `MainWindow` responsibilities:**
- `load_collections()` — populates `QStandardItemModel` from storage
- `on_collection_clicked()` — opens request in a tab or toggles expansion
- `show_collection_item_context_menu()` / `confirm_delete()` — context menu logic
- `handle_delete_collection_item()` — delete orchestration + metrics
- `start_collection_item_rename()` / `on_collection_item_editor_closed()` — inline rename
- `_find_collection_item()` — tree model search helper
- `on_tree_expanded()` / `on_tree_collapsed()` / `restore_tree_state()` — expand/collapse state
- Icon loading for collections and HTTP methods
- `_pending_rename` state

**Signals emitted (to MainWindow or TabsPresenter):**
- `open_request_in_tab(request_data: RequestData)`
- `collections_changed()` — after create/delete/rename

**Dependencies injected:**
- `RequestManager`
- `StateManager`
- `MetricsManager` (or injectable metrics service per R2)
- `icons: dict[str, QIcon]`

---

### 2. `TabsPresenter`

**File:** `pypost/ui/presenters/tabs_presenter.py`

**Responsibility:** Owns the `QTabWidget` — opening, closing, restoring, and naming tabs;
distributing environment variables and settings to each `RequestTab`; handling per-tab request
worker lifecycle.

**Owns these current `MainWindow` responsibilities:**
- `add_new_tab()` — creates `RequestTab`, wires signals, sets indent/env
- `close_tab()` — removes tab, ensures at least one tab exists
- `restore_tabs()` — restores tabs from saved state
- `save_tabs_state()` — persists open tab IDs
- `_rename_request_tabs()` — syncs tab label after a rename
- `handle_send_request()` — worker creation and lifecycle
- `on_request_finished()` / `on_request_error()` — response display
- `on_headers_received()` / `on_chunk_received()` — streaming updates
- `_reset_tab_ui_state()` — re-enables send button
- `_position_add_tab_button()` — positions the "+" button
- Tab navigation: `close_tab`, `handle_next_tab`, `handle_previous_tab`, `handle_switch_to_tab`
- `handle_new_tab()` — wraps `add_new_tab` with logging/metrics
- `handle_close_tab()` / `handle_next_tab()` / `handle_previous_tab()` / `handle_switch_to_tab()`
- Global tab actions: `handle_send_request_global`, `handle_focus_url`,
  `handle_switch_to_params_global`, `handle_switch_to_headers_global`,
  `handle_switch_to_body_global`, `handle_switch_to_script_global`

**Signals emitted:**
- `variable_set_requested(key: str | None, value: str)` — forwarded from `ResponseView`
- `env_update_requested(vars: dict)` — forwarded from `RequestWorker`

**Dependencies injected:**
- `StateManager`
- `RequestManager` (to resolve request IDs during restore)
- `settings: AppSettings`

---

### 3. `EnvPresenter`

**File:** `pypost/ui/presenters/env_presenter.py`

**Responsibility:** Owns the environment selector in the top bar — loading, selecting,
propagating variables to tabs, MCP server lifecycle, and environment variable mutation.

**Owns these current `MainWindow` responsibilities:**
- `load_environments()` — populates `env_selector` combo box
- `on_env_changed()` — resolves variables, starts/stops MCP, saves config, propagates to tabs
- `on_mcp_status_changed()` — updates `mcp_status_label`
- `open_env_manager()` — opens `EnvironmentDialog`, saves, reloads
- `handle_open_environments()` — shortcut handler
- `on_env_update()` — applies post-request variable updates from workers
- `handle_variable_set_request()` — prompts for variable name, saves to environment

**Signals emitted:**
- `env_variables_changed(variables: dict)` — consumed by `TabsPresenter` to push to open tabs
- `env_keys_changed(keys: list[str] | None)` — consumed by `TabsPresenter` for response views

**Dependencies injected:**
- `StorageManager`
- `ConfigManager`
- `MCPServerManager`
- `settings: AppSettings`
- `get_collections: Callable[[], list[Collection]]` — to find MCP-exposed requests

---

## MainWindow After Refactoring

`MainWindow.__init__` will:

1. Instantiate core services: `StorageManager`, `ConfigManager`, `RequestManager`,
   `StateManager`, `StyleManager`.
2. Instantiate `CollectionsPresenter`, `TabsPresenter`, `EnvPresenter`.
3. Build the layout by placing each presenter's root widget into the `QSplitter`/`QVBoxLayout`.
4. Wire cross-presenter signals (e.g. `CollectionsPresenter.open_request_in_tab` →
   `TabsPresenter.add_new_tab`, `EnvPresenter.env_variables_changed` →
   `TabsPresenter.on_env_variables_changed`).
5. Set up the menu bar and keyboard shortcuts (delegating actions to presenters).
6. Call `apply_settings()` — which may be delegated to a thin settings helper or kept in
   `MainWindow` since it touches all three presenters.

`MainWindow` retains only:
- Window-level setup (`setWindowTitle`, `resize`, `_create_menu_bar`, `_setup_shortcuts`)
- Composition wiring (presenter instantiation + signal connections)
- `apply_settings()` (orchestrates font/indent across presenters)
- `handle_exit()`
- `keyPressEvent()` (delegates to `TabsPresenter`)

---

## Interfaces / Contracts

Each presenter exposes:
- A `widget` property (or is itself a `QWidget` subclass) returning the root Qt widget to
  embed in `MainWindow`'s layout.
- Public methods called by `MainWindow` wiring (documented in class docstring).
- Signals declared at class level.

No new external dependencies are introduced. Presenters receive all collaborators via
constructor injection.

---

## Non-Functional Requirements

- **No behaviour change:** All existing features — tab management, collection CRUD, environment
  management, MCP, metrics, keyboard shortcuts, settings — must work identically after the
  refactoring.
- **Testability:** Each presenter must be instantiable in a unit test without a real
  `QMainWindow` (using `QApplication` + injected mocks).
- **Line length:** Max 100 characters per line (project rule).
- **Language:** Python 3.11, PySide6.
- **Existing tests must pass:** No regressions.
- **Incremental delivery acceptable:** Presenters can be extracted one at a time as long as
  `MainWindow` remains functional after each step.

---

## Out of Scope

- Replacing `MetricsManager` singleton (R2) — separate ticket.
- Replacing `template_service` global (R3) — separate ticket.
- Introducing `HTTPClientInterface` (R4) — separate ticket.
- Unifying collection loading via `RequestManager.reload_collections()` (R5) — may be done
  as a prerequisite sub-step but is not the primary goal.
- Any new user-facing features.

---

## Definition of Done

- [ ] `CollectionsPresenter`, `TabsPresenter`, `EnvPresenter` exist in
  `pypost/ui/presenters/`.
- [ ] `MainWindow` contains no business logic beyond composition and window setup.
- [ ] All existing unit and integration tests pass.
- [ ] Each presenter can be instantiated in a test with mocked dependencies.
- [ ] `main_window.py` is ≤ 150 LOC.
- [ ] No new lint errors; line length ≤ 100 characters throughout.

---

## Q&A

- **Q:** Should presenters subclass `QWidget`? **A:** Preferred — they own a root widget
  and this keeps Qt ownership clear. Alternatively a plain Python class holding a `QWidget`
  attribute is acceptable if it simplifies testing.
- **Q:** What about `RequestTab` and `TabBarWithAddButton`? **A:** These helper classes
  stay in `main_window.py` or move to a `tabs_presenter.py` module; they are not
  independently presented.
- **Q:** Can steps be done incrementally? **A:** Yes. Extract one presenter at a time,
  keeping `MainWindow` green after each step.
- **Q:** Is `apply_settings` a fourth presenter? **A:** No. It orchestrates across presenters
  so it stays in `MainWindow` as a thin coordinator method.
