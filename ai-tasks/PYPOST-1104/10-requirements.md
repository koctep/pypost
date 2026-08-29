# PYPOST-1104: Upgrade custom headers editor to key-value table widget with env variable completion

## Goals

In PyPost, users configure upstream MCP (Model Context Protocol) proxy servers to seamlessly connect AI agents and PyPost clients with external, enterprise, or cloud-hosted MCP tool and resource providers. Connecting to these upstream services typically requires custom HTTP request headers for authentication (e.g., `Authorization: Bearer <token>`, `X-API-Key: <key>`), multi-tenant routing (e.g., `X-Workspace-ID: <id>`), or client identification.

The previous MCP server editor dialog relied on a free-form, multiline plain text box where users had to manually format headers as `Key: Value` lines. This approach suffered from several significant business and usability drawbacks:
1. **High Error Rate and Silent Omission**: Free-form text allows typos, missing colons, whitespace anomalies, or malformed header keys that silently get ignored during parsing or cause upstream authentication failures during live proxy operations.
2. **Cognitive Overhead and Memory Burden**: Users had to memorize or navigate away to other dialogs to look up the exact names of environment variables (e.g. `{{ API_KEY }}`), increasing friction and leading to misspelled variable references.
3. **Absence of Inline Feedback**: Users received no immediate validation hints or syntax guidance while configuring headers. Missing variables or malformed expressions were only discovered at request time when proxy calls failed.
4. **Inconsistent User Experience**: Across other PyPost components (such as HTTP request editors and MCP client draft tabs), headers and parameters are managed through structured tabular editors with row controls and variable awareness. The plain-text headers box was an inconsistent outlier.

**Business Goal**: Modernize and streamline the MCP server custom headers editing experience by replacing the plain-text input in the MCP server editor with a structured, interactive Key-Value table widget featuring inline environment variable autocompletion (`{{ VAR }}`), real-time syntax validation hints, and dynamic environment binding. This reduces configuration errors, accelerates upstream service integration, and ensures a consistent, high-quality user experience.

**Implementation language**: Python (integrated within the existing PyPost application).

## User Stories

- **As an API developer / workspace user**, I want to enter custom HTTP headers as distinct Key and Value pairs in an interactive table with automatic row addition, so that I don't have to manually format raw text or worry about delimiter parsing issues.
- **As an engineer configuring multi-environment credentials**, I want inline autocomplete suggestions for environment variables (`{{ VAR }}`) when typing in the header value field, so that I can quickly reference variables defined in my active environment without typing them from memory or making spelling mistakes.
- **As a user editing headers**, I want immediate visual hints and feedback if a header key is invalid (e.g., contains prohibited characters or is blank while a value exists) or if a referenced variable does not exist in the selected environment, so that I can fix errors before saving the configuration.
- **As a workspace administrator switching environments**, I want the header editor's autocomplete suggestions and variable validation to update automatically when I change the target environment in the editor dialog, so that the hints always reflect the currently selected environment.
- **As an operator reviewing configurations**, I want to hover over variable placeholders in the header editor to see resolved variable values and preview what will be sent upstream, while sensitive/secret values remain appropriately masked.

## Definition of Done

- The free-form multiline text editor for custom headers in the MCP server editor is replaced with an interactive Key-Value table widget.
- Users can view, add, edit, and remove header rows in an intuitive tabular format with separate Key and Value columns.
- The table automatically manages row creation (e.g. trailing empty row for quick entry) and allows removing or clearing unused header pairs.
- Typing `{{` in the header value editor activates an inline autocomplete / suggestion list showing available environment variable names from the currently selected environment.
- Selecting an autocomplete suggestion inserts the formatted variable placeholder (e.g. `{{ VARIABLE_NAME }}`) at the cursor position.
- Real-time syntax validation hints are provided:
  - Validates that header keys conform to standard HTTP header naming conventions (non-empty token without prohibited characters like spaces or colons).
  - Validates template placeholder syntax (e.g., detecting unclosed `{{` or malformed expressions).
  - Provides visual warnings or tooltips when a referenced variable name is not present in the selected environment.
- Changing the selected environment in the dialog immediately refreshes the variable suggestions and validation status of the header table.
- Existing custom headers from saved configurations are correctly populated into the key-value table when opened for editing, and edited headers are serialized into the server configuration upon saving.
- If no custom headers are needed or entered, saving succeeds cleanly with an empty headers configuration.
- All existing MCP server workflows (adding, editing, saving, and upstream forwarding) continue to function without regression.
- Automated tests verify table interaction, environment variable autocompletion triggers, syntax validation feedback, environment change updates, and configuration round-tripping.

## Task Description

PyPost enables managing upstream MCP proxy server endpoints alongside local collection servers. This task upgrades the user interface for editing custom headers in the MCP server editor dialog, transitioning from a basic text area to an interactive key-value table with environment variable completion and syntax validation.

### Functional Scope

1. **Structured Key-Value Table Presentation**:
   - Two-column table with distinct "Key" and "Value" fields.
   - Support for populating existing headers when editing an existing configuration.
   - Dynamic row management supporting automatic row addition when editing the last empty row, as well as clearing or deleting rows.
   - Automatic trimming of header keys while preserving meaningful header values.

2. **Environment Variable Autocompletion**:
   - Activated inline upon typing `{{` within the value field.
   - Displays a filtered list of available variable names provided by the currently selected environment.
   - Supports keyboard navigation (up/down arrows, Enter/Tab to select, Escape to dismiss) for seamless, uninterrupted editing.
   - Inserts the selected variable formatted with closing delimiters (e.g., `{{ VARIABLE_NAME }}`).

