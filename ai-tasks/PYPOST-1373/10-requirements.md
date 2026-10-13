# PYPOST-1373: [PYPOST-1284] Implement VariableSetupWizardDialog and expandable VariableGuidanceCard component

## Goals

When users add or configure an MCP server originating from a collection library in PyPost, configuring the required environment variables is often complex and error-prone. Many integrations require sensitive credentials—such as Google Cloud OAuth access tokens, personal access tokens, or API secrets—which demand step-by-step instructions to acquire.

While [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) (WIZARD-1) extended the `CollectionVariable` model with a rich `help_text` guidance attribute, the application currently lacks dedicated UI components to present this guidance. Existing variable editing forms rely on flat layouts with brief tooltips, offering no expandable guidance panels, secret masking toggles, or contextual validation.

This task ([PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373), WIZARD-2) represents Layer 2 of the [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) epic decomposition defined in [PYPOST-1368](https://pypost.atlassian.net/browse/PYPOST-1368).

**Business Goal:**
Deliver an intuitive, guided variable setup experience by creating a reusable `VariableGuidanceCard` component and a dedicated `VariableSetupWizardDialog` modal. The components provide step-by-step guidance via expandable panels, pre-populate default or existing values, offer secret masking with visibility toggles, and enforce required variable validation before allowing users to proceed.

## Programming Language

- **Implementation language**: Python (PySide6 / Qt UI components, dialogs, validation logic, and automated Qt test fixtures).

## User Stories

- As a **PyPost user**, I want to view clear, expandable step-by-step guidance for collection variables so that I can follow credential generation instructions directly within the app without switching back and forth to external documentation.
- As a **security-conscious user**, I want secret variables to be masked by default with an eye toggle to reveal or hide the text, so that I can inspect entered credentials without risking accidental shoulder-surfing.
- As a **user configuring an MCP server**, I want default values pre-populated and required fields highlighted, so that I can quickly understand what values are needed and avoid configuration errors.
- As a **developer integrating library dialogs (PYPOST-1374 / WIZARD-3)**, I want a clean, modal dialog (`VariableSetupWizardDialog`) accepting a list of `CollectionVariable` objects and initial values, and returning resolved variable mappings on acceptance, so that the editor can easily launch and process wizard results.

## Definition of Done

This task is considered complete when:

1. `VariableGuidanceCard` is implemented as a reusable Qt widget displaying:
   - Variable name, type badge/label, and required status indicator.
   - Appropriate input control initialized with pre-populated values or defaults.
   - Secret masking toggle (eye button) that switches input between masked (password) and plain text for secret variables.
   - Expandable guidance panel toggled via an expand/collapse action (e.g. "Show Guidance" / "Hide Guidance"), cleanly rendering rich `help_text` with clickable links and formatted instructions when present.
   - Compact display when `help_text` is absent or empty (guidance toggle hidden or disabled).
2. `VariableSetupWizardDialog` is implemented as a PySide6 modal dialog displaying:
   - Header with clear explanatory context.
   - Scrollable container holding `VariableGuidanceCard` instances for each variable in the collection.
   - Real-time or submit-time validation verifying all required variables are supplied.
   - Standard action buttons: Cancel (reject) and Save/Finish/Apply (accept).
   - Dialog state management preventing acceptance if required variables are empty or invalid.
3. Result extraction: The dialog exposes a clean method/property (e.g. `get_values()`) returning the resolved dictionary mapping variable names to user-configured values (or separating overrides and secrets as required by downstream callers).
4. Unit and UI tests verify:
   - Card rendering, label display, and requirement indicators.
   - Secret masking and eye toggle behavior.
   - Guidance panel expansion and collapse transitions.
   - Dialog initialization with variables and pre-populated values.
   - Validation failures when required fields are empty and successful acceptance when valid.
   - Value extraction matching user input.
5. Quality gates (`make check`, `make lint`, `make verify-ai-tasks`) pass cleanly without regressions.

## Task Description

### Problem Statement

Configuring MCP collection variables currently lacks:
- An expandable container for displaying multi-line setup instructions (`help_text`).
- Clear visual indicators for required variables versus optional variables.
- Secret masking toggles for password/token fields.
- A dedicated wizard modal to guide users through initial setup before saving an MCP server.

### Scope

- **In Scope**:
  - `VariableGuidanceCard`:
    - Reusable UI component (e.g. in `pypost/ui/widgets/` or `pypost/ui/dialogs/`).
    - Configured using `CollectionVariable` instances.
    - Input control (`QLineEdit` or type-appropriate input) pre-populated from defaults or caller-provided values.
    - Password echo mode and reveal/hide toggle for secret variables.
    - Collapsible/expandable help section with toggle button ("Show Guidance" / "Hide Guidance"), rendering formatted text/markdown cleanly.
    - Validation state feedback (required fields, empty checks).
  - `VariableSetupWizardDialog`:
    - Modal dialog (e.g. in `pypost/ui/variable_setup_wizard_dialog.py`).
    - Displays list of `VariableGuidanceCard` widgets in a scrollable area.
    - Action buttons: Cancel, Finish/Save.
    - Validation: checks required fields before accepting.
    - Method to extract resolved values (`get_values()`).
  - Automated tests:
    - Qt test fixture tests covering widget interactions, state toggles, validation, and dialog lifecycle.

- **Out of Scope**:
  - Direct integration into `pypost/ui/dialogs/mcp_servers_dialog.py` (`_McpServerEditor`) and overlay persistence into `LocalLibraryOverlay` (scoped to **PYPOST-1374** / WIZARD-3).
  - Modifying `examples/collections/google_drive.json` or authoring collection-specific documentation (scoped to **PYPOST-1375** / WIZARD-4).
  - Modifying the underlying `CollectionVariable` model schema (completed in **PYPOST-1372** / WIZARD-1).

### Functional Requirements

- **FR-1 Reusable VariableGuidanceCard Component**:
  - Renders variable name, type label (e.g., string, integer, boolean), and required status badge (e.g., `* Required` or visual badge).
  - Provides an input field initialized with pre-populated values or fallback default values from the `CollectionVariable`.
  - Reflects validation status (e.g. visual cues for required fields that are blank).
- **FR-2 Expandable Guidance Section**:
  - If `help_text` is present on the variable, provides a toggle control (e.g., "Show Guidance" / "Hide Guidance" button or disclosure arrow).
  - Displays guidance in an expandable panel using formatted rich text/markdown rendering with word wrap and support for clickable links (`setOpenExternalLinks(True)`).
  - If `help_text` is empty or None, the guidance panel and toggle are hidden or omitted to conserve screen space.
- **FR-3 Secret Masking & Pre-population**:
  - Variables marked with `secret=True` default to masked input (`QLineEdit.EchoMode.Password`).
  - Secret fields feature an eye toggle button allowing the user to unmask/mask the entered text (`QLineEdit.EchoMode.Normal` vs `EchoMode.Password`).
  - Pre-populates default values defined on `CollectionVariable.default` or passed from initial values dictionary.
- **FR-4 VariableSetupWizardDialog Presentation & Validation**:
  - Modal dialog presenting `VariableGuidanceCard` instances for an ordered collection of variables inside a scrollable layout.
  - Action buttons: Cancel (`reject()`) and Save/Finish (`accept()`).
  - Validation: when user triggers Save/Finish, validates that all required variables have non-empty inputs. If any required variable is empty, blocks acceptance and visually highlights missing required fields.
- **FR-5 Result Extraction**:
  - Provides a public method or property (e.g., `get_values() -> dict[str, Any]`) returning a dictionary of variable names mapped to their configured string or parsed values.

### Non-Functional Requirements

- **NFR-1 PySide6 / Qt Standards**: Follow PyPost UI patterns and conventions (proper parent widget passing, layout management, dark/light theme compatibility, and clean widget cleanup).
- **NFR-2 Testability**: Designed for headless Qt testing via `pytest-qt` or standard Qt test fixtures without hanging dialog execution.
- **NFR-3 Modularity & Separation of Concerns**: Clean separation between card widget presentation, dialog flow management, and data extraction.
- **NFR-4 Usability & Accessibility**: Clear typographic hierarchy, responsive layout that scrolls smoothly when many variables are configured, and intuitive keyboard navigation (Tab/Shift-Tab, Enter/Escape).

### Constraints and Assumptions

- Works with PySide6 widgets (`QDialog`, `QFrame`, `QLineEdit`, `QToolButton`, `QScrollArea`, `QVBoxLayout`, `QLabel`, `QPushButton`, `QDialogButtonBox`).
- Integrates with `CollectionVariable` model updated in PYPOST-1372 (`pypost/models/collection_variable.py`), which provides `name`, `type`, `default`, `description`, `help_text`, `required`, and `secret`.
- Initial values may be passed as a dictionary `dict[str, Any]` representing existing overrides or secrets from active configurations.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **CollectionVariable** | Schema definition representing a configurable environment variable with metadata (`name`, `type`, `default`, `required`, `secret`, `help_text`). |
| **VariableGuidanceCard** | Reusable widget representing an individual variable input row with masking toggle, validation indicators, and collapsible rich help panel. |
| **VariableSetupWizardDialog** | Modal dialog hosting a sequence of guidance cards for an MCP collection, validating inputs, and returning resolved configurations. |
| **Resolved Variables Mapping** | Key-value dictionary mapping variable names to user-entered configuration values. |

## Q&A

- **Q: How does `VariableGuidanceCard` handle non-string variables (e.g., boolean or integer)?**  
  **A:** While string variables and secret tokens are the most common, integer/number or boolean inputs can use text inputs with type validation or standard Qt input controls, with strings converted or validated according to `CollectionVariable.type`.
- **Q: Where should the new UI components live in the codebase?**  
  **A:** `VariableSetupWizardDialog` belongs in `pypost/ui/variable_setup_wizard_dialog.py`. `VariableGuidanceCard` can either reside alongside the dialog in `pypost/ui/variable_setup_wizard_dialog.py` or as a reusable component in `pypost/ui/widgets/variable_guidance_card.py` (to be determined during Step 2 Architecture).
- **Q: Does this task wire the dialog into `McpServersDialog`?**  
  **A:** No. Connecting the wizard to `McpServersDialog` / `_McpServerEditor` and persisting into `LocalLibraryOverlay` is explicitly scoped to child task PYPOST-1374 (WIZARD-3). This separation ensures PYPOST-1373 stays strictly focused on UI widget implementation, testing, and validation.
