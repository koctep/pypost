# PYPOST-1284 Decomposition Notes: Variable Setup Wizard with Rich Help Guidance

## Epic Overview

**Epic Key**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)  
**Summary**: Add variable setup wizard with rich help guidance when adding MCP server from library  
**Sprint**: 2029 (MCP Variable Setup Wizard)

### Problem Statement

When configuring or adding an MCP server from a library collection in PyPost, users often struggle to configure required environment variables without instructions. Complex credentials (such as Google Drive OAuth access tokens or Jira API credentials) require step-by-step guidance on how to generate and obtain them.

Currently:
1. `CollectionVariable` model supports `name`, `type`, `default`, `description`, `required`, and `secret`, but lacks rich guidance fields (e.g. `help_text` or detailed instructions / step-by-step guidance).
2. When selecting a connected library collection in `_McpServerEditor`, variable inputs are presented in a basic vertical form layout (`_library_variables`) without structured wizard steps, expandable help guidance panels, secret toggles, or clear required validation indicators.
3. Example library collections (such as `examples/collections/google_drive.json`) only provide basic single-line `description` strings rather than actionable step-by-step setup guides for obtaining tokens.

## Scope Breakdown and Slicing Strategy

To deliver the epic without monolithic changes and keeping all child stories strictly sized to ≤ 5 Story Points, the epic is decomposed into four focused, independently deliverable child stories:

| Child Key | Provisional ID | Summary | SP | Dependencies | Focus Area | Sprint |
| --- | --- | --- | --- | --- | --- | --- |
| [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) | **WIZARD-1** | Extend `CollectionVariable` model and schemas with rich help guidance support | 3 SP | None | Core model & schema validation | Sprint 2029 |
| [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) | **WIZARD-2** | Implement variable setup wizard dialog with expandable guidance panels | 5 SP | PYPOST-1372 | UI Wizard / dialog component & guidance rendering | Sprint 2029 |
| [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) | **WIZARD-3** | Integrate variable setup wizard into MCP server configuration dialog | 5 SP | PYPOST-1373 | Workflow integration, pre-populating defaults, secret masking & saving | Sprint 2029 |
| [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) | **WIZARD-4** | Add sample help guidance to reference library collections & comprehensive test suite | 3 SP | PYPOST-1372, PYPOST-1373, PYPOST-1374 | Reference fixtures, docs & integration / contract tests | Sprint 2029 |

Total Estimated Effort: 16 SP (4 stories, each ≤ 5 SP, assigned to active Sprint 2029 under epic PYPOST-1284).

---

### Detailed Slice Descriptions

#### WIZARD-1 -> PYPOST-1372: Extend CollectionVariable model and schemas with rich help guidance support
- **Issue Key**: [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Scope**:
  - Update `CollectionVariable` (in `pypost/models/collection_variable.py`) and schema serialization to support `help_text` (or rich markdown/text instructions) and optional guidance attributes (such as external doc URL or step-by-step hints).
  - Ensure backwards compatibility with collections that omit guidance fields.
  - Update library manifest models (`pypost/models/library_manifest.py`) and collection serializers/parsers if necessary.
  - Unit tests covering model validation, default values, serialization, and round-trips.
- **Estimated Story Points**: 3 SP
- **Primary Deliverables**: `pypost/models/collection_variable.py`, serialization tests, unit tests.

#### WIZARD-2 -> PYPOST-1373: Implement variable setup wizard dialog with expandable guidance panels
- **Issue Key**: [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373)
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Scope**:
  - Create a dedicated Variable Setup Wizard dialog or reusable component (e.g. `pypost/ui/dialogs/variable_setup_wizard_dialog.py` or wizard widget).
  - Provide an intuitive variable configuration workflow with expandable/collapsible guidance cards or help panels displaying rich step-by-step instructions.
  - Support secret masking with show/hide toggle, input type validation, required indicators, and profile selection if applicable.
  - Unit and UI tests for wizard state, panel expansion, validation feedback, and cancel/apply signals.
- **Estimated Story Points**: 5 SP
- **Primary Deliverables**: Wizard UI classes, widget tests, interaction tests.

#### WIZARD-3 -> PYPOST-1374: Integrate variable setup wizard into MCP server configuration dialog
- **Issue Key**: [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374)
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Scope**:
  - Connect the Variable Setup Wizard to `McpServersDialog` / `_McpServerEditor` when configuring a library collection MCP server.
  - Support launching the wizard upon collection selection or via an explicit "Configure Variables / Setup Wizard" action.
  - Pre-populate variable values from existing configuration overlays/profiles.
  - Validate required fields before allowing server save, and cleanly map wizard outputs into the MCP server configuration and environment overlays.
  - UI regression and integration tests ensuring seamless flow in `_McpServerEditor`.
- **Estimated Story Points**: 5 SP
- **Primary Deliverables**: `pypost/ui/dialogs/mcp_servers_dialog.py`, presenter/editor integration, integration tests.

#### WIZARD-4 -> PYPOST-1375: Add sample help guidance to reference library collections & comprehensive test suite
- **Issue Key**: [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Scope**:
  - Enrich example library collections (notably `examples/collections/google_drive.json` and any Jira / sample collections) with realistic, step-by-step guidance on obtaining credentials (e.g., Google Cloud Console OAuth setup, scopes, token generation).
  - Add end-to-end and contract tests verifying that rich guidance flows from collection files through the wizard and into active server configurations.
  - Provide developer documentation on how collection authors can specify rich guidance for library variables.
- **Estimated Story Points**: 3 SP
- **Primary Deliverables**: Example collections, `doc/dev/` guides, automated tests.

---

## Sprint Alignment

All child tasks must be added to **Sprint 2029** ("MCP Variable Setup Wizard") upon creation in Jira during the decomposition execution.

---

## Architectural Refinements and Contracts (Step 2 Alignment)

From the architectural analysis performed in `ai-tasks/PYPOST-1368/20-architecture.md`, the following refinements are established for implementation:

1. **Model Evolution Strategy (`CollectionVariable.help_text`)**:
   - `help_text` will be typed as `str = ""` with default empty string to ensure zero schema friction with existing collections.
   - Rich formatting (Markdown / HTML) will be supported for instructional text, code snippets, and credential console URLs.

2. **UI Component Architecture**:
   - A dedicated `VariableSetupWizardDialog` will be implemented in `pypost/ui/dialogs/variable_setup_wizard_dialog.py`.
   - Each variable will be presented via a self-contained `VariableGuidanceCard` component supporting:
     - Name and requirement badge (`* Required`).
     - Input field with validation indicator.
     - Eye toggle button (`QToolButton`) for masking/unmasking secret credentials.
     - Expandable/collapsible frame for rich step-by-step guidance.
   - Prevents further bloat of `mcp_servers_dialog.py` (which currently exceeds 1,200 LOC).

3. **Editor Integration & Overlay Persistence**:
   - A `"Configure Variables in Wizard..."` action will be integrated into `_McpServerEditor`.
   - On completion, values are segregated into `LocalLibraryOverlay["overrides"]` and `LocalLibraryOverlay["secrets"]`.

4. **Reference Implementation**:
   - `examples/collections/google_drive.json` will serve as the canonical reference demonstrating multi-step Google Cloud OAuth setup instructions for `google_drive_access_token`.