3. **Syntax Validation Hints & Variable Verification**:
   - Header Key Validation: Warns if a key contains invalid HTTP header characters (such as colons, spaces, control characters) or if a value is provided without a key.
   - Template Syntax Validation: Detects unclosed template expressions (e.g., `{{ VAR` without matching `}}`) or empty placeholders.
   - Variable Existence Verification: Provides visual warning cues or informative tooltips if a referenced variable name is not defined in the selected environment.
   - Visual Clarity: Validation hints should be unobtrusive yet clearly visible, guiding the user to correct issues.

4. **Environment Context Synchronization**:
   - The table reacts dynamically to changes in the environment selector within the editor dialog.
   - When the user selects a different environment, the autocompletion candidate list and variable existence validation immediately update to reflect the newly selected environment.

5. **Data Serialization & Dialog Integration**:
   - Cleanly converts table rows into the dictionary format (`dict[str, str]`) expected by the MCP server configuration upon dialog acceptance.
   - Preserves compatibility with existing proxy server configuration loading and saving.
   - Maintains conditional visibility: custom headers table is shown only when "Upstream Proxy" server type is active.

### Boundaries and Out of Scope

- Modifying the upstream proxy network transport or server-side header dispatch logic (this was completed in PYPOST-1092).
- Creating or editing environment variables from within this dialog (environment management remains in the dedicated Environment Manager).
- Modifying headers for local collection-based MCP servers (headers are strictly an upstream proxy capability).
- Adding complex templating scripts or functions (headers support standard variable substitution).

## Non-Functional Requirements

- **Usability & Ergonomics**: Smooth keyboard navigation (Tab between cells, arrow keys and Enter/Tab for autocomplete selection).
- **Responsiveness**: Autocomplete suggestion filtering and validation hints must update instantaneously with zero perceptible UI lag.
- **Visual Consistency**: Align with existing PyPost key-value tables and dialog styling for a coherent user experience.
- **Robustness**: Malformed inputs, rapid keystrokes, or switching between empty/populated environments must never cause unhandled exceptions or UI crashes.
- **Security & Privacy**: Variable values marked as hidden/secret in the environment must remain masked during hover preview and never be exposed in plaintext logs.

## Main Entities

- **MCP Server Configuration**: The business entity representing an endpoint definition, its operational mode (proxy), target URL, transport, and associated custom headers.
- **Custom Header Entry**: A business pair comprising a standardized HTTP header field name (Key) and an associated value string (Value), which may contain zero or more dynamic variable expressions.
- **Environment Context**: The business entity representing the currently selected environment, providing the set of variable names for autocomplete suggestions and validation verification.
- **Variable Placeholder Expression**: A templated placeholder (e.g. `{{ VAR_NAME }}`) representing a value to be dynamically substituted from the environment.
- **Validation Hint State**: The business state of a header entry indicating its validity (e.g., valid, missing key, invalid header name syntax, unclosed template expression, undefined environment variable).

## User Scenarios

### Scenario 1: Adding an Authorization Header with Autocomplete
1. A user opens the MCP Server configuration dialog and selects "Upstream Proxy".
2. In the Custom Headers table, the user clicks the first row, enters `Authorization` in the Key column, and presses Tab to move to the Value column.
3. The user types `Bearer {{`. An autocomplete popup appears displaying available environment variables (e.g., `API_TOKEN`, `AUTH_KEY`).
4. The user selects `API_TOKEN` and presses Enter. The field completes to `Bearer {{ API_TOKEN }}`.
5. The validation status indicates the entry is valid. The user saves the configuration.

### Scenario 2: Environment Switch with Variable Verification
1. A user edits an existing proxy server configuration that contains a header `X-Service-Key: {{ STAGING_KEY }}`.
2. The user switches the environment selector in the dialog from "Staging" to "Production".
3. In the "Production" environment, `STAGING_KEY` does not exist.
4. The custom headers table immediately displays a visual validation hint/warning indicating that `STAGING_KEY` is not defined in the selected environment.
5. The user updates the value to `{{ PROD_KEY }}`, which autocompletes from the Production environment, clearing the warning.

### Scenario 3: Header Key Syntax Validation Hint
1. A user enters `Invalid Header Name:` in the Key column.
2. The table displays an inline syntax validation hint indicating that header keys cannot contain spaces or colons.
3. The user corrects the key to `Invalid-Header-Name`, and the validation warning disappears.

## Q&A

| Question | Answer |
| --- | --- |
| Should autocomplete trigger automatically upon typing `{{`? | Yes. Typing `{{` within the value field should trigger the autocomplete suggestion list showing environment variables, minimizing unnecessary interruptions during regular typing while providing instant access to variables. |
| Does autocomplete insert the closing braces `}}` automatically? | Yes. Selecting a variable suggestion inserts the full placeholder (e.g., `{{ VAR_NAME }}`) with closing braces if not already present. |
| Should missing environment variables prevent saving the dialog? | A missing environment variable triggers an advisory validation hint to alert the user, but does not hard-block saving, as users may plan to define or import the variable into the environment subsequently. However, structurally invalid rows (e.g., a value with an empty key or illegal key characters) should be flagged. |
| Are custom headers displayed for Local Collection MCP servers? | No. Custom headers are only applicable to upstream proxy MCP servers. When "Local Collection" is selected, the custom headers section remains hidden, matching current behavior. |
