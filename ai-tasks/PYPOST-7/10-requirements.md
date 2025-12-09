# Requirements: PYPOST-7 Open Current Environment in Editor

## 1. Description
When the user clicks the "Manage" button to edit environments, the "Manage Environments" dialog should open with the currently selected environment pre-selected in the list.

## 2. Language
Python (PySide6)

## 3. Functional Requirements
1. **Identify Current Environment**:
   - The system must identify which environment is currently selected in the main window's environment dropdown.
2. **Pass Context to Dialog**:
   - The "Manage Environments" dialog must accept the name (or ID) of the current environment when initialized.
3. **Select Environment in Dialog**:
   - When the dialog opens, it must automatically select the row corresponding to the passed environment name in the environment list.
   - If "No Environment" is selected in the main window, the dialog should retain its default behavior (selecting the first item or none).
   - If the passed environment is not found in the list (edge case), the dialog should default to the first item.

## 4. Non-Functional Requirements
- **Usability**: Improves user workflow by reducing clicks/search time.
- **Responsiveness**: The selection should happen immediately upon dialog opening.

## 5. Scope
- Modification of `pypost/ui/main_window.py` (method `open_env_manager`).
- Modification of `pypost/ui/dialogs/env_dialog.py` (`__init__` and/or `load_list`).

## 6. User Stories
- As a user working in "Dev" environment, when I click "Manage", I want the "Dev" environment to be selected in the list so I can immediately edit its variables.

