# PYPOST-1353: "Built-in" source with read-only marker in the MCP server dialog

## Research

### Current State and Problem
In epic PYPOST-1335 ("Built-in collections source for MCP server creation"), the core runtime,
model configuration, and controller save layers were implemented across PYPOST-1350, PYPOST-1351,
and PYPOST-1352:
1. `pypost/core/builtin_collections.py` provides `BuiltinCollectionView`:
   - `list_entries()` loads and validates curated entries from `builtin-collections.yaml`.
   - Each `BuiltinCollectionEntry` contains `collection_path`, `environment_path`, `name`,
     `collection_id`, and `version`.
   - `entry.selection()` returns the library identity mapping:
     `{"library_id": "pypost-examples", "manifest_id": "pypost-examples", "path": collection_path}`.
2. `pypost/models/settings.py` provides `McpServerConfiguration`:
   - Contains `bundled_library: bool = False`.
   - Validator rule E8 enforces: when `bundled_library` is true, `library_id` must equal
     `"pypost-examples"`, `manifest_id` and `library_collection_path` are required, and
     `collection_id` is ignored / None.
3. `pypost/ui/mcp_server_controller.py` (`upsert_mcp_server`):
   - Implemented in PYPOST-1352: contains a dedicated `if configuration.bundled_library:` branch
     before `if configuration.library_id:`. It checks view membership against curated entries in
     `registry._builtin_view.list_entries()`, resolves via `LibraryRuntimeResolver` with the bundled
     adapter and empty candidate overlay, reconfigures running instances or saves via
     `LibraryMcpSaveTransaction(..., overlay={})` without modifying overlay files.

However, the user interface in `pypost/ui/dialogs/mcp_servers_dialog.py` has not yet integrated the
Built-in source:
- `_McpServerEditor`:
  - `_collection_source` combo only contains `"Workspace collection"` (`"workspace"`) and
    `"Connected library"` (`"library"`).
  - Editing an existing row with `configuration.bundled_library=True` falls into the `"library"`
    branch because `configuration.library_id == "pypost-examples"`, attempting to look up the
    collection in `LibraryMcpSourcePicker` / generic library service, showing preset combos, and
    rendering overlay variable fields.
  - Adding a new Built-in server is impossible through the UI dialog.
  - Omitted library preset and overlay widgets: currently, selecting `"library"` always renders
    presets and overlay variables. Built-in servers must hide these widgets.
  - Environment selection: workspace environments are loaded in `_environment`, but save validation
    in `_accept_if_complete` does not specifically check or enforce the Built-in environment rules
    alongside curated collection selection.
  - `configuration()` method emits `McpServerConfiguration` with `bundled_library=False` unless
    specifically populated.
- `McpServersDialog` (Server overview table):
  - In `_populate_table`, column 4 (Collection) calls `_library_collection_description` for rows
    with `library_id`. For Built-in rows (`configuration.bundled_library=True`), this displays
    `"{library_name} / {collection_name} [{library_id}]"`.
  - It must instead display `f"Built-in / {server_collection_name} (read-only)"` to give immediate
    visual clarity.
- `pypost/ui/presenters/mcp_controls_presenter.py`:
  - `_open_mcp_servers` creates `McpServersDialog` without passing `builtin_view`. The dialog
    should receive `builtin_view` (or default to `BuiltinCollectionView()` / controller view) to
    populate entries without recreating or rebuilding server registries.

### User Story and Interaction Analysis
Per `ai-tasks/PYPOST-1353/10-requirements.md` and `ai-tasks/PYPOST-1336/20-architecture.md`
(interaction scheme items 4 and 6):
1. User opens "Add MCP Server" (or edits a Built-in row).
2. User chooses "Built-in" in the Collection Source combo (`"builtin"`).
3. The editor shows a dedicated `_builtin_collection` picker loaded with curated entries from
   `builtin_view.list_entries()`.
4. Picker items are formatted as `f"{entry.name} (read-only)"` with tooltip:
   `"Shipped with PyPost and updated on application upgrade (read-only)."`
