# PYPOST-18: Technical Debt Analysis

## Shortcuts Taken

- **Manual Variable Propagation**: Variable updates happen via explicit call to `set_variables` in `RequestWidget`, which pushes them down the hierarchy. This works, but as UI structure complicates, it might become inconvenient. In the future, consider using Dependency Injection or a global context/signal mechanism.

## Code Quality Issues

- **VariableHoverHelper**: The helper performs two functions: finding a variable by index (for text fields) and full string resolution (for tables). Perhaps variable resolution logic should be separated into a distinct service (e.g., `EnvironmentService` or `TemplateEngine`) to avoid duplicating substitution logic, which might also exist in `TemplateEngine`.

## Missing Tests

- **Unit Tests**: Unit tests for `VariableHoverHelper.resolve_text` are missing. Tests were created but not committed.
- **UI Tests**: No automated UI tests to verify tooltip appearance in the table.

## Performance Concerns

- **MouseMoveEvent**: Variable resolution happens inside `mouseMoveEvent`. Although the regular expression is simple, with very large tables and active mouse movement, this could create load. Currently, preliminary check `VARIABLE_PATTERN.search(text)` minimizes impact.

## Follow-up Tasks

- [ ] Write and commit unit tests for `VariableHoverHelper` (methods `find_variable_at_index` and `resolve_text`).
- [ ] Consider moving variable substitution logic to a common `TemplateEngine`.
