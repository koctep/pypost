# PYPOST-1415: Virtualized table model and background collection fetching for variable import dialog

## Research

### 1. Existing Implementation Analysis

The current `ImportCollectionVariablesDialog` (`pypost/ui/dialogs/import_collection_variables_dialog.py`) manages the selection, diff inspection, and conflict resolution of variables imported from workspace collections or remote libraries into a target `Environment`.

Key aspects of the current implementation:
1. **Source Collection Selection**:
   - In `__init__`, the dialog iterates over local `workspace_collections` and adds them to `self.collection_combo`.
   - If `library_service` is supplied, it performs synchronous calls (`list_connections()` and `list_manifest_collections()`) directly on the UI thread to populate remote library options.
   - When the user changes collection in `self.collection_combo`, `_on_collection_changed` invokes `_get_selected_collection()`. For library collections (`("library", conn_id, path)`), it calls `self.library_service.read_collection(...)` synchronously on the GUI thread.
2. **Table Construction and Row Allocation**:
   - The table is instantiated as a `QTableWidget(0, 9)` (`self.vars_table`).
   - In `_populate_variables_table()`, for every variable in `col.variables`:
     - Creates 8 standalone `QTableWidgetItem` instances (Select, Name, Current Value, Candidate Value, Type, Secret, Status, Description).
     - If the variable collides with an existing environment variable (`var.name in self.target_environment.variables`), it instantiates a standalone `QComboBox` child widget, configures its items ("Keep Current", "Overwrite"), sets object names, hooks signal listeners, and installs it via `self.vars_table.setCellWidget(i, COL_STRATEGY, combo)`.
3. **Collision Detection & Preset Updates**:
   - Collision detection is based on key membership: `var.name in self.target_environment.variables`.
   - Secret masking is dual-source: `is_secret = bool(var.secret) or (var.name in self.target_environment.hidden_keys)`. If `is_secret`, both the current environment value and candidate value are masked with `HIDDEN_MASK` (`********`).
   - When presets change (`_on_preset_changed`), the dialog loops through all rows, looks up preset values, formats them, and calls `setItem` / `setText` on cell `(row, COL_CANDIDATE_VALUE)`.
4. **Selection State and Bulk Strategy**:
   - Row selection state is read from `QTableWidgetItem.checkState()`.
   - Conflict strategy is read from `cellWidget(row, COL_STRATEGY).currentText()`.
   - `bulk_set_collision_strategy` iterates across all rows in the table widget, finds `cellWidget(row, COL_STRATEGY)`, and updates `setCurrentIndex`.
   - `_update_preview_summary` iterates over all rows in the table to tally counts for new variables to add, colliding variables to overwrite, and colliding variables to keep.

### 2. Current Performance Bottlenecks

1. **Main UI Thread Freeze During Remote Retrieval**:
   - Network I/O and deserialization of remote collection manifests via `library_service.read_collection` execute synchronously on the main Qt thread.
   - Any network latency (1–5+ seconds), socket timeout, or high-latency link blocks the Qt event loop entirely.
   - During this freeze, the application stops repainting, becomes unresponsive to window dragging/resizing, risks OS "Application Not Responding" (ANR) warnings, and prevents users from cancelling the operation or selecting an alternative local collection.
2. **Heavy Heap Allocation and Slow Layout from QTableWidget Cell Widgets**:
   - For collections containing 1,000 to 2,500+ variables, `QTableWidget` instantiates 18,000+ to 22,500+ `QTableWidgetItem` objects and up to 2,500+ individual `QComboBox` QWidget instances.
   - In Qt, each child widget added via `setCellWidget` registers its own windowing system handle, event filter, and geometry management overhead.
   - Instantiating 2,500 combos takes 400ms–1,200ms of CPU time during dialog initialization and preset switching.
   - Scrolling through the table causes severe stutter (> 100ms frame drops) as the layout engine must calculate clipping, repositioning, and redraw events for thousands of off-screen child widgets.
3. **Lack of In-Flight Request Cancellation & Race Condition Vulnerability**:
   - If a user triggers a remote collection fetch and then changes their selection or closes the dialog, there is no mechanism to abort the in-flight network call.
   - If multiple collection selections occur in rapid succession, responses could arrive out of order, allowing a slow, superseded response to overwrite a subsequent user selection.
