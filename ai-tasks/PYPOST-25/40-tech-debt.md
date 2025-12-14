# PYPOST-25: Technical Debt Analysis

## Shortcuts Taken

- **Manual Signal Connection**: Signal connection happens in `add_new_tab`. If tabs are created elsewhere, connection might be missed.
- **No Validation for New Variable Name**: Basic check for empty string is present, but no check for valid characters (e.g., spaces, special symbols) that might be invalid for Jinja2 templates.

## Missing Tests

- No UI tests for context menu interaction.

## Follow-up Tasks

- Add validation for variable names.