5. Preset and overlay widgets (`_library_profile`, `_library_variables`) are hidden.
6. The user selects a workspace environment. If no environment is selected, `Save` is blocked with
   error message `"Collection and environment are required."`.
7. On Save, `configuration()` emits:
   - `library_id = "pypost-examples"`
   - `manifest_id = "pypost-examples"`
   - `library_collection_path = selected_entry.collection_path`
   - `library_collection_index = None`
   - `bundled_library = True`
   - `collection_id = None`
   - `environment_id = selected_environment_id`
8. In the server table, `configuration.bundled_library` rows render as
   `f"Built-in / {entry_name} (read-only)"`.
9. Existing Workspace collection and Library flows remain intact. Legacy library rows pointing to
   `"pypost-examples"` without `bundled_library` continue to open and display as `"Library"` rows.

## Implementation Plan

### High-Level Plan
1. **`pypost/ui/dialogs/mcp_servers_dialog.py`**:
   - `_McpServerEditor`:
     - Accept optional `builtin_view: BuiltinCollectionView | None = None`. If not provided,
       instantiate `BuiltinCollectionView()` as fallback.
     - Add `"Built-in"` item (`"builtin"`) to `_collection_source` combo.
     - Create `self._builtin_collection = QComboBox()` for selecting curated built-in entries.
     - Populate `_builtin_collection` from `self._builtin_view.list_entries()`:
       - Item text: `f"{entry.name} (read-only)"`.
       - Item data: `entry`.
       - Item tooltip: `"Shipped with PyPost and updated on application upgrade (read-only)."`.
     - Update layout: add `_builtin_collection` row to form layout.
     - Update `_on_collection_source_changed()`:
       - If source is `"builtin"`:
         - Show `_builtin_collection`.
         - Hide `_collection` (workspace picker), `_library`, `_library_collection`,
           `_library_profile`, and `_library_variables`.
         - Hide form layout labels for hidden widgets.
       - If source is `"workspace"`: show `_collection`, hide library and builtin widgets.
       - If source is `"library"`: show library widgets, hide `_collection` and builtin widgets.
     - Update constructor configuration initialization for editing:
       - If `configuration.bundled_library`:
         - Select `"builtin"` in `_collection_source`.
         - Preselect matching entry in `_builtin_collection` where
           `entry.collection_path == configuration.library_collection_path`.
         - Select `configuration.environment_id` in `_environment`.
       - Else if `configuration.library_id`:
         - Select `"library"` in `_collection_source` (handles legacy rows with
           `library_id == "pypost-examples"` and `bundled_library=False`).
       - Else:
         - Select `"workspace"` in `_collection_source`.
     - Update `_accept_if_complete()`:
       - When source is `"builtin"`, verify `_builtin_collection.currentData()` is not None and
         `_environment.currentData()` is not None. If either is missing, show
         `"Collection and environment are required."` and reject.
     - Update `configuration()`:
       - When source is `"builtin"`:
         - Obtain selected `BuiltinCollectionEntry`.
         - Construct `McpServerConfiguration` with:
           - `id = self._id`
           - `name = self._name.text().strip() or None`
           - `host = self._host.text().strip()`
           - `port = self._port.value()`
           - `server_type = "local"`
           - `library_id = "pypost-examples"`
           - `manifest_id = "pypost-examples"`
           - `library_collection_path = entry.collection_path`
           - `library_collection_index = None`
           - `bundled_library = True`
           - `collection_id = None`
           - `environment_id = str(self._environment.currentData())`
           - `enabled = self._enabled`
     - Update `library_selection()`:
       - Returns None when source is `"builtin"` so generic library save hooks are not invoked
         with uninitialized library picker data.
   - `McpServersDialog`:
     - Accept optional `builtin_view: BuiltinCollectionView | None = None`. Pass it down to
       `_McpServerEditor` in `_add()` and `_edit()`.
     - Update table row rendering in `_populate_table()`:
       - If `configuration.bundled_library`:
         - Resolve entry name using `self._builtin_view` entries matching
           `configuration.library_collection_path`, falling back to
           `configuration.name` or `configuration.library_collection_path`.
         - Format target description: `f"Built-in / {display_name} (read-only)"`.
       - Else if `configuration.library_id`:
         - Render via `_library_collection_description(configuration)`.
       - Else:
         - Render workspace collection name.
