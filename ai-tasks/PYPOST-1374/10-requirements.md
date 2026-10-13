# PYPOST-1374: [PYPOST-1284] Integrate variable setup wizard launch and overlay persistence in MCP server editor

## Goals

When users add or configure an MCP server originating from a library collection in PyPost, configuring the required environment variables is currently cumbersome and lacks guidance. Complex credentials (such as Google Cloud OAuth access tokens, personal access tokens, or external API keys) require clear, step-by-step instructions and secure entry.

In earlier layers of epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284):
- [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) (Layer 1) extended the `CollectionVariable` model with rich `help_text` guidance.
- [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) (Layer 2) created the reusable `VariableGuidanceCard` and `VariableSetupWizardDialog` modal.

However, the MCP server editor dialog does not yet integrate this wizard. Instead, it relies on a raw form layout that provides flat input fields, hides descriptions behind tooltips, and offers no expandable guidance or secret reveal toggles.

This task ([PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374), Layer 3 / WIZARD-3) connects the wizard into the MCP server configuration dialog and wires configured variable values into `LocalLibraryOverlay` persistence.

**Business Goal:**
Provide users configuring an MCP server from a library collection with an accessible, guided setup experience by offering a prominent "Configure Variables..." action (and optional automatic guidance prompt) in the MCP server editor. User configurations entered via the wizard—including masked secrets and non-secret overrides—are validated and cleanly persisted into the local library overlay upon saving the server configuration, without regressing any existing MCP server management workflows.

## Programming Language

- **Implementation language**: Python (PySide6 / Qt UI editor integration, dialog lifecycle, overlay persistence, and automated Qt test fixtures).

## User Stories

- As a **PyPost user adding an MCP server from a library collection**, I want a clearly visible button to launch the Variable Setup Wizard so that I can view detailed step-by-step guidance and configure all required variables in a focused dialog.
- As a **user selecting a collection with variables for the first time**, I want the option to be guided through variable setup so that I do not miss mandatory configuration steps before attempting to start the server.
- As a **user re-editing an existing MCP server**, I want the wizard pre-populated with my previously saved overlay values and profile defaults, so that I can inspect and update variables without re-entering values from scratch.
- As a **security-conscious user**, I want secret credentials (passwords, tokens) to remain masked and be persisted securely into the `secrets` partition of the local library overlay, while non-secret settings are persisted as `overrides`.
- As a **developer maintaining PyPost**, I want the wizard launch and overlay persistence to integrate cleanly into the server editor without breaking non-library MCP server workflows (such as workspace collections or proxy servers).

## Definition of Done

This task is considered complete when:

1. **Wizard Launch Integration (FR-1 & FR-2)**:
   - A dedicated "Configure Variables..." button is provided in the MCP server editor when a library collection that defines variables is active.
   - When selecting a library collection with variables or when creating a new library MCP server, the editor enables easy access to the wizard (either via button click or automatic prompt when unconfigured required variables exist).
   - If the selected collection defines no variables, the wizard action is disabled or hidden appropriately.
2. **Pre-population & Dialog Flow (FR-3)**:
   - Clicking "Configure Variables..." instantiates and executes the variable setup wizard dialog, populated with the collection's variable definitions.
   - Initial values passed to the wizard reflect active local library overlay overrides/secrets or the active profile defaults.
3. **Overlay Persistence & Handoff (FR-4)**:
   - Accepting the wizard updates the server editor's internal overlay state, separating configured values into `overrides` and `secrets`.
   - The inline editor fields and labels reflect the updated values.
   - When the MCP server is saved, the updated overlay candidate is handed off and persisted to disk via the overlay manager.
4. **Secret Variable Handling (FR-5)**:
   - Secret variables are strictly segregated into the `secrets` partition of the local library overlay.
   - Secret values are masked in the editor and wizard, and are never logged or exposed in plain text error messages.
5. **Quality Gates & Non-Functional Compliance**:
   - PySide6 compatibility and headless testability without hanging or blocking dialogs.
   - Zero regression across all existing MCP servers dialog workflows (workspace collections, proxy servers, built-in collections, server lifecycle operations).
   - Full test coverage for wizard launch, value pre-population, cancellation, acceptance, and overlay persistence.
   - All quality gates pass (`make verify-ai-tasks`, `make lint`, `make typecheck`, `make test`).

## Task Description

### Problem Statement

In the MCP server editor, library variables are currently rendered in a flat form layout without interactive guidance:
- Long setup instructions (`help_text`) introduced in PYPOST-1372 cannot be displayed effectively in a flat form layout.
- Users have no dedicated wizard experience (implemented in PYPOST-1373) to step through variables with interactive validation.
- While basic packaging of variables into overrides and secrets exists, there is no direct link between the new variable setup wizard and the editor's overlay lifecycle.
- When a user selects a collection with required variables, there is no guided prompt encouraging them to configure required credentials before proceeding.

### Scope

