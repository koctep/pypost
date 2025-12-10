# PYPOST-17: Technical Debt Analysis

## Shortcuts Taken

- **Search for existing request**: We iterate through all collections and requests to find the
  request ID. For a small number of requests, this is fine, but it's O(N) where N is total requests.
- **Data Update**: We update the request object in place within the collection list. Ideally, there
  should be a cleaner method in `StorageManager` or `Collection` model to "update_request(req)".

## Code Quality Issues

- `MainWindow.handle_save_request` is becoming a bit large and handles UI logic (dialogs), business
  logic (search), and storage logic. It might be better to move the "search and save" logic into a
  controller or service method.

## Missing Tests

- No unit tests were added for the save logic or the settings persistence. Manual testing is relied
  upon.

## Performance Concerns

- As mentioned, linear search for request ID might be slow if the user has thousands of requests. A
  hash map index (ID -> Request) would be O(1).

## Follow-up Tasks

- **Refactor Request Management**: Create a `RequestManager` service that handles finding, updating,
  and saving requests, decoupling it from `MainWindow`.
- **Optimize Lookup**: Implement an index for request IDs.
