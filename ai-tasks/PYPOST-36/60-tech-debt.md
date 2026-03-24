# PYPOST-36: Technical Debt Analysis


## Shortcuts Taken

- **Inline rename without delegate** ([PYPOST-341](https://pypost.atlassian.net/browse/PYPOST-341)):
  Rename uses `QTreeView` editor close events in `MainWindow` rather than a dedicated delegate;
  pragmatic but keeps orchestration in a large module.
- **Rename tests omit GUI** ([PYPOST-342](https://pypost.atlassian.net/browse/PYPOST-342)):
  Coverage focuses on `RequestManager` business logic, not GUI integration.

## Code Quality Issues

- **Monolithic MainWindow** ([PYPOST-343](https://pypost.atlassian.net/browse/PYPOST-343)):
  Rename, delete, and menu logic share a file with unrelated UI behavior; a tree-action controller
  would improve maintainability.
- **Duplicated error handling** ([PYPOST-344](https://pypost.atlassian.net/browse/PYPOST-344)):
  Rename and delete flows repeat notification/error patterns; shared helpers would reduce risk.

## Missing Tests

- **GUI rename gaps** ([PYPOST-345](https://pypost.atlassian.net/browse/PYPOST-345)):
  - context menu `Rename` visibility and selection,
  - inline rename commit/cancel behavior,
  - empty-name rejection path in UI,
  - rename observability metric increments in UI flow.
- No end-to-end storage-level test for collection rename when target filename already exists.
  — [PYPOST-346](https://pypost.atlassian.net/browse/PYPOST-346)

## Performance Concerns

- **Full tree reload on rename** ([PYPOST-347](https://pypost.atlassian.net/browse/PYPOST-347)):
  Success and cancel paths reload the entire collections tree; incremental model updates could
  reduce work for large trees.

## Follow-up Tasks

- Add GUI integration tests for context-menu rename lifecycle (select, commit, cancel,
  validation).
  — [PYPOST-348](https://pypost.atlassian.net/browse/PYPOST-348)
- Extract collection-tree context-menu actions into a focused component/service.
  — [PYPOST-349](https://pypost.atlassian.net/browse/PYPOST-349)
- **Storage collision policy** ([PYPOST-350](https://pypost.atlassian.net/browse/PYPOST-350)):
  Clarify behavior when collection names collide under filename-based persistence (possible
  overwrites).
- Add metrics assertions in automated tests for rename statuses.
  — [PYPOST-351](https://pypost.atlassian.net/browse/PYPOST-351)
