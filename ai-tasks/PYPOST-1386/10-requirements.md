# PYPOST-1386: Refactor HiddenFieldsTable to Virtualized Model for Large Selector Datasets

## Goals

In enterprise API testing and development, organizations frequently operate with complex microservices and extensive data payloads (e.g., healthcare FHIR bundles, financial banking records, customer ERP systems) containing hundreds or thousands of nested fields, personally identifiable information (PII), credentials, and regulatory-sensitive attributes.

When users configure response masking in PyPost using the "Hidden Fields" tab of `RequestEditor`, two critical user experience and scalability limitations emerge when managing large selector catalogs:

1. **Sluggish Scrolling and Interface Stutter at Scale**: When a request contains a large number of hidden field selectors (e.g., 500 to 1,000+ paths), the UI table experiences noticeable frame drops, rendering lag, and stutter during vertical scrolling. A smooth 60 frames per second (FPS) interactive experience is essential for developer productivity during payload inspection.
2. **High Memory Overhead from Concrete Item Allocations**: The existing table implementation creates standalone table item objects for every individual row and cell regardless of whether they are visible on screen. In massive selector configurations, this leads to unnecessary memory footprint, delayed initial dialog rendering, and slower garbage collection cycles.
3. **Preservation of Core Editing Workflows**: While modernizing the table presentation layer, all interactive editing features established in PYPOST-1377 must remain completely intact. Specifically, the auto-expanding trailing empty row for fast sequential entry, inline editing, context menu actions ("Add Selector", "Remove Selected"), keyboard shortcuts (`Delete`/`Backspace`), request dirty-state tracking, and tab-isolation copy semantics must continue to function seamlessly.
4. **Decoupled Architecture and Backward Compatibility**: The underlying data model and presentation view must be cleanly separated, while providing full backward compatibility with existing request editor bindings, automated UI test contracts, and accessor APIs.

The business goal of this task is to provide an instantaneous, responsive, and lightweight selector configuration experience that effortlessly scales to massive selector lists (>1,000 entries) with zero UI freezes, smooth 60 FPS scrolling, minimal memory overhead, and 100% preservation of user editing interactions and API contracts.

## Implementation Language

- **Implementation language**: Python

## User Stories

- As an **enterprise security engineer**, I want to configure and inspect lists of over 1,000 sensitive field selectors in a request without experiencing UI stutter, laggy scrolling, or interface freezes.
- As an **API developer**, I want to quickly type new selector expressions into an auto-expanding empty row at the bottom of the table without having to click an external "Add" button between each entry.
- As a **QA engineer**, I want to select multiple selector rows and delete them simultaneously using either the `Delete` key, `Backspace` key, or a right-click context menu, so that I can efficiently clean up obsolete masking rules.
- As an **application user**, I want changes made in the hidden fields table to immediately trigger dirty tracking and tab indicators, ensuring unsaved modifications are never lost when navigating between requests or tabs.
- As a **maintainer of PyPost UI test suites**, I want the table's public interface and contract methods (`get_data()`, `set_data()`, `add_row()`, `remove_selected_rows()`, and change signals) to remain fully backward compatible so existing tests and parent widgets continue operating without breaking changes.

## Definition of Done

This task is considered complete when:

1. The hidden fields table utilizes virtualized presentation, evaluating and rendering only the rows currently visible within the active scroll viewport rather than instantiating widget items for the entire dataset upfront.
2. The table maintains a fluid 60 FPS vertical scrolling rate (frame rendering latency under 16 ms) when populated with large selector datasets (>1,000 entries).
3. Initialization and population of the table with 1,000+ selector entries occurs rapidly (<100 ms) without freezing or blocking the main application window.
4. The auto-expanding empty trailing row interaction is preserved:
   - Entering text into the last row automatically appends a new blank trailing row.
   - Calling `set_data(selectors)` always terminates with a clean, editable trailing empty row.
