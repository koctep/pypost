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

- No unit tests were added for the save logic or the settings persistence. Manual testing is relied
  upon.

## Performance Concerns

- As mentioned, linear search for request ID might be slow if the user has thousands of requests. A
  hash map index (ID -> Request) would be O(1). This can now be optimized inside `RequestManager`
  without changing the rest of the app.

## Follow-up Tasks

- **[COMPLETED] Refactor Request Management**: Create a `RequestManager` service.
- **Optimize Lookup**: Implement an index for request IDs inside `RequestManager`.
