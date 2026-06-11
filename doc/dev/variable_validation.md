# Variable Validation

## Overview

PYPOST-163 adds validation for new variable names to ensure they are compatible with Jinja2 templating used throughout PyPost. Previously, only empty string validation was performed when creating new environment variables via the context menu in the ResponseView.

## Why Variable Validation is Needed

Environment variables in PyPost are used as template variables in Jinja2 templates (for request URLs, headers, body, etc.). Jinja2 has specific rules for variable names:
- Must start with a letter or underscore
- Can only contain alphanumeric characters and underscores (a-z, A-Z, 0-9, _)
- Cannot start with a digit
- Cannot contain spaces or special characters (except underscore)

Without validation, users could create variable names that would cause template rendering errors when used in requests.

## Validation Rules

When creating a new variable name via the "New Variable..." option in the ResponseView context menu, the following rules are enforced:

1. **Not Empty**: Variable name cannot be empty or only whitespace
   - Error: "Variable name cannot be empty."

2. **First Character**: Must be a letter or underscore (cannot start with a digit)
   - Error: "Variable name cannot start with a digit."

3. **Subsequent Characters**: Must be alphanumeric or underscore only
   - Error: "Variable name can only contain letters, numbers, and underscores."

## Implementation Details

### Location
- **Rule source (shared):** `pypost/core/variable_name_validation.py`
  - `validate_variable_name(name) -> tuple[bool, str]` — pure validation, no side effects
- **UI integration:** `pypost/ui/presenters/env_presenter.py`
  - `EnvPresenter.handle_variable_set_request()` — new-variable flow
  - `EnvPresenter._is_valid_variable_name()` — delegates to core module; records metrics/logs

### Flow
1. User right-clicks in ResponseView → Context Menu → "Set Variable" → "New Variable..."
2. QInputDialog prompts for variable name
3. OnOK, the name is stripped and validated:
   - Empty check (existing)
   - Character validation (new)
4. If valid: Variable is created in current environment
5. If invalid: QMessageBox shows error, operation aborted

### Observability
- **Logging**: DEBUG logs for validation attempts, INFO logs for successful variable setting
- **Metrics**: 
  - `gui_variable_validation_total{result="valid|invalid"}` - tracks validation attempts
  - `gui_variable_validation_failures_total{reason="empty|starts_with_digit|invalid_chars"}` - tracks failures by reason

## Examples

### Valid Variable Names
- `api_key`
- `_internal`
- `userId123`
- `service_url`
- `DEBUG_MODE`

### Invalid Variable Names
- `123api` (starts with digit)
- `api-key` (contains hyphen)
- `user name` (contains space)
- `user.name` (contains period)
- `api key!` (contains space and exclamation)
- `""` (empty string)

## Backward Compatibility

This change only affects *new* variable creation. Existing environment variables with any naming convention continue to work unchanged. The validation is applied only when users attempt to create new variables via the UI.

## Related Components
- `ResponseView` (`pypost/ui/widgets/response_view.py`) - Triggers the variable setting flow
- `TabsPresenter` (`pypost/ui/presenters/tabs_presenter.py`) - Routes variable_set_requested signal
- `MainWindow` (`pypost/ui/main_window.py`) - Sets up signal connections
- `MetricsManager` (`pypost/core/metrics.py`) - Tracks validation metrics