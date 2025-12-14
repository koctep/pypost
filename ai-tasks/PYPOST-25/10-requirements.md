# Requirements: PYPOST-25 - Response Context Menu (Set env)

## Goals
Improve the convenience of working with environment variables by allowing the user to quickly update variable values and create new ones directly from the received response.

## User Stories
- As a user, I want to access the "Set env" function in the response context menu as the first item, and "Copy" as the second.
- As a user, I want to select text in the response and save it to an existing environment variable via the context menu.
- As a user, I want to be able to create a new environment variable from the selected text via the same menu.

## Acceptance Criteria
- [ ] In the `ResponseView` component, a context menu appears when right-clicking on selected text.
- [ ] Menu item order:
    1.  `Set env` (submenu)
    2.  `Copy`
- [ ] In the `Set env` submenu:
    - List of existing environment variables.
    - Item `New Variable...` (or similar) to create a new variable.
- [ ] When selecting an existing variable, its value is updated.
- [ ] When selecting `New Variable...`, a dialog appears to enter the name of the new variable. After entry, the variable is created with the selected value.
- [ ] Changes are saved in the environment configuration.
- [ ] The updated/new value is immediately available for use.

## Task Description
It is necessary to refine `ResponseView` and `MainWindow`.

### Technical Details
- **Component**: `ResponseView`.
- **Method**: `contextMenuEvent` or `createStandardContextMenu`.
- **Logic**:
    - Update `show_context_menu` method.
    - Change order of adding actions (first Env, then Copy).
    - Add "Add new..." item to variables menu.
    - Emit `variable_set_requested` signal with a special key value (e.g., `None` or a special flag) for creating a new variable, or handle this inside `MainWindow`.
    - *Clarification*: It is better if `ResponseView` just emits a signal "want to set variable", and `MainWindow` figures out if it's new or old. Or `ResponseView` can request the new variable name itself?
    - *Decision*: `ResponseView` is responsible only for display. If "New Variable..." is selected, it emits a signal, e.g., `variable_set_requested(None, value)` or `create_variable_requested(value)`.
    - Let's extend the contract `variable_set_requested(key, value)`. If `key` is `None`, it means a request to create a new one.

- **Component**: `MainWindow`.
- **Logic**:
    - Signal handling: if `key` is `None`, show `QInputDialog` to enter variable name.
    - Variable name validation.
    - Creation/Update of variable in `Environment`.
    - Saving and broadcasting updates.

## Q&A
- **Q:** What if no environment is selected?
- **A:** The "Set env" item should be hidden or disabled.