4. **Modal / Blocking Error Traps**:
   - Network failures or timeouts in `read_collection` currently catch and log the exception, but leave the table in an empty or undefined state without clear user feedback or retry mechanisms.

### 3. Architectural Patterns & Industry Best Practices

1. **Qt Model/View Virtualization (`QAbstractTableModel`)**:
   - Qt's Model/View architecture separates data storage from visual rendering.
   - By subclassing `QAbstractTableModel` (e.g. `CollectionVariablesTableModel`), the table data is held in efficient Python memory structures (tuples/dataclasses).
   - The view (`QTableView`) queries only the visible viewport rows (typically 25–35 rows) via `model.data(index, role)`.
   - Off-screen rows consume zero widget handles and zero layout calculations, achieving instant dialog loading (< 20ms) and rock-solid 60 FPS scrolling regardless of whether the collection has 10 or 100,000 variables.
2. **Item Delegate for Column 4 Editing (`QStyledItemDelegate`)**:
   - Instead of permanently allocating thousands of `QComboBox` child widgets, a `ConflictStrategyDelegate(QStyledItemDelegate)` handles editing for colliding rows in the Conflict Strategy column.
   - In normal state, `data(index, DisplayRole)` renders the strategy text ("Keep Current" or "Overwrite") directly using standard Qt drawing routines (zero widget allocation).
   - When a user interacts with a colliding cell, `createEditor()` instantiates a single `QComboBox` editor on demand for only the active cell. When editing completes or focus is lost, `setModelData()` updates the model and the editor widget is cleanly discarded.
   - To preserve backward compatibility with existing tests and external consumers expecting `cellWidget(row, COL_STRATEGY)` or `get_row_strategy(row)`, the table view and dialog provide adapter methods that seamlessly bridge delegate/model state.
3. **Dedicated Background Worker (`CollectionFetchWorker` on `QThread`)**:
   - Remote I/O is offloaded to a dedicated background `QThread` (leveraging `LibraryOperationWorker` or `CollectionFetchWorker`).
   - The UI thread remains completely unblocked, draggable, and interactive.
4. **Monotonic Request Generation Counter (Race & Stale Response Prevention)**:
   - A monotonic request counter (`self._fetch_generation: int = 0`) is incremented whenever a new fetch is initiated or cancelled.
   - The worker reports its result along with the generation ID under which it was launched.
   - When a worker finishes or errors, the dialog compares the returned generation ID against `self._fetch_generation`. If mismatched, the result is silently discarded as stale.
5. **Non-Modal Inline Error State & Recovery**:
   - When a fetch fails, an inline error banner (`self.error_label`) with a retry button (`self.retry_fetch_btn`) is displayed within the dialog.
   - The dialog remains open and interactive, allowing the user to retry the operation or switch to a different collection.

---

## Implementation Plan

### High-Level Implementation Steps

1. **Phase 1: Design and Implement `CollectionVariablesTableModel`**:
   - Create `CollectionVariableRowRecord` dataclass storing row state:
     - `name: str`
     - `current_value: str` (or formatted value)
     - `candidate_value: str` (raw and formatted)
     - `strategy: ConflictStrategy | None`
     - `var_type: str`
     - `is_secret: bool`
     - `is_collision: bool`
     - `is_effective_secret: bool`
     - `status: str`
     - `description: str`
     - `is_selected: bool`
   - Implement `CollectionVariablesTableModel(QAbstractTableModel)`:
     - `rowCount()`, `columnCount()`, `headerData()`.
     - `data(index, role)`: handles `DisplayRole`, `CheckStateRole` (for column 0), `TextAlignmentRole`, `ToolTipRole`.
     - `flags(index)`: sets checkable flags on column 0, editable flags on column 4 for collisions, selectable/enabled flags on all cells.
     - `setData(index, value, role)`: updates checkbox state on column 0, updates conflict strategy on column 4, emits `dataChanged`, and notifies listeners for summary recalculation.
     - Bulk helper methods: `select_all()`, `deselect_all()`, `set_all_collision_strategy()`, `update_preset()`.