5. Inline editing of selector strings, keyboard deletion (`Delete` / `Backspace`), and context menu operations ("Add Selector", "Remove Selected") function identically to existing behavior.
6. Multi-row selection and batch deletion remove all selected non-empty rows while preserving the trailing empty row invariant.
7. Change signals (`data_changed` and `changed`) are emitted on every addition, modification, and deletion to ensure parent `RequestEditor` dirty tracking and unsaved change detection remain fully operational.
8. The table preserves complete public API backward compatibility:
   - `get_data() -> list[str]`
   - `set_data(data: list[str]) -> None`
   - `add_row(selector: str = "") -> None`
   - `remove_selected_rows() -> None`
   - Signals: `data_changed`, `changed`
   - Accessor facades or property contracts required by existing UI tests (such as `rowCount()` and item access).
9. All automated unit and integration tests pass cleanly, and code conforms to repository standards via `make check`.

## Task Description

### Problem Statement

In `PYPOST-1377`, the initial `HiddenFieldsTable` component was implemented using a concrete widget-based table (`QTableWidget`) to rapidly deliver the masking configuration interface for `RequestEditor`. In this approach, each selector entry requires instantiating visual table item objects on the heap. While performant for typical workloads (1–50 selectors), large enterprise API requests containing hundreds or thousands (>1,000) of sensitive field selectors suffer from:
- Delayed dialog initialization and loading times.
- Stutter and frame drops during vertical scrolling because off-screen items incur layout and memory overhead.
- Tight coupling between presentation items and underlying string data.

### Scope

- **Virtualized Table Presentation**: Transitioning the table component to a virtualized model-view architecture where cell rendering is deferred and bound dynamically to visible viewport rows.
- **Efficient Memory Model**: Storing the selector list in a lightweight Python data structure without per-cell widget allocations for off-screen rows.
- **Workflow & Interaction Parity**:
  - Auto-expanding trailing row for rapid sequential input.
  - Context menu actions: "Add Selector" and "Remove Selected".
  - Keyboard shortcuts: `Delete` and `Backspace` outside cell editing mode.
  - Multi-row selection and deletion.
  - Whitespace trimming on retrieval and omission of empty rows.
- **Signal & Notification Continuity**: Emitting `data_changed` and `changed` signals whenever table contents are modified.
- **Backward Compatibility**: Maintaining identical external interface methods (`get_data`, `set_data`, `add_row`, `remove_selected_rows`) and supporting existing test assertions.

### Out of Scope / Constraints

- Changes to request persistence, JSON serialization schemas, or Pydantic data models (`RequestData.hidden_response_fields` remains `list[str]`).
- Modifying the masking engine or MCP response sanitization logic (`sensitive_text_sanitizer.py`, `McpResponseSanitizer`).
- Modifying the click-to-reveal response view presentation in `ResponseView`.
- Implementing complex selector syntax validation or regex compilers (tracked separately under PYPOST-1387).
- Adding multi-column selector metadata (e.g., custom replacement masks or comments).

### Functional Requirements

- **FR1: Virtualized Selector Display**:
  - The table must render selector strings efficiently using on-demand viewport virtualization.
  - The single column header must remain titled `"Field Selector"` and stretch across the available table width.
  - Only visible rows must be rendered at any given time, avoiding upfront instantiation of visual widgets for non-visible rows.

- **FR2: Auto-Expanding Trailing Row**:
  - The table must always maintain exactly one empty trailing row at the bottom of the list to facilitate rapid consecutive data entry.
  - When the user inputs text into the trailing empty row, a new empty trailing row must automatically be generated below it.
  - Loading an empty dataset (`set_data([])`) must display exactly one empty row ready for editing.

- **FR3: Data Population and Extraction**:
  - `set_data(data: list[str])` must populate the table with the provided list of selector strings, trimming whitespace and filtering out empty entries, followed by a single empty trailing row.
  - `get_data() -> list[str]` must return all non-empty selector strings in row order, omitting trailing or intermediate empty rows.

- **FR4: Row Addition and Selection**:
  - `add_row(selector: str = "")` must append a new selector or focus and activate the existing trailing blank row if already empty.
  - If a non-empty selector string is passed to `add_row("path.to.field")`, it must populate the trailing row, append a new blank row, and select the newly added row.