- **In Scope**:
  - Enhancing the MCP server editor in the server management dialog:
    - Adding a "Configure Variables..." button alongside or within the library variables section.
    - Providing automatic wizard prompting or clear visual cues when selecting a library collection with variables.
    - Converting manifest dictionary variables to variable models when invoking the wizard dialog.
    - Passing existing overlay values (`overrides`, `secrets`, active profile defaults) into the wizard.
    - Handling wizard dialog acceptance by synchronizing results into the editor's overlay state and inline form fields.
    - Handling wizard dialog rejection/cancellation without discarding existing saved configuration.
    - Ensuring persisted overlay handoff upon saving the server configuration.
  - Adding stable widget identifiers for automated UI tests.
  - Automated tests covering:
    - Button presence and state when library collection has/lacks variables.
    - Wizard launch, pre-population of existing values, and cancellation.
    - Wizard acceptance updating overlay state, overrides, and secrets.
    - Persistence flow to the local library overlay upon saving the server.
    - Preservation of secrets and masking.

- **Out of Scope**:
  - Modifying the core `CollectionVariable` data model (completed in **PYPOST-1372**).
  - Modifying the internal presentation logic or widgets of `VariableSetupWizardDialog` and `VariableGuidanceCard` (completed in **PYPOST-1373**).
  - Authoring sample collection guidance in `examples/collections/google_drive.json` (scoped to **PYPOST-1375** / Layer 4).
  - Modifying workspace collection or upstream proxy server workflows.

### Functional Requirements

- **FR-1: Editor "Configure Variables..." Action Button**:
  - In the MCP server editor, when the collection source is a library collection and the selected collection defines variables, provide a clearly labeled action button (e.g. `"Configure Variables..."` or `"Setup Variables in Wizard..."`).
  - The button must be visible and enabled when variables exist for the selected collection.
  - If the selected collection defines no variables or a non-library source is selected, the button must be hidden or disabled.
- **FR-2: Guided Wizard Prompt on Collection Selection**:
  - When the user selects or switches to a library collection defining required variables in the editor, the editor facilitates launching the wizard (via prominent action or prompt) so that the user is guided to complete required variables.
- **FR-3: Wizard Invocation and Value Pre-population**:
  - When the wizard action is triggered, the editor opens the variable setup wizard dialog with:
    - The collection's variables converted into variable models.
    - Initial values pre-populated from the union of current draft overlay values (`overrides` and `secrets`) and the active profile's default values.
    - The collection's display name passed for window title / header context.
  - If the user cancels the wizard, the dialog closes and any previous editor values remain unchanged.
- **FR-4: Overlay Persistence upon Wizard Acceptance**:
  - When the wizard is accepted, the editor extracts configured variables.
  - The editor updates its internal overlay draft, partitioning values into `overrides` and `secrets`.
  - Inline input fields in the editor are synchronized with the wizard's configured values.
  - When the user saves the MCP server configuration, the updated overlay candidate is handed off and persisted to disk via the overlay manager.
- **FR-5: Secret Variable Segregation and Masking**:
  - Variables declared as secrets must be strictly saved into the `secrets` partition of the local library overlay (and never into `overrides`).
  - Non-secret variables must be saved into the `overrides` partition.
  - Secret values must remain masked in all editor controls (password display mode) and must not be exposed in log messages, debug outputs, or plaintext error dialogs.

### Non-Functional Requirements

- **NFR-1 PySide6 / Qt Compliance**: Follow PyPost Qt idioms, ensuring proper parent-child hierarchy, layout management, and clean memory handling.
- **NFR-2 Headless Testability**: The wizard launch, user interactions, acceptance, and persistence must be fully testable in headless automated environments (using standard Qt event processing without hanging modals).
- **NFR-3 Zero Regression**: Existing workflows in the server management dialog—including workspace collection MCP servers, proxy servers, built-in servers, server start/stop/remove operations, and dirty state warnings—must continue to operate without regression.
- **NFR-4 Performance & Responsiveness**: Launching the wizard and synchronizing values back to the editor must occur instantaneously with zero perceptible UI latency.

### Constraints and Assumptions

- `VariableSetupWizardDialog` is available from the UI wizard package.
- `CollectionVariable` is available from the models package.
- `LocalLibraryOverlay` is available from the library manifest package.
- The server editor maintains draft overlay settings and handles packaging overlay candidates for persistence.
- Saving library servers delegates to settings controller and overlay manager persistence.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **_McpServerEditor** | The primary configuration dialog for creating and editing MCP server configurations in PyPost. |
| **VariableSetupWizardDialog** | Modal dialog hosting interactive variable cards with expandable help guidance and secret masking. |
| **CollectionVariable** | Data model declaring a variable's name, type, default, required flag, secret flag, and `help_text`. |
| **LocalLibraryOverlay** | Persisted user-specific model storing active profile, secret credentials, and non-secret overrides for a library collection. |
| **Draft Overlay State** | In-memory draft dictionary tracking overlay settings in the editor before persistence. |

## Q&A

- **Q: Does the wizard replace the existing inline variables form or complement it?**  
  **A:** The wizard complements the inline form. Users can use the inline fields for quick checks, while the "Configure Variables..." button opens the rich wizard with expandable step-by-step guidance. On wizard acceptance, both inline fields and the overlay draft are synchronized.
- **Q: How are secret variables distinguished from non-secret variables?**  
  **A:** The variable model's secret flag determines secret status. Wizard results partition variables so that secrets are stored into the overlay `secrets` partition and non-secrets into `overrides`.
- **Q: How does persistence happen?**  
  **A:** When the wizard is accepted, the editor updates its internal overlay draft. When the user clicks "Save" in the editor, the overlay candidate is packaged and persisted to disk via the settings controller and local overlay manager.
- **Q: What happens if the wizard is cancelled?**  
  **A:** No changes are applied to the overlay draft or inline fields; previous values are preserved.