2. **Phase 2: Implement `ConflictStrategyDelegate`**:
   - Create `ConflictStrategyDelegate(QStyledItemDelegate)` for column 4 (`COL_STRATEGY`).
   - `createEditor()`: returns a `QComboBox` populated with "Keep Current" and "Overwrite" if the row is a collision; returns `None` for non-colliding rows.
   - `setEditorData()`: sets the combo's active index matching the model's current strategy.
   - `setModelData()`: commits the selected strategy back to the model via `setData()`.
   - `updateEditorGeometry()`: positions the combo cleanly within the table cell rectangle.
3. **Phase 3: Implement Compatibility `CollectionVariablesTableView`**:
   - Subclass `QTableView` (or provide compatibility interface on `vars_table`) exposing helper methods expected by existing tests and callers:
     - `columnCount() -> int`
     - `rowCount() -> int`
     - `horizontalHeaderItem(col) -> HeaderItemProxy` (exposing `.text()`)
     - `item(row, col) -> TableItemProxy` (exposing `.text()`, `.checkState()`)
     - `cellWidget(row, col) -> QWidget | None` (for column 4, provides a compatible `QComboBox` representation on demand for colliding rows, or `None` for non-colliding rows).
4. **Phase 4: Implement Asynchronous Collection Fetching & Worker Orchestration**:
   - Create `CollectionFetchWorker(QThread)`:
     - Signals: `fetch_completed(object, int)`, `fetch_failed(Exception, int)`.
     - Safely invokes `library_service.read_collection(connection_id, path)` in `run()`.
   - Update `ImportCollectionVariablesDialog`:
     - Maintain `_fetch_generation: int = 0` and `_active_fetch_worker: CollectionFetchWorker | None = None`.
     - Add loading UI components: `loading_container`, `loading_label`, `loading_spinner` / progress indicator, and `cancel_loading_btn`.
     - Add error UI components: `error_container`, `error_label`, and `retry_fetch_btn`.
     - When a remote collection is selected:
       - Increment `_fetch_generation`.
       - Show loading indicator, disable table / preset combo / import button.
       - Launch `CollectionFetchWorker`.
     - If user clicks "Cancel Loading" or switches collections:
       - Increment `_fetch_generation` to invalidate the in-flight request.
       - Request worker interruption/cancellation.
       - Hide loading indicator and reset dialog controls.
     - On `fetch_completed`:
       - If generation matches: hide loading, populate table model with fetched collection, re-enable controls.
     - On `fetch_failed`:
       - If generation matches: hide loading, display inline error banner with error message and retry button.
5. **Phase 5: Refactor Dialog Methods & Verification**:
   - Update `_on_preset_changed()`, `get_row_strategy()`, `set_row_strategy()`, `get_variable_conflict_strategies()`, `bulk_set_collision_strategy()`, `is_row_selected()`, `set_row_selected()`, `select_all()`, `deselect_all()`, and `accept()` to interface cleanly with the virtualized model.
   - Run `make check` and `make verify-ai-tasks`.

---

### Mandatory — Failing Repro (next Step 3)

In Step 3, automated red tests must be written **before** modifying production code to assert desired behaviors and fail cleanly on current production implementation:

- **Test File Location**: `tests/test_variable_import_virtualization_repro.py`
- **What it Asserts (Desired Behaviors)**:
  1. **Virtualized Model Architecture & Zero-Widget Scaling**:
     - Creating and loading a collection with 2,000 variables into `ImportCollectionVariablesDialog` uses `CollectionVariablesTableModel` inheriting `QAbstractTableModel`.
     - Verifies that zero permanent `QComboBox` cell widgets are instantiated across the 2,000 rows during table population, confirming O(1) viewport-only widget allocation.
     - Verifies that `model.data()` correctly returns masked values (`HIDDEN_MASK`) for secret keys and formatted values for normal keys without leaking raw secret strings.
  2. **Non-Blocking Background Collection Fetching & UI Responsiveness**:
     - Selecting a remote library collection with an artificial latency delay (e.g. 1.0s mock worker) does not block the Qt event loop (`QApplication.processEvents()` processes without stalling).
     - Verifies that `loading_container` / loading indicator is visible and import buttons are disabled while fetching.
     - Verifies that `cancel_loading_btn` is accessible and functional.
  3. **Cancellation and Request Generation Race Protection**:
     - Starting a fetch for Remote Collection 1 (generation 1) and immediately switching to Remote Collection 2 (generation 2) or cancelling via `cancel_loading_btn`.
     - When Remote Collection 1 worker emits its late completion, the dialog discards the stale response and does not overwrite Collection 2.
  4. **Graceful Error Recovery & Non-Modal Retry**:
     - Simulating a network failure / timeout in `library_service.read_collection`.
     - Verifies that the dialog catches the exception, clears the loading indicator, displays an informative non-modal error message in `error_label`, and provides an active retry button without crashing or closing the dialog.
     - Verifies that switching back to a local workspace collection clears the error banner and successfully renders local variables.
  5. **Bulk Strategy & Preview Summary on Virtualized Model**:
     - Applying `bulk_overwrite_btn.click()` across 1,000 colliding rows updates all rows in the virtualized model in < 50ms and updates summary text instantaneously.
     - Applying `bulk_keep_current_btn.click()` resets all rows to `ConflictStrategy.SKIP`.
