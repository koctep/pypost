# PYPOST-341: Architecture

## Research

- `EnvironmentNameDelegate` validates in `setModelData` and calls back on accept.
- `CollectionTreeActions` already owns rename business logic and incremental tree sync.
- `CollectionsPresenter` wires the tree view and `CollectionTreeActions`.

## Implementation Plan

1. Add `CollectionItemRenameDelegate` in `pypost/ui/delegates/`.
2. Delegate: `createEditor` only for pending-rename index; `setEditorData` shows request
   name (not `METHOD name`); `setModelData` trims/commits or rejects empty; `closeEditor`
   handles Escape cancel.
3. `CollectionTreeActions`: replace `on_editor_closed` with `handle_rename_committed`,
   `handle_rename_cancelled`, `handle_rename_rejected_empty`, and `is_rename_index`.
4. `CollectionsPresenter`: `setItemDelegate(CollectionItemRenameDelegate(...))`; remove
   `itemDelegate().closeEditor` wiring.
5. Tests: new delegate unit tests; update presenter rename tests to call new handlers.

## Architecture

```mermaid
flowchart LR
    CP[CollectionsPresenter]
    D[CollectionItemRenameDelegate]
    CTA[CollectionTreeActions]
    RM[RequestManager]
    CP -->|setItemDelegate| D
    D -->|on_committed / on_cancelled| CTA
    CTA --> RM
```

| Component | Responsibility |
|-----------|----------------|
| `CollectionItemRenameDelegate` | Editor lifecycle, empty-name guard, cancel detection |
| `CollectionTreeActions` | Persistence, metrics, dialogs, tree sync |
| `CollectionsPresenter` | Tree model, delegate installation, signal wiring |

## Removed

- `CollectionTreeActions.on_editor_closed`
- `CollectionsPresenter` `closeEditor` connection on default delegate
- Temporary `item.setText(data.name)` before `edit()` for requests
