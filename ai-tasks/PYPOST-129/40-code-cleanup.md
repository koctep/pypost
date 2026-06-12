# PYPOST-129: Code Cleanup

## Lint and format

- No new linter issues in edited files.
- Line length within 100 characters.

## Structure

- Removed monolithic `VariableHoverHelper` implementation; logic lives in two focused classes.
- `_TemplateServiceAlias` descriptor keeps test patching ergonomic without duplicating service
  state.

## Imports

- Call sites import `VariableHoverLocator` / `VariableHoverResolver` where the responsibility
  is unambiguous.
- Tests retain `VariableHoverHelper` coverage for the facade.