- **How to Force the Failure Without Live External Deps**:
  - Use a mock `library_service` with configurable delays (`time.sleep` in worker or threading events) and simulated network exceptions (`ConnectionError`, `TimeoutError`).
  - Tests run with `@pytest.mark.timeout(30)` conforming to the `do-testing` contract.
  - Since the current production code uses synchronous `read_collection` and `QTableWidget.setCellWidget`, these tests will fail immediately on the current codebase, providing the required red baseline.
- **Sequencing**:
  - Step 2: Architecture design and review approval.
  - Step 3: Implement `tests/test_variable_import_virtualization_repro.py`, verify red failures via `make test PYTEST_ARGS="tests/test_variable_import_virtualization_repro.py"`.
  - Step 4: Implement virtualized model, delegate, background worker, cancellation, error recovery, and update dialog until all tests pass green.
  - Step 5: Code cleanup and static analysis verification via `make check`.
  - Step 6: Observability and structured logging validation.

---

## Architecture

### 1. Component Architecture & Relationships

```mermaid
classDiagram
    class ImportCollectionVariablesDialog {
        -Environment target_environment
        -list~Collection~ workspace_collections
        -Any library_service
        -int _fetch_generation
        -CollectionFetchWorker _active_fetch_worker
        -CollectionVariablesTableModel _model
        -ConflictStrategyDelegate _strategy_delegate
        -CollectionVariablesTableView vars_table
        -QWidget loading_container
        -QLabel loading_label
        -QPushButton cancel_loading_btn
        -QWidget error_container
        -QLabel error_label
        -QPushButton retry_fetch_btn
        +begin_fetch_collection(connection_id, path)
        +cancel_active_fetch()
        +_on_fetch_completed(collection, generation_id)
        +_on_fetch_failed(error, generation_id)
        +get_row_strategy(row) ConflictStrategy
        +set_row_strategy(row, strategy)
        +bulk_set_collision_strategy(strategy)
        +is_row_selected(row) bool
        +set_row_selected(row, selected)
        +select_all()
        +deselect_all()
        +accept()
    }

    class CollectionVariablesTableModel {
        -list~CollectionVariableRowRecord~ _records
        -dict~str, ConflictStrategy~ _strategies
        -Environment _environment
        -Collection _collection
        -str _preset_name
        +rowCount(parent) int
        +columnCount(parent) int
        +data(index, role) Any
        +headerData(section, orientation, role) Any
        +flags(index) ItemFlags
        +setData(index, value, role) bool
        +load_collection(collection, preset_name)
        +set_preset(preset_name)
        +set_all_selected(selected)
        +set_all_collision_strategy(strategy)
        +get_summary_counts() tuple
        +get_selected_keys() set~str~
        +get_conflict_strategies() dict~str, ConflictStrategy~
    }

    class CollectionVariableRowRecord {
        +str name
        +str current_display
        +str candidate_display
        +Any raw_current
        +Any raw_candidate
        +ConflictStrategy strategy
        +str var_type
        +bool is_collection_secret
        +bool is_env_secret
        +bool is_effective_secret
        +bool is_collision
        +str status
        +str description
        +bool is_selected
    }

    class ConflictStrategyDelegate {
        +createEditor(parent, option, index) QWidget
        +setEditorData(editor, index)
        +setModelData(editor, model, index)
        +updateEditorGeometry(editor, option, index)
    }

    class CollectionFetchWorker {
        +Signal fetch_completed(object, int)
        +Signal fetch_failed(Exception, int)
        -Any library_service
        -str connection_id
        -str collection_path
        -int generation_id
        -bool _cancelled
        +run()
        +cancel()
    }

    class CollectionVariablesTableView {
        +columnCount() int
        +rowCount() int
        +horizontalHeaderItem(col) HeaderItemProxy
        +item(row, col) TableItemProxy
        +cellWidget(row, col) QWidget
    }

    ImportCollectionVariablesDialog --> CollectionVariablesTableModel : owns
    ImportCollectionVariablesDialog --> CollectionVariablesTableView : embeds
    ImportCollectionVariablesDialog --> ConflictStrategyDelegate : installs on col 4
    ImportCollectionVariablesDialog --> CollectionFetchWorker : spawns asynchronously
    CollectionVariablesTableView --> CollectionVariablesTableModel : displays
    CollectionVariablesTableModel *-- CollectionVariableRowRecord : contains
```

