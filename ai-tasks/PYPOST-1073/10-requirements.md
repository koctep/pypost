# PYPOST-1073: Manage Environments — Display Current Environment Variables on Open

## Goals

When an API developer or QA engineer works with PyPost, environments allow managing base URLs, authentication tokens, headers, and other variables across staging, production, or local test servers.

When opening the **Manage Environments** dialog from the main window (via the "Manage" button or keyboard shortcut), the user expects to immediately see and edit the variables belonging to the currently active environment.

Currently, when the dialog opens, the list on the left highlights the current environment, but the right-hand variables table remains blank or uninitialized until the user explicitly re-clicks an item in the list. This creates confusion, makes the application appear unresponsive or broken, and leads users to fear that their environment variables were lost.

The business goal of this task is to:
1. Ensure that upon opening the Manage Environments dialog, the variables and settings of the currently selected environment are immediately loaded and visible in the variables table.
2. Ensure consistent state handling across all opening conditions, including when an environment is actively selected, when "No Environment" is selected, when the list of environments is empty, and when switching between environments.
3. Establish robust regression test coverage for these user scenarios to prevent future UX regressions.

**Implementation language**: Python (within the existing PySide6 / Qt Python desktop client; no new stack introduced).

## User Stories

- **US-1**: As a developer using PyPost with an active environment selected, when I open the Manage Environments dialog, I want the variables table and MCP settings on the right to immediately display the active environment's variables without requiring me to re-click the environment in the list.
- **US-2**: As a user opening Manage Environments when "No Environment" is selected in the top bar, I want the dialog to handle this gracefully (e.g. selecting the default/first available environment or displaying a clear empty state) without crashing or displaying invalid data.
- **US-3**: As a user managing multiple environments, when I switch between environments in the list inside the dialog, I want the variables table to immediately and accurately update to reflect the newly selected environment's variables and configuration.
- **US-4**: As a developer maintaining PyPost, I want automated regression tests that exercise the Manage Environments opening and switching flows, so that any future changes to presenters or widgets will not break variable display on dialog open.

## Definition of Done

- When `EnvironmentDialog` is opened with an active environment name:
  - The left list highlights that environment.
  - The right variables table immediately populates with all variables of that environment.
  - The MCP checkbox correctly reflects the environment's `enable_mcp` setting.
- When `EnvironmentDialog` is opened with no environment selected (`None` / "No Environment"):
  - If environments exist, the dialog consistently handles the initial selection and displays the corresponding variables (or clean empty state if appropriate).
  - If no environments exist, the dialog displays empty state gracefully without errors, disabling variable edits until an environment is added.
- Switching selection between environments in the list updates the variables table and MCP checkbox immediately and accurately.
- Adding, renaming, or deleting environments inside the dialog preserves correct variable synchronization and selection state.
- Automated regression tests are added to verify the user scenarios (initial open with selected environment, initial open with no environment, switching between environments).
- Tests follow project standards: fast, hermetic, explicit pytest timeout marks.
- All existing tests pass and lint checks (`make lint`) succeed.

## Task Description

In PyPost, environment management is split into an environment presenter (`EnvPresenter`), the modal dialog (`EnvironmentDialog`), the list widget (`EnvironmentListWidget`), and the variables table widget (`EnvironmentVariablesWidget`).

When opening the dialog, the active environment name is passed to the dialog. However, the initial synchronization between the list selection and the variable table display does not trigger the loading of the variables into the table on initial open.

This task resolves this gap by ensuring that the selected environment's state is properly propagated to the variable table upon dialog initialization and selection changes.

### Scope

- **In Scope**:
  - Initial synchronization of the active environment's variables and settings when opening the Manage Environments dialog.
  - Handling of all initial selection states: active environment specified, "No Environment" selected, and empty environment list.
  - Verification of environment switching, creation, and deletion synchronization inside the dialog.
  - Adding automated regression tests for these user scenarios.

- **Out of Scope**:
  - Changing the storage schema or serialization format for environments.
  - Modifying encryption mechanisms or key management.
  - Redesigning the layout or styling of the environment dialog.
  - Changes to other unrelated dialogs or collection managers.

