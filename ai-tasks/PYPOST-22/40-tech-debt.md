# PYPOST-22: Technical Debt Analysis


## Shortcuts Taken

- **Manual Signal Connection**: Signal connection happens in `add_new_tab`. If tabs are created elsewhere, connection might be missed. — [PYPOST-162](https://pypost.atlassian.net/browse/PYPOST-162)
- **No Validation for New Variable Name**: Basic check for empty string is present, but no check for valid characters (e.g., spaces, special symbols) that might be invalid for Jinja2 templates. — [PYPOST-163](https://pypost.atlassian.net/browse/PYPOST-163)

## Missing Tests

- No UI tests for context menu interaction. — [PYPOST-164](https://pypost.atlassian.net/browse/PYPOST-164)

## Follow-up Tasks

- Add validation for variable names. — [PYPOST-165](https://pypost.atlassian.net/browse/PYPOST-165)