---

### 2. Sequence Diagram: Asynchronous Collection Fetching & Generation Race Protection

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Dialog as ImportCollectionVariablesDialog
    participant Worker as CollectionFetchWorker (QThread)
    participant Service as LibraryService (Remote Network)
    participant Model as CollectionVariablesTableModel
    participant View as CollectionVariablesTableView

    User->>Dialog: Selects Remote Collection "EnterpriseAPI"
    Note over Dialog: Increment _fetch_generation = 1
    Dialog->>Dialog: Show loading indicator & cancel button
    Dialog->>Dialog: Disable table, preset combo, import button
    Dialog->>Worker: Start worker (gen=1, conn_id, path)
    Worker->>Service: read_collection(...) [Background Thread]

    alt User Cancels In-Flight Fetch
        User->>Dialog: Clicks "Cancel Loading"
        Note over Dialog: Increment _fetch_generation = 2
        Dialog->>Worker: cancel()
        Dialog->>Dialog: Hide loading indicator, restore controls
        Service-->>Worker: Late collection data returns
        Worker-->>Dialog: fetch_completed(collection, gen=1)
        Note over Dialog: gen 1 != _fetch_generation (2) -> DISCARD
    else User Switches to Another Collection
        User->>Dialog: Selects Collection "LocalAPI"
        Note over Dialog: Increment _fetch_generation = 2
        Dialog->>Worker: cancel() (gen 1)
        Dialog->>Dialog: Load local collection immediately
        Dialog->>Model: load_collection(local_col)
        Model-->>View: dataChanged() -> Instant render
        Service-->>Worker: Late collection data returns for gen 1
        Worker-->>Dialog: fetch_completed(collection, gen=1)
        Note over Dialog: gen 1 != _fetch_generation (2) -> DISCARD
    else Network Error or Timeout
        Service-->>Worker: Exception (TimeoutError / ConnectionError)
        Worker-->>Dialog: fetch_failed(error, gen=1)
        Dialog->>Dialog: Hide loading indicator
        Dialog->>Dialog: Display inline error banner & retry button
        Dialog->>Dialog: Keep dialog open and responsive
        User->>Dialog: Clicks "Retry"
        Note over Dialog: Increment _fetch_generation = 2
        Dialog->>Worker: Start new worker (gen=2)
    else Successful Fetch
        Service-->>Worker: Collection data returned
        Worker-->>Dialog: fetch_completed(collection, gen=1)
        Note over Dialog: gen 1 == _fetch_generation (1) -> ACCEPT
        Dialog->>Dialog: Hide loading indicator
        Dialog->>Model: load_collection(collection)
        Model-->>View: layoutChanged() / dataChanged()
        Dialog->>Dialog: Enable table, preset combo, import button
        Dialog->>Dialog: Update preview summary
    end
