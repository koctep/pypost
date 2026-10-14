# PYPOST-1377: [PYPOST-1312] Request model, persistence, and RequestEditor UI for hidden response fields

## Goals

Users routinely interact with APIs that return sensitive information such as authentication tokens, passwords, session identifiers, API keys, and personally identifiable information (PII). When working in team environments, during demos, screen-sharing sessions, or when exposing requests to automated AI agents via MCP tools, exposing these response fields unredacted creates severe security and privacy risks.

Parent Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) ("Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output") introduces full-lifecycle response field confidentiality into PyPost. To enable downstream presentation masking (click-to-reveal in the GUI response viewer) and fail-closed redaction (permanent masking in MCP tool agent outputs), the system must first provide the foundational ability to define, persist, duplicate, and visually edit which response fields should be hidden for each request.

This task ([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377), MASK-1) provides that core configuration and persistence foundation:
1. **Request Configuration**: Allow requests to declare an ordered list of hidden response field selectors.
2. **Collection Persistence & Compatibility**: Store configured hidden response fields alongside other request properties in saved collections, while ensuring full backward compatibility with existing saved collections that lack this configuration.
3. **Tab Isolation & Dirty Tracking**: Ensure that opening requests in isolated tabs preserves configured hidden response fields, and that dirty-state detection accurately reflects user edits to hidden field configurations.
4. **Intuitive Editor Management**: Provide an interactive, intuitive UI table in the request editor allowing users to add, view, edit, and remove hidden response field selectors.

## Programming Language

- **Implementation language**: Python (PyPost data models, persistence serializers, Qt UI components, and unit test suites).

## User Stories

- As an **API Developer / Security Engineer**, I want to configure a list of sensitive response field names or paths on any HTTP request, so that subsequent executions know which response values must be kept confidential.
- As a **PyPost Desktop User**, I want to manage hidden response field selectors directly within the request editor UI (adding, editing, and deleting entries), so that I do not need to manually edit raw JSON collection files.
- As a **Collaborating Developer**, I want my saved collections to preserve configured hidden response fields across application restarts and git commits, so that my team members automatically benefit from the same security configurations.
- As an **Existing User**, I want all my legacy collection files to load without error or schema rejection, defaulting safely to an empty hidden response field list.
- As a **Multi-Tab User**, I want isolated request tabs to carry over configured hidden response fields upon duplication, while keeping their draft edits completely isolated from other open tabs and accurately reflecting unsaved dirty states.

## Definition of Done

This task is considered complete when:

1. **Request Configuration Support**:
   - The request data model supports configuring a list of hidden response field selectors (strings).
   - Defaults to an empty list when no hidden fields are specified.
2. **Collection Persistence & Backward Compatibility**:
   - Saving a request or collection preserves configured hidden response field selectors in the collection file.
   - Existing legacy collection files and test fixtures lacking hidden response fields load cleanly without validation errors or data loss.
3. **Tab Copy Isolation & Dirty Tracking**:
   - Tab isolation deep copy preserves configured hidden response fields so isolated tabs receive independent copies of the list.
   - Dirty-state checking detects modifications to the hidden response fields list (e.g., adding, removing, or reordering selectors) and distinguishes dirty drafts from saved states.
4. **RequestEditor Configuration UI**:
   - The request editor provides a dedicated, intuitive UI section/table for configuring hidden response field selectors.
   - Users can add new field selectors, edit existing selectors in place, and delete selectors.
   - Modifications in the UI immediately update the working request draft and trigger appropriate dirty-state notifications.
5. **Automated Verification**:
   - Unit tests verify model validation, default initialization, JSON collection serialization/deserialization round-trips, tab isolation deep copy, and request editor UI interactions.
   - All repository quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) pass cleanly.

## Task Description

### Problem Statement

Currently, PyPost requests define request-side parameters (method, URL, headers, query params, auth, body), but do not have a mechanism to define response-side confidentiality rules. Users testing endpoints that emit sensitive secrets (such as JWT tokens or credentials) cannot indicate which response attributes require confidentiality.

Without request-level configuration:
- Downstream GUI response viewers cannot know which fields should be masked or revealed on demand.
- MCP tool execution wrappers cannot know which fields must be redacted before sending data to AI agents.
- There is no UI in the request editor to view or modify response confidentiality settings.

### Scope

- **In Scope**:
  - Request configuration schema extension to support a list of hidden response field selectors (defaulting to empty).
  - Persistence round-tripping in collection JSON serializers and loaders.
  - Tab isolation deep copy logic ensuring independent duplication across editor tabs.
  - Dirty-state comparison logic incorporating hidden response fields.
  - Request editor UI component providing an editable table or list to add, edit, and remove field selectors.
  - Comprehensive unit test coverage for models, persistence, copy semantics, and UI interactions.