## Functional Requirements

- **FR-1 (Initial Variable Display)**: When the Manage Environments dialog is opened with a specified active environment, the dialog must immediately populate the variables table with that environment's keys and values, and set the MCP checkbox to match `enable_mcp`.
- **FR-2 (Fallback Selection)**: When the dialog is opened without a pre-selected environment (or if the specified environment is not found in the list):
  - If the environment list is non-empty, the first environment is selected and its variables are displayed.
  - If the environment list is empty, the variable table and MCP checkbox remain cleared and disabled.
- **FR-3 (Reactive Environment Switching)**: Whenever the user changes the selected row in the environment list, the variables table and MCP checkbox must immediately reload with the newly selected environment's data.
- **FR-4 (State Preservation during Dialog Actions)**: Adding, renaming, importing, or deleting environments must properly refresh the selection and update the variables table accordingly.

## Non-Functional Requirements

- **NFR-1 (Usability & Responsiveness)**: The dialog must open immediately without noticeable lag or flicker when populating environment variables.
- **NFR-2 (Testability & Reliability)**: All user scenarios must be verifiable via automated unit and integration tests without opening blocking GUI windows or requiring real human interaction.
- **NFR-3 (Safety & Code Quality)**: Changes must adhere to PEP 8, maintain strict typing, declare pytest timeouts on all tests, and avoid regression in existing presenter or storage logic.

## Main Entities

- **Environment**: Business entity representing a named set of key-value variables, hidden keys, and MCP server configuration.
- **Environment Manager Dialog**: The modal interface allowing users to view, create, edit, import, export, and delete environments.
- **Environment List**: Left-pane component presenting available environments and handling row selection.
- **Environment Variables Table**: Right-pane component displaying variable names, values, mask toggles, and MCP enablement for the selected environment.
- **Environment Presenter**: Presentation layer coordinating main-window environment selection, storage persistence, and opening the manager dialog.

## User Scenarios

### Scenario 1: Opening Manage Environments with an Active Environment
1. User selects environment "Staging" (which has 3 variables: `BASE_URL`, `API_KEY`, `TIMEOUT`) in the main window top bar.
2. User clicks the "Manage" button.
3. The Manage Environments dialog opens.
4. **Expected**: "Staging" is highlighted in the left list, and the 3 variables (`BASE_URL`, `API_KEY`, `TIMEOUT`) are immediately displayed in the right variables table.

### Scenario 2: Opening Manage Environments with "No Environment"
1. User has "No Environment" selected in the top bar.
2. User clicks the "Manage" button.
3. The Manage Environments dialog opens.
4. **Expected**: The dialog opens cleanly; if environments exist, the first environment is selected and displayed, or if no environments exist, the table is empty and controls are disabled.

### Scenario 3: Switching Environments Inside the Dialog
1. User opens the Manage Environments dialog.
2. User clicks on "Production" in the left list, then clicks on "Development".
3. **Expected**: The variables table immediately updates to show "Production" variables, then immediately updates to show "Development" variables.

### Scenario 4: Creating a New Environment Inside the Dialog
1. User clicks the "Add" button in the dialog and enters "Local".
2. **Expected**: "Local" is added to the list, selected, and an empty variable table with a new row is presented for editing.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this considered a functional bug rather than a feature request? | The dialog is designed to show and edit the selected environment. Highlighting an item on the left while leaving the right panel empty is a defect in state synchronization that harms user experience and creates confusion about data loss. |
| Should opening the dialog modify the currently active environment in the main window? | No. Changes made in the dialog take effect only upon completing or interacting with the dialog as per existing application lifecycle. |
| How should "No Environment" be handled when opening the dialog? | If environments exist in the workspace, selecting the first environment in the list ensures the user immediately sees a working environment. If no environments exist, the table remains empty and disabled until an environment is added. |
| What automated tests are required? | Regression tests for `EnvironmentDialog` and `EnvPresenter` verifying that opening with a current environment loads variables immediately, opening without an environment handles state safely, and switching selection loads corresponding variables. |
