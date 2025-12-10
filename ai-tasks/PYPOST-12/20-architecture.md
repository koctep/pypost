# Architecture: PYPOST-12 - Saving Tree View State

## Research
In `PySide6`, `QTreeView` has methods `expand(index)`, `collapse(index)`, and `isExpanded(index)`.
The data model (`QStandardItemModel`) stores data. Top-level items (collections) have `Qt.UserRole` with the collection ID (UUID).

To track expansion/collapse state changes, signals `expanded(QModelIndex)` and `collapsed(QModelIndex)` of `QTreeView` itself can be used.

Settings storage is already implemented via `AppSettings` and `ConfigManager`. We need to add a new field to `AppSettings`.

## Implementation Plan
1.  **Data Model**:
    *   Update `pypost/models/settings.py`: add field `expanded_collections: List[str] = []` to `AppSettings` class.

2.  **UI Logic (`MainWindow`)**:
    *   In `__init__` or `load_collections`:
    *   After loading data, iterate through model items.
    *   If collection ID is in `settings.expanded_collections`, call `self.collections_view.expand(index)`.
    *   Connect `QTreeView.expanded` and `QTreeView.collapsed` signals to new slots.
    *   In signal handling slots:
    *   Get collection ID from index.
    *   Update `expanded_collections` list in `self.settings`.
    *   Save settings via `self.config_manager.save_config(self.settings)`.

## Architecture

### 1. Models (`pypost/models/settings.py`)
Change settings schema to store list of expanded collection IDs.

### 2. UI (`pypost/ui/main_window.py`)
Add logic for handling tree signals and restoring state.

*   **New Methods**:
    *   `on_tree_expanded(index: QModelIndex)`: Adds ID to settings.
    *   `on_tree_collapsed(index: QModelIndex)`: Removes ID from settings.
    *   `restore_tree_state()`: Applies settings to tree after loading.

*   **Changes in `load_collections`**:
    *   Call `restore_tree_state()` after populating the model.

### 3. Interaction
[Diagram describing interaction]

## Q&A
*   **Q: What if a collection ID is in settings, but the collection itself no longer exists?**
    *   A: `restore_tree_state` will simply ignore IDs not present in the model. On next save (if user collapses/expands something), the list will be overwritten with actual data (or cleanup can be done on load, but "lazy" update on save is simpler).
*   **Q: When to save settings?**
    *   A: Can save immediately on every click (simple and reliable for desktop app with local config).