2. **`pypost/ui/presenters/mcp_controls_presenter.py`**:
   - In `_open_mcp_servers()`: pass `builtin_view` from `controller.registry._builtin_view` (or
     construct/pass default `BuiltinCollectionView()`) to `McpServersDialog`.
3. **Automated Repro Test Suite (`tests/test_mcp_builtin_dialog.py`)**:
   - Implement comprehensive headless GUI tests covering AC 1–6 with explicit timeouts and bounded
     waits per `do-testing`.

### Mandatory — Failing Repro Design (Step 3)
In Step 3, write automated failing GUI tests in `tests/test_mcp_builtin_dialog.py` asserting all
requirements prior to editing production code.

- **Test Suite Path**: `tests/test_mcp_builtin_dialog.py`
- **Pytest Marker**: `@pytest.mark.usefixtures("qapp")`, `@pytest.mark.timeout(30)`
- **Failing Repro Assertions**:
  1. `test_editor_creates_builtin_server_configuration`:
     - Instantiate `_McpServerEditor` with valid collections, environments, and `builtin_view`.
     - Verify `"Built-in"` is present in `_collection_source`.
     - Select `"Built-in"` in `_collection_source`.
     - Verify `_builtin_collection` is visible, while `_collection`, `_library`,
       `_library_profile`, and `_library_variables` are hidden.
     - Select a curated entry (e.g. Jira Cloud MCP) and an environment.
     - Call `_accept_if_complete()` and `configuration()`.
     - Assert configuration has `bundled_library=True`, `library_id="pypost-examples"`,
       `manifest_id="pypost-examples"`, `library_collection_path="collections/jira_mcp.json"`,
       `collection_id=None`, and matching `environment_id`.
  2. `test_editor_blocks_save_when_environment_missing`:
     - Select `"Built-in"` source.
     - Set environment combo to index `-1` (no selection).
     - Call `_accept_if_complete()`.
     - Assert dialog is not accepted, error text says `"Collection and environment are required."`.
  3. `test_editor_renders_readonly_marker_and_tooltips_in_picker`:
     - Inspect `_builtin_collection` items.
     - Assert all items contain `" (read-only)"` suffix in their text.
     - Assert item tooltips explain the collection is shipped with PyPost and updated on upgrade.
  4. `test_editor_opens_existing_builtin_server_for_editing`:
     - Provide existing `McpServerConfiguration` with `bundled_library=True`,
       `library_id="pypost-examples"`, `library_collection_path="collections/jira_mcp.json"`,
       and `environment_id="env-1"`.
     - Verify `_collection_source` selects `"Built-in"`.
     - Verify `_builtin_collection` preselects the Jira entry.
     - Verify `_environment` preselects `"env-1"`.
  5. `test_editor_opens_legacy_examples_library_server_as_library`:
     - Provide `McpServerConfiguration` with `bundled_library=False`,
       `library_id="pypost-examples"`, and `library_collection_path="collections/jira_mcp.json"`.
     - Verify `_collection_source` selects `"Connected library"` (`"library"`), preserving E8
       backward compatibility.
  6. `test_dialog_overview_table_renders_builtin_readonly_marker`:
     - Instantiate `McpServersDialog` with configurations including a `bundled_library=True` row,
       an ordinary library row, and a workspace row.
     - Assert column 4 of the Built-in row equals `"Built-in / Jira Cloud MCP (read-only)"`.
     - Assert ordinary library and workspace rows render their existing descriptors unchanged.

Sequencing:
- Step 3: Implement `tests/test_mcp_builtin_dialog.py` asserting these cases. Run `make test` to
  confirm red failures.
- Step 4: Implement dialog and presenter changes until all tests pass green.

## Architecture

### Module Structure and Component Diagram