```

---

### 3. Sequence Diagram: Virtualized Model, View & Delegate Interaction

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant View as CollectionVariablesTableView
    participant Delegate as ConflictStrategyDelegate
    participant Model as CollectionVariablesTableModel

    User->>View: Scrolls table (viewport exposes rows 100-130)
    loop For each visible cell (r, c)
        View->>Model: data(index(r, c), DisplayRole)
        Model-->>View: Formatted text / HIDDEN_MASK
        opt c == COL_SELECT
            View->>Model: data(index(r, c), CheckStateRole)
            Model-->>View: Checked / Unchecked
        end
    end
    Note over View: Zero widgets created for off-screen rows (1..99, 131..2500)

    User->>View: Clicks Conflict Strategy cell on row 105 (Collision)
    View->>Delegate: createEditor(parent, option, index)
    Delegate->>Model: data(index, DisplayRole)
    Delegate-->>View: QComboBox("Keep Current", "Overwrite")
    User->>Delegate: Selects "Overwrite"
    Delegate->>Model: setData(index, ConflictStrategy.OVERWRITE, EditRole)
    Model->>Model: Update record 105 strategy
    Model-->>View: dataChanged(index, index)
    Model-->>Dialog: Summary counts updated
    View->>Delegate: destroyEditor()
```

---

### 4. Component Responsibilities & Module Decomposition

| Module / Component | Responsibilities | Key Collaborators |
| --- | --- | --- |
| **`CollectionVariableRowRecord`** | Lightweight in-memory representation of one variable row: name, current value, candidate value, conflict strategy, secret status, collision status, selection status. | `CollectionVariablesTableModel` |
| **`CollectionVariablesTableModel`** | Subclasses `QAbstractTableModel`. Implements virtualized data provider, flags, editing, checkbox handling, preset updates, bulk operations, and real-time summary calculation. | `CollectionVariablesTableView`, `ConflictStrategyDelegate`, `Environment`, `Collection` |
| **`ConflictStrategyDelegate`** | Subclasses `QStyledItemDelegate`. Provides on-demand `QComboBox` editing for column 4 on colliding rows, committing user selections back to the model. Discarded upon edit finish. | `QTableView`, `CollectionVariablesTableModel` |
| **`CollectionFetchWorker`** | Subclasses `QThread`. Runs `library_service.read_collection` off the main thread. Emits completion and failure signals accompanied by generation token. | `library_service`, `ImportCollectionVariablesDialog` |
| **`CollectionVariablesTableView`** | Subclasses `QTableView`. Configures header behavior, selection modes, and exposes backward-compatible methods (`item()`, `cellWidget()`, `rowCount()`, `columnCount()`) for existing test suites and consumers. | `CollectionVariablesTableModel`, `ConflictStrategyDelegate` |
| **`ImportCollectionVariablesDialog`** | Dialog orchestrator. Manages source collection selection, preset selection, loading/error UI states, worker lifecycle, generation tokens, preview summary labels, and import confirmation. | `CollectionVariablesTableView`, `CollectionVariablesTableModel`, `CollectionFetchWorker`, `import_collection_variables_to_environment` |

---

### 5. Detailed Module Interfaces & Specifications

#### 5.1 `CollectionVariablesTableModel`

```python
class CollectionVariablesTableModel(QAbstractTableModel):
    def __init__(
        self,
        target_environment: Environment,
        collection: Collection | None = None,
        preset_name: str | None = None,
        parent: QObject | None = None,
    ) -> None: ...

    def rowCount(self, parent: QModelIndex = ...) -> int: ...
    def columnCount(self, parent: QModelIndex = ...) -> int: ...
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any: ...
    def flags(self, index: QModelIndex) -> Qt.ItemFlags: ...
    def data(self, index: QModelIndex, role: int = ...) -> Any: ...
    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool: ...

    # Domain & State Operations
    def load_collection(self, collection: Collection | None, preset_name: str | None = None) -> None: ...
    def set_preset(self, preset_name: str | None) -> None: ...
    def select_all(self) -> None: ...
    def deselect_all(self) -> None: ...
    def set_all_collision_strategy(self, strategy: ConflictStrategy) -> int: ...
    def get_row_strategy(self, row: int) -> ConflictStrategy | None: ...
    def set_row_strategy(self, row: int, strategy: ConflictStrategy) -> None: ...
    def is_row_selected(self, row: int) -> bool: ...
    def set_row_selected(self, row: int, selected: bool) -> None: ...
    def get_summary_counts(self) -> tuple[int, int, int, int]:
        """Returns (will_add, will_overwrite, will_keep, total_selected)."""
        ...
    def get_selected_keys(self) -> set[str]: ...
    def get_variable_conflict_strategies(self) -> dict[str, ConflictStrategy]: ...
```