- **FR5: Row Removal and Batch Deletion**:
  - `remove_selected_rows()` must delete all selected rows from the table, except for the trailing empty row.
  - If all rows are deleted, the table must retain or recreate a single empty trailing row.
  - The right-click context menu must provide "Remove Selected" (enabled when one or more rows are selected) and "Add Selector".
  - Pressing `Delete` or `Backspace` when the table has selected rows (and is not actively editing text in a cell) must invoke `remove_selected_rows()`.

- **FR6: Change Notification**:
  - The table must emit both `data_changed` and `changed` signals whenever a selector is added, edited, or removed.
  - `RequestEditor` must receive these signals to update tab dirty status and enable save actions.

- **FR7: API & Test Compatibility**:
  - The table component must preserve all existing public methods and properties so parent widgets and existing tests continue to operate without modification.
  - Common table introspection operations utilized in existing automated tests (such as checking `rowCount()` and verifying cell item text) must be supported.

### Non-Functional Requirements

- **NFR1: Performance & Scroll Fluidity**:
  - Vertical scrolling must maintain 60 FPS (frame rendering time < 16 ms) with 1,000+ selector rows.
  - Initial load time for 1,000 rows via `set_data()` must be under 100 ms on standard desktop hardware.
- **NFR2: Memory Footprint**:
  - Heap memory usage for the table must scale with the number of visible rows in the viewport, rather than growing proportionally to the total number of entries with dedicated widget allocations.
- **NFR3: Code Quality & Repository Compliance**:
  - All code must comply with repository standards and pass `make lint`, `make typecheck`, and `make check`.
- **NFR4: Reliability & Test Coverage**:
  - All existing test contracts in `tests/test_request_hidden_fields_model_and_ui.py` must pass.
  - New test coverage must verify virtualization behavior with 1,000+ entries.

## Entities

- **Field Selector**: A string expression representing a JSON key or dot-notation path (e.g., `token`, `auth.secret`, `data.users[*].ssn`) whose values should be hidden or masked in response representations.
- **Selector Collection**: An ordered sequence of string selectors associated with a `RequestData` entity, represented as a Python list of strings.
- **Virtualized Selector Viewport**: The visual rendering window that displays and scrolls through the selector collection, instantiating visual cells only for rows currently within the visible geometry.
- **Trailing Blank Entry**: A dedicated, editable empty entry maintained at the end of the selector collection to streamline user entry of subsequent selectors.
- **Table Change Event**: A notification emitted whenever the user modifies, adds, or removes a selector in the table, informing parent components (such as `RequestWidget`) to mark the document draft dirty.

## Q&A

### Q1: Why is this refactoring needed if the existing table works for typical requests?
**A**: While typical requests only configure 5–20 hidden field selectors, enterprise users frequently handle large monolithic APIs or multi-tenant microservices where payloads contain hundreds or thousands of nested fields. With the current `QTableWidget` implementation, every row instantiates a heavy `QTableWidgetItem` object, leading to slow dialog initialization, high memory usage, and stuttering during vertical scrolling. Moving to a virtualized model decouples the data array from the view, achieving constant-time viewport rendering and silky-smooth 60 FPS scrolling regardless of list size.

### Q2: How does the auto-expanding trailing row work in a virtualized model?
**A**: In the virtualized model, the underlying data source treats the list of selectors plus one virtual trailing blank entry as the total row count (`len(selectors) + 1`). When the user commits text into the trailing empty row, the model appends the string to the data store, notifies the view of a newly inserted row, and creates the next empty trailing row seamlessly.

### Q3: Will existing tests or parent widgets break with this refactoring?
**A**: No. The refactored table preserves all public methods (`set_data()`, `get_data()`, `add_row()`, `remove_selected_rows()`) and signals (`data_changed`, `changed`). Furthermore, compatibility facades for standard table queries (such as `rowCount()` and `item(row, col)`) will ensure that existing UI integration tests continue passing without modification.

### Q4: Does this change alter the serialization format or storage of `hidden_response_fields`?
**A**: No. The serialization format remains a standard JSON array of strings (`list[str]`) within `RequestData`. The refactoring is strictly confined to the UI table presentation and data virtualization layer.
