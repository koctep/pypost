# Requirements: PYPOST-6 - Single-Click Interaction

## Problem/Task Description
The current implementation of the collection tree requires a double-click to open requests or expand folders, which slows down navigation. It is necessary to change the interaction model so that main actions are performed with a single click, as is common in many modern IDEs and editors (e.g., VS Code in preview mode, or simply to speed up work).

## Programming Language
**Python** (PySide6/Qt for UI)

## Functional Requirements

### 1. Opening Requests
- **Action**: Single click with the left mouse button on a request item in the collection tree.
- **Result**:
    - If the request is already open in a tab -> the tab becomes active.
    - If the request is not open -> it opens in a new tab (or replaces the current one if preview mode is implemented, but standard opening is implied for now).
- **Context**: `CollectionTreeWidget` (or similar component).

### 2. Working with Folders
- **Action**: Single click with the left mouse button on a folder item (or collection acting as a root folder).
- **Result**: Toggle expansion state (Expand/Collapse).
    - If the folder is collapsed -> it expands.
    - If the folder is expanded -> it collapses.
- **Exception**: Clicking on the arrow (expansion indicator) should work as before (standard Qt behavior), but now clicking on the name/row of the folder also triggers this action.

### 3. Double Click
- Special actions for double click are not required (behavior is absorbed by single click).

## Non-functional Requirements
- **Responsiveness**: The interface must react instantly.
- **Compatibility**: The change must not break context menu (Right click) or Drag & Drop functionality, if present or planned.

## Entities
- `CollectionTree` / `RequestWidget`: UI components requiring signal processing changes (`itemClicked` instead of `itemDoubleClicked` or similar).
