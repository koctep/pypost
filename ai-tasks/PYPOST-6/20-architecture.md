# Architecture: PYPOST-6 - Single-Click Interaction with Collections

## 1. Overview of Changes
Changes affect the `MainWindow` class in the `pypost/ui/main_window.py` module. The main goal is to replace the double-click event (`doubleClicked`) with a single-click (`clicked`) for the `QTreeView` element (collection tree), implementing appropriate logic for requests and folders.

## 2. System Modules

**File**: `pypost/ui/main_window.py`
**Class**: `MainWindow`

#### Changes in `__init__`:
- Remove `doubleClicked` signal connection.
- Add `clicked` signal connection to the click handling slot.

#### New/Modified Methods:
- Main click handling method.
- **Algorithm**:
    1. Get item/data by index (`index`).
    2. Determine item type (Request or Folder/Collection).
    3. **If Request**:
        - Call request opening logic (existing code from `on_collection_double_click`).
    4. **If Folder/Collection**:
        - Check current state (`self.collections_view.isExpanded(index)`).
        - If collapsed -> Expand (`self.collections_view.expand(index)`).
        - If expanded -> Collapse (`self.collections_view.collapse(index)`).

## 3. Component Interaction
[No significant changes in interaction between components]

## 4. Constraints and Risks
- Conflict with Selection: Single click also selects the item. This is expected behavior; there should be no conflicts.
- Double Click: Will be perceived as two fast single clicks. For folders, this will lead to rapid expansion and collapse, which may look like "flickering".
- *Solution*: In most file managers, single-click expand works fine. If it becomes annoying, a timer check could be added, but it's overhead for current requirements. Standard explorer behavior (with "open with single click" enabled) is the norm.

## 5. Migration Plan
1. Change signal binding in `MainWindow`.
2. Rename `on_collection_double_click` to `on_collection_clicked` (or create new and move logic).
3. Add toggle expansion logic.