```mermaid
flowchart TD
    subgraph UI Presenter ["pypost/ui/presenters/mcp_controls_presenter.py"]
        PRES["McpControlsPresenter._open_mcp_servers"]
    end

    subgraph UI Dialogs ["pypost/ui/dialogs/mcp_servers_dialog.py"]
        DLG["McpServersDialog"]
        TABLE["_table (Overview Table)"]
        EDITOR["_McpServerEditor"]
        SRC_COMBO["_collection_source<br/>(workspace | library | builtin)"]
        BUILTIN_COMBO["_builtin_collection<br/>(name (read-only))"]
        ENV_COMBO["_environment"]
    end

    subgraph Core Services ["pypost/core/builtin_collections.py"]
        VIEW["BuiltinCollectionView<br/>list_entries()"]
        ENTRY["BuiltinCollectionEntry"]
    end

    subgraph Models ["pypost/models/settings.py"]
        CFG["McpServerConfiguration<br/>bundled_library=True"]
    end

    PRES -->|supplies builtin_view| DLG
    DLG --> TABLE
    DLG -->|opens with builtin_view| EDITOR
    VIEW -->|list_entries()| BUILTIN_COMBO
    SRC_COMBO -->|toggle visible widgets| BUILTIN_COMBO
    EDITOR -->|configuration()| CFG
    TABLE -->|renders 'Built-in / name (read-only)'| CFG
```

### Module Responsibilities and Changes

1. `pypost/ui/dialogs/mcp_servers_dialog.py`:
   - `_McpServerEditor`:
     - Adds `"Built-in"` source option.
     - Manages `_builtin_collection` combo populated via `BuiltinCollectionView.list_entries()`.
     - Formats items with `(read-only)` suffix and informational tooltips.
     - Manages widget visibility (hides library preset and overlay widgets when `"builtin"` is
       active).
     - Validates environment selection before saving.
     - Emits `McpServerConfiguration` with `bundled_library=True` and
       `library_id="pypost-examples"`.
     - Preselects `"Built-in"` for existing bundled rows while preserving `"library"` for legacy
       rows without `bundled_library`.
   - `McpServersDialog`:
     - Holds `_builtin_view` reference.
     - Formats table collection column as `"Built-in / <name> (read-only)"` for bundled rows.
     - Passes `_builtin_view` down to editor instances.
2. `pypost/ui/presenters/mcp_controls_presenter.py`:
   - Supplies `builtin_view` to `McpServersDialog` from the registry or as a default instance.
3. `tests/test_mcp_builtin_dialog.py`:
   - Headless automated unit/GUI test suite validating discovery, selection, validation, table
     rendering, and backward compatibility.

### Selected Architectural Patterns and Justification

- **Model-View-Presenter (MVP) Integration**: The presenter coordinates dialog invocation and
  injects read-only views without coupling the dialog directly to the controller's runtime registry
  internals.
- **Tagged Source State Machine in Editor**: `_collection_source` switches form field visibility
  cleanly between workspace, library, and built-in modes. This ensures mutually exclusive options
  and avoids invalid configurations leaking across sources.
- **Fail-Fast GUI Validation**: Saving a Built-in server without an environment is rejected directly
  in the dialog with clear inline feedback before reaching backend transactions.

## Q&A

- **Q: Why format picker and table items with "(read-only)"?**
  A: Shipped examples cannot be edited in place. Adding "(read-only)" immediately alerts the user
  that these collections are read-only application resources maintained by PyPost updates.
- **Q: Why hide library presets and overlay fields for Built-in servers?**
  A: Built-in servers resolve exclusively from the selected workspace environment and shipped
  manifest declarations. They do not support custom library presets or overlay files, so showing
  those controls would mislead users into attempting unsupported configuration.
- **Q: How does the editor distinguish between a Built-in server and a legacy library server
  pointing to "pypost-examples"?**
  A: The editor checks `configuration.bundled_library`. If true, it activates `"Built-in"`. If false
  (even with `library_id == "pypost-examples"`), it activates `"Connected library"`. This ensures
  100% backward compatibility for existing library rows (E8 guard).
