# Architecture: PYPOST-163

## Overview
The task is to add validation for new variable names in the environment variable setting functionality. Currently, only an empty string check is performed when creating new variable names via the context menu in ResponseView. This architecture extends the validation to ensure variable names contain only valid characters for Jinja2 templates (alphanumeric and underscore, not starting with a digit).

## Changes Summary

### 1. `EnvPresenter.handle_variable_set_request()` (`pypost/ui/presenters/env_presenter.py`)
**Current Behavior**: 
- When `key` is None (new variable), shows QInputDialog to get variable name
- Only validates that the name is not empty after stripping

**New Behavior**:
- Add character validation for Jinja2-compatible variable names
- Valid characters: letters (a-z, A-Z), digits (0-9), underscore (_)
- Cannot start with a digit
- Show appropriate error message for invalid characters
- Implemented `_is_valid_variable_name` helper method for validation logic
- Added metrics tracking for validation attempts and failures

### 2. Validation Logic
Implemented helper function to validate variable names:
- Check if string is empty (existing)
- Check if first character is a digit (invalid)
- Check if all characters are alphanumeric or underscore (invalid if not)
- Provide clear error messages for each validation failure
- Track validation metrics for monitoring

## Component Changes

### `EnvPresenter` (`pypost/ui/presenters/env_presenter.py`)
- Modified `handle_variable_set_request` method to include character validation
- Added private helper method `_is_valid_variable_name(name: str) -> tuple[bool, str]` 
- The helper returns (is_valid, error_message) for clear feedback
- Added metrics tracking for validation attempts (valid/invalid) and failures by type

## Validation Rules
1. **Not Empty**: Variable name cannot be empty or only whitespace
2. **First Character**: Must be a letter or underscore (cannot start with digit)
3. **Subsequent Characters**: Must be alphanumeric or underscore only
4. **Error Messages**: 
   - Empty: "Variable name cannot be empty."
   - Starts with digit: "Variable name cannot start with a digit."
   - Invalid characters: "Variable name can only contain letters, numbers, and underscores."

## Dependencies
- No new dependencies required
- Uses existing PySide6 QInputDialog and QMessageBox for user interaction
- Builds upon existing variable setting flow
- Uses existing MetricsManager for tracking validation metrics

## Risks & Mitigation
- **Risk**: Changing validation might break existing workflows if users have variables with invalid names
  - **Mitigation**: This only affects *new* variable creation; existing variables are unaffected
- **Risk**: Overly restrictive validation might block legitimate use cases
  - **Mitigation**: Follows standard Jinja2/Python variable naming conventions which are widely accepted

## Implementation Approach
1. Extracted validation logic to a reusable helper method
2. Integrated validation into the existing new variable flow
3. Maintained backward compatibility for all existing functionality
4. Provided clear, actionable error messages to guide users
5. Added metrics tracking for observability

## Flow Diagram
```
User Right-Clicks ResponseView → Context Menu → "Set Variable" → "New Variable..."
                                                    ↓
                                    QInputDialog.getText() → User enters name
                                                    ↓
                                    EnvPresenter.handle_variable_set_request(key=None, value)
                                                    ↓
                                    [NEW] Validate variable name characters via _is_valid_variable_name
                                                    ↓
                                    If valid: Proceed to set variable in environment
                                    If invalid: Show QMessageBox with error, abort
```