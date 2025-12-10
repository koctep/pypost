# Requirements: PYPOST-18 - Variable Tooltips in Tables

## Goals
Extend variable tooltip functionality (implemented in PYPOST-16) to header and parameter tables. This will allow users to see variable values without needing to switch context, even when working with tabular data.

## User Stories
- As a user, I want to see the value of the `{{token}}` variable in the Headers table when hovering over the corresponding cell.
- As a user, I want to see variable values in the Params table to verify correct substitution.
- As a user, if a cell contains multiple variables, I want to see all of them (or the fully resolved string) in the tooltip.

## Acceptance Criteria
- [ ] **Headers Table**: Hovering over a cell in the headers table containing `{{variable}}` displays a tooltip.
- [ ] **Params Table**: Hovering over a cell in the parameters table containing `{{variable}}` displays a tooltip.
- [ ] **Content Resolution**: The tooltip shows the resolved value of variables. If there are multiple variables, show either a list or (preferably) the resulting string with substituted values.
- [ ] **Dynamic Updates**: Tooltips use current values from the active environment.

## Task Description
It is necessary to refine `KeyValueTable` (or create `VariableAwareTableWidget`) by adding mouse event handling to display tooltips.

### Technical Details
- **Components**:
    - `KeyValueTable` (in `pypost/ui/widgets/request_editor.py`): Add inheritance or mixin to support variables.
    - `VariableHoverHelper`: Use existing helper for finding/resolving variables.
- **Challenges**:
    - In `QTableWidget` it is difficult to determine the exact character under the cursor without entering edit mode.
- **Solution**: When hovering over a cell, check its text. If the text contains variables, show a tooltip with a preview of the substitution result (e.g., `Bearer {{token}}` -> `Bearer secret_123`).

## Q&A
- **Should variables be highlighted inside the cell?**
    - No, standard `QTableWidget` rendering is sufficient.
- **What to show in the tooltip?**
    - The fully resolved string.