- **Out of Scope**:
  - GUI response rendering, syntax highlighting, and click-to-reveal interactivity in `ResponseView` (addressed in **PYPOST-1379** / MASK-3).
  - MCP response sanitization and permanent agent masking execution (addressed in **PYPOST-1378** / MASK-2).
  - End-to-end integration contracts across GUI and MCP boundaries (addressed in **PYPOST-1380** / MASK-4).

### Functional Requirements

- **FR-1 Configurable Hidden Field Selectors**:
  - Every request configuration must allow specifying zero or more hidden response field selectors.
  - If omitted in input data or newly created, the list must default to an empty list (`[]`).
  - Field selectors are represented as text strings (e.g., simple field names or paths).

- **FR-2 Collection Persistence & Backward Compatibility**:
  - Serializing a request or collection to JSON must include configured hidden response fields.
  - Deserializing a collection must restore configured hidden response fields exactly as saved.
  - Deserializing collections created prior to this feature (where the field is absent) must succeed without error, setting hidden response fields to an empty list.

- **FR-3 Tab Isolation & Dirty Tracking**:
  - Duplicating a request into an isolated tab must produce an independent, decoupled copy of the hidden response fields list, such that edits in one tab do not mutate the other tab.
  - Request comparison and dirty-state detection must treat differences in hidden response fields as unsaved changes (dirty), and identical lists as clean (not dirty).

- **FR-4 RequestEditor Configuration UI**:
  - The request editor must present a clear, accessible UI section (table or list) displaying currently configured hidden response field selectors.
  - The UI must allow users to:
    - Add a new field selector entry.
    - Edit an existing field selector inline.
    - Remove an existing field selector.
  - Changes made in the UI must immediately reflect in the active request draft and emit change/dirty notifications.
  - Loading a request into the editor must populate the table with that request's configured selectors; clearing the editor must reset the table.

### Non-Functional Requirements

- **NFR-1 Backward Compatibility**: Existing user collections, workspace files, and test fixtures must load transparently without migration scripts or breaking changes.
- **NFR-2 UI Responsiveness & Usability**: Adding, editing, or deleting entries in the request editor UI must be instantaneous (< 16ms) and follow established UI styling patterns of existing request editor tabs (such as Headers or Params).
- **NFR-3 Data Integrity**: Tab duplication must be strictly isolated to prevent shared mutable list references between tabs.
- **NFR-4 Maintainability & Testability**: Every capability must be covered by automated unit tests without requiring live network calls or external dependencies.

### Main Business Entities

| Business Entity | Description |
| --- | --- |
| **Request Configuration** | The core domain entity capturing all parameters of an HTTP request, now including response confidentiality settings. |
| **Hidden Response Field Selector** | A string identifier representing a response field or key (such as `token`, `password`, `secret`) designated by the user to be hidden. |
| **Collection** | A grouped, persisted set of requests stored on disk, preserving all request settings including hidden field selectors. |
| **Isolated Request Tab** | An independent workspace tab holding a draft copy of a request, isolated from other tabs and from the persisted storage until saved. |
| **Request Editor UI** | The interactive desktop interface where users inspect and edit request parameters, now providing controls to manage hidden response fields. |

## Q&A

- **Q: Why is this configuration attached to individual requests rather than global application settings?**
  - **A:** Different API endpoints have different response payloads and security requirements. For example, an authentication endpoint (`/api/login`) returns sensitive tokens that should be masked, whereas a public catalog endpoint (`/api/products`) returns open data. Attaching the configuration to the request allows fine-grained, contextual security rules that travel with the collection.

- **Q: Does this task implement the actual masking or click-to-reveal logic?**
  - **A:** No. Per the epic decomposition (see [PYPOST-1312 Decomposition Notes](file:///home/src/ai-tasks/PYPOST-1312/decomposition-notes.md) and [Developer Docs](file:///home/src/doc/dev/hidden_response_fields.md)), this task (MASK-1) establishes the foundational data model, collection persistence, tab isolation copy, and request editor UI. Downstream tasks implement MCP permanent masking (MASK-2 / PYPOST-1378), GUI click-to-reveal (MASK-3 / PYPOST-1379), and end-to-end integration tests (MASK-4 / PYPOST-1380).

- **Q: How should legacy collections without this field be handled?**
  - **A:** They must load with 100% backward compatibility, cleanly initializing the hidden response fields list to an empty list without raising validation errors.

- **Q: What UI pattern should be used for managing hidden response fields in the editor?**
  - **A:** It should follow the established patterns in PyPost's `RequestWidget` (such as the Key-Value tables used for headers and query parameters or dedicated editor tabs), allowing users to view, add, edit, and remove selector strings conveniently.
