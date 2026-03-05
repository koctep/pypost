# PYPOST-36: Technical Debt Analysis

## Shortcuts Taken

- Inline rename flow is implemented via `QTreeView` editor close events in `MainWindow`, without a
  dedicated delegate class. This is a pragmatic solution but keeps UI orchestration logic in one
  large window module.
- Rename test coverage is focused on business logic (`RequestManager`) and does not include GUI
  integration tests.

## Code Quality Issues

- `pypost/ui/main_window.py` is a large multi-responsibility class. Rename/delete/menu logic lives
  in the same file as unrelated UI behavior. A dedicated tree-item action controller would improve
  maintainability.
- Rename and delete flows duplicate parts of error/notification handling. Shared helpers could
  reduce repetition and lower change risk.

## Missing Tests

- No automated GUI test for:
  - context menu `Rename` visibility and selection,
  - inline rename commit/cancel behavior,
  - empty-name rejection path in UI,
  - rename observability metric increments in UI flow.
- No end-to-end storage-level test for collection rename when target filename already exists.

## Performance Concerns

- Rename success and cancel paths currently reload the full collections tree. For large trees this
  may be heavier than necessary. Incremental model updates could reduce UI work.

## Follow-up Tasks

- Add GUI integration tests for context-menu rename lifecycle (select, commit, cancel, validation).
- Extract collection-tree context-menu actions into a focused component/service.
- Add storage collision policy for collection names (currently filename-based persistence may
  overwrite same-name collection files).
- Add metrics assertions in automated tests for rename statuses.
