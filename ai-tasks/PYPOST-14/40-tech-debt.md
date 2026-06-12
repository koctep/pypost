# PYPOST-14: Technical Debt Analysis


## Status: FIXED
Addressed in PYPOST-14 by implementing `RequestManager`.

## Shortcuts Taken

- **[FIXED] Search for existing request**: Logic for searching requests has been moved to `RequestManager.find_request`. While it is still O(N) internally, the complexity is encapsulated.
- **[FIXED] Data Update**: Request updates are now handled by `RequestManager.save_request`.

## Code Quality Issues

- **[FIXED] `MainWindow.handle_save_request` complexity**: The logic has been simplified by delegating
  search and persistence to `RequestManager`. `MainWindow` now focuses on UI interaction (dialogs).

## Missing Tests

- No unit tests were added for the save logic or the settings persistence; manual testing
  is relied upon.
  — [PYPOST-125](https://pypost.atlassian.net/browse/PYPOST-125)

## Performance Concerns

- **[FIXED] Linear request ID search**: Replaced with `_request_index` hash map for O(1) lookup
  in `RequestManager.find_request` ([PYPOST-127](https://pypost.atlassian.net/browse/PYPOST-127),
  [PYPOST-126](https://pypost.atlassian.net/browse/PYPOST-126)).

## Follow-up Tasks

- **[COMPLETED] Refactor Request Management**: Create a `RequestManager` service.
- **[COMPLETED] Optimize Lookup**: Index for request IDs inside `RequestManager`. — [PYPOST-127](https://pypost.atlassian.net/browse/PYPOST-127)