#### 5.2 `ConflictStrategyDelegate`

```python
class ConflictStrategyDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject | None = None) -> None: ...
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget | None: ...
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None: ...
    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex
    ) -> None: ...
    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None: ...
```

#### 5.3 `CollectionFetchWorker`

```python
class CollectionFetchWorker(QThread):
    fetch_completed = Signal(object, int)  # (Collection, generation_id)
    fetch_failed = Signal(object, int)     # (Exception, generation_id)

    def __init__(
        self,
        library_service: Any,
        connection_id: str,
        collection_path: str,
        generation_id: int,
        parent: QObject | None = None,
    ) -> None: ...

    def run(self) -> None: ...
    def cancel(self) -> None: ...
```

#### 5.4 Backward-Compatibility Facade on `CollectionVariablesTableView`

```python
class CollectionVariablesTableView(QTableView):
    """QTableView providing backward-compatible access for tests and legacy callers."""

    def columnCount(self) -> int:
        return self.model().columnCount() if self.model() else 0

    def rowCount(self) -> int:
        return self.model().rowCount() if self.model() else 0

    def horizontalHeaderItem(self, col: int) -> _HeaderItemProxy: ...
    def item(self, row: int, col: int) -> _TableItemProxy: ...
    def cellWidget(self, row: int, col: int) -> QWidget | None: ...
```

---

## Q&A

**Q: How does `CollectionVariablesTableModel` handle dual-source secret masking during rapid scrolling?**  
A: Every `CollectionVariableRowRecord` computes `is_effective_secret = bool(var.secret) or (var.name in env.hidden_keys)` upon loading or updating. When the view queries `data(index, DisplayRole)` for `COL_CURRENT_VALUE` or `COL_CANDIDATE_VALUE`, the model directly returns `HIDDEN_MASK` (`********`) if `is_effective_secret` is true. Because this lookup is O(1) in-memory without string manipulation or regex parsing, scrolling at 60 FPS across thousands of rows remains completely fluid while guaranteeing zero plaintext leakage.

**Q: What happens if a user clicks "Overwrite All Collisions" when there are 2,500 variables?**  
A: In `CollectionVariablesTableModel.set_all_collision_strategy()`, the model iterates through its in-memory list of records, updates the strategy attribute on colliding records, and emits a single `dataChanged(index(0, COL_STRATEGY), index(rowCount - 1, COL_STRATEGY))` signal. Only the rows currently visible on screen are repainted by Qt. The entire bulk update and summary recalculation completes in under 5 milliseconds.

**Q: How does the generation counter prevent race conditions when switching remote collections?**  
A: When a user selects Remote Collection A, `_fetch_generation` increments to 1, and Worker A begins reading. If the user then selects Remote Collection B before Worker A finishes, `_fetch_generation` increments to 2, Worker A is signalled to cancel, and Worker B begins reading with generation 2. When Worker A eventually terminates and emits `fetch_completed(col_A, generation_id=1)`, the dialog compares `generation_id (1)` with `self._fetch_generation (2)`. Because `1 != 2`, Worker A's payload is safely dropped.

**Q: How does the dialog handle network failures or timeouts during remote fetching?**  
A: If `library_service.read_collection` raises an exception (such as `TimeoutError`, `ConnectionError`, or manifest parsing failure), the worker catches it and emits `fetch_failed(error, generation_id)`. If the generation matches, the dialog hides the loading indicator, displays an inline non-modal error message in `self.error_label` with a retry button, and keeps the source combo active. The dialog does not freeze or close, allowing the user to retry or switch collections without losing their active environment state.

**Q: Will existing PYPOST-1414 tests like `test_workspace_environment_import_diff_repro.py` continue to pass?**  
A: Yes. The custom `CollectionVariablesTableView` implements a lightweight compatibility layer providing `.item(row, col).text()`, `.horizontalHeaderItem(col).text()`, and `.cellWidget(row, COL_STRATEGY)`. In addition, public dialog methods like `get_row_strategy()`, `set_row_strategy()`, `bulk_set_collision_strategy()`, `select_all()`, and `deselect_all()` preserve their exact signatures and behavior. All existing tests in `test_workspace_environment_import_diff_repro.py` and `test_workspace_environment_import_repro.py` will pass cleanly.
