# PYPOST-34: Architecture for "Save As..." Action in Request Workflow

## Research

### External research (Qt official docs)

1. `QMenu` keeps action ordering as inserted; this supports explicit placement of `Save As...`
   before `Save`.
   Source: https://doc.qt.io/qt-6/qmenu.html
2. `QAction` provides a reusable command object with `triggered` signal for menu actions.
   Source: https://doc.qt.io/qt-6/qaction.html
3. `QFileDialog::getSaveFileName` describes standard save-file dialog behavior when user must
   provide a new save target.
   Source: https://doc.qt.io/qt-6/qfiledialog.html#getSaveFileName

### Current codebase findings

1. Request action menu is owned by `RequestWidget` in
   `pypost/ui/widgets/request_editor.py` and currently contains only `Save`.
2. Current save workflow emits `save_requested` from `RequestWidget` and is handled by
   `MainWindow.handle_save_request(...)` in `pypost/ui/main_window.py`.
3. Existing save flow supports overwrite for existing request IDs and creation flow via
   `SaveRequestDialog` for unsaved/new requests.
4. Step 1 requirement for this task is: `Save As...` appears in `Actions` before `Save`, opens
   new-save dialog flow, and always writes to a new request entity without overwriting source.

## Implementation Plan

1. Extend request action entry points in `RequestWidget` with a dedicated `Save As...` action
   placed before `Save`, plus keyboard shortcut `Ctrl+Shift+S`.
2. Introduce a separate event path from `RequestWidget` to `MainWindow` for `Save As...` to keep
   save semantics explicit and avoid accidental overwrite behavior reuse.
3. Reuse existing save dialog module (`SaveRequestDialog`) as the UI boundary for entering target
   name/collection, preserving current user save patterns.
4. Ensure save-as orchestration in `MainWindow` produces a new request identity and updates UI
   state (tab title, active request reference, collections tree).
5. Keep send flow and regular save flow unchanged.

## Architecture

### Module Diagram

```mermaid
flowchart LR
    U[User] -->|Actions: Save As...| RW[RequestWidget]
    U -->|Ctrl+Shift+S| RW
    RW -->|save_as_requested(RequestData)| MW[MainWindow Save-As Orchestrator]
    MW --> SD[SaveRequestDialog]
    SD -->|name + collection target| MW
    MW --> RM[RequestManager]
    RM --> ST[StorageManager]
    MW --> TV[Tabs and Collections UI State]

    U -->|Actions: Save| RW
    RW -->|save_requested(RequestData)| MW2[Existing Save Orchestrator]
```

### Modules and Responsibilities

1. `RequestWidget` (`pypost/ui/widgets/request_editor.py`)
   - Owns `Actions` menu structure and ordering.
   - Emits dedicated user-intent events: save vs save as.
2. Save-As Orchestrator (`MainWindow` scope)
   - Receives save-as intent and executes "always create new entity" behavior.
   - Coordinates dialog input, entity creation, and UI refresh.
3. `SaveRequestDialog` (`pypost/ui/dialogs/save_dialog.py`)
   - Captures user-provided request name and collection target.
   - Validates required save inputs before accept.
4. `RequestManager` / `StorageManager` (`pypost/core/`)
   - Persist new request entity and collection linkage.
5. UI State Update Layer (`MainWindow` tabs/tree)
   - Refreshes collections tree and updates active tab context to newly created request.

### Dependencies Between Modules

1. `RequestWidget` depends on Qt menu/action components and emits high-level signals only.
2. Save-As Orchestrator depends on `SaveRequestDialog` and `RequestManager`.
3. `SaveRequestDialog` depends on available collections provided by orchestrator.
4. UI State Update Layer depends on orchestrator outputs (new request data and target
   collection).

### Selected Architectural Patterns and Justification

1. Intent-Separated Command pattern
   - Separate `Save` and `Save As...` entry points to prevent semantic ambiguity between
     overwrite and create-new behavior.
2. Orchestrator pattern in `MainWindow`
   - Keep cross-module coordination (dialog, persistence, UI refresh) in one controller layer.
3. Signal-Slot Event pattern (Qt)
   - Preserve existing Qt event architecture and keep widget components decoupled from
     persistence logic.

### Main Interfaces Between Modules

1. `RequestWidget` -> `MainWindow` save-as interface
   - Event: `save_as_requested(RequestData)`.
   - Contract: data reflects current editor state at trigger time.
2. `MainWindow` -> `SaveRequestDialog` interface
   - Input: available collections and parent window context.
   - Output: accepted request name + target collection (or new collection intent).
3. `MainWindow` -> `RequestManager` persistence interface
   - Operation: create and persist a request as a new entity in target collection.
   - Contract: source request is not overwritten.
4. `MainWindow` -> UI state interface
   - Operations: update tab title/current request reference, reload collection tree, preserve
     expanded-state behavior.

### Interaction Scheme

1. User edits an existing request and selects `Actions -> Save As...`.
2. `RequestWidget` updates in-memory request data and emits save-as intent event.
3. `MainWindow` opens `SaveRequestDialog` for new save target input.
4. On confirm, orchestrator resolves target collection (existing or newly created).
5. Orchestrator persists a new request entity via `RequestManager`.
6. `MainWindow` refreshes tree/tabs and binds current tab to the newly created request entity.
7. Original request remains unchanged throughout this path.

## Q&A

- Q: Why separate save-as signal/path instead of reusing current save handler with a flag?
  A: Separate intent reduces regression risk in existing overwrite behavior and keeps logic
  explicit.
- Q: Why keep `SaveRequestDialog` rather than introducing a new dialog type?
  A: It already captures required save target data and aligns with current user flow.
- Q: How is menu placement guaranteed?
  A: `QMenu` action ordering follows insertion order, so `Save As...` is inserted before
  `Save`.
