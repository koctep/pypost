# PYPOST-15: Technical Debt Analysis


## Shortcuts Taken

- **Manual Variable Propagation**: Variable updates happen via explicit call to `set_variables` in `RequestWidget`, which pushes them down the hierarchy. This works, but as UI structure complicates, it might become inconvenient. In the future, consider using Dependency Injection or a global context/signal mechanism. — [PYPOST-128](https://pypost.atlassian.net/browse/PYPOST-128)

## Code Quality Issues

- **VariableHoverHelper**: The helper performs two functions: finding a variable by index (for text fields) and full string resolution (for tables). Perhaps variable resolution logic should be separated into a distinct service (e.g., `EnvironmentService` or `TemplateEngine`) to avoid duplicating substitution logic, which might also exist in `TemplateEngine`. — [PYPOST-129](https://pypost.atlassian.net/browse/PYPOST-129)

## Missing Tests

- **Unit Tests**: Unit tests for `VariableHoverHelper.resolve_text` are missing. Tests were created but not committed. — [PYPOST-130](https://pypost.atlassian.net/browse/PYPOST-130)
- **UI Tests**: No automated UI tests to verify tooltip appearance in the table. — [PYPOST-131](https://pypost.atlassian.net/browse/PYPOST-131)

## Performance Concerns

- **MouseMoveEvent**: Variable resolution happens inside `mouseMoveEvent`. Although the regular expression is simple, with very large tables and active mouse movement, this could create load. Currently, preliminary check `VARIABLE_PATTERN.search(text)` minimizes impact. — [PYPOST-132](https://pypost.atlassian.net/browse/PYPOST-132)

## Follow-up Tasks

- Write and commit unit tests for `VariableHoverHelper` (methods `find_variable_at_index` and `resolve_text`). — [PYPOST-133](https://pypost.atlassian.net/browse/PYPOST-133)
- Consider moving variable substitution logic to a common `TemplateEngine`. — [PYPOST-134](https://pypost.atlassian.net/browse/PYPOST-134)
