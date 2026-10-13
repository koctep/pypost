# PYPOST-1368: Decompose epic PYPOST-1284 into child tasks

## Goals

Epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) asks to "Add variable setup wizard with rich help guidance when adding MCP server from library". When users add or configure an MCP server originating from a collection library, configuring required environment variables is currently error-prone and unintuitive. Complex credentials—such as Google Cloud Bearer tokens or Jira API tokens—require step-by-step instructions that are not surfaced in the current flat form layout.

This story ([PYPOST-1368](https://pypost.atlassian.net/browse/PYPOST-1368)) exists to analyze and break down epic PYPOST-1284 into **implementable child Jira tasks** (each ≤ 5 Story Points), each scoped for a full Top-Down cycle (Steps 1–8), and assign them to the active sprint (**Sprint 2029: MCP Variable Setup Wizard**).

**Business Goal:** Sprint planners and developers receive clear, deliverable, and estimable work packages that together fully satisfy the parent epic's scope (data models, wizard UI, dialog integration, and reference fixtures/tests) without oversized tickets stalling sprint velocity.

## Programming Language

- **This task (PYPOST-1368):** Markdown planning artifacts and Jira issue tracking operations.
- **Child stories under PYPOST-1284:** Python (PyPost models, Qt UI dialogs, examples, and tests).

## User Stories

- As a **sprint planner**, I want epic PYPOST-1284 decomposed into well-defined child tasks with estimates ≤ 5 SP and clear acceptance criteria, so that work can be tracked and parallelized effectively in Sprint 2029.
- As a **PyPost user**, I want a guided setup wizard with expandable step-by-step instructions and secret masking when adding an MCP server from a library collection, so that I can easily obtain and configure complex credentials like OAuth tokens.
- As a **collection library author**, I want to define rich help guidance (e.g. `help_text` or instructional links) on collection variables, so that users consuming my collection have clear instructions within the application.
- As an **implementer**, I want each child story focused on a distinct architectural layer (model/schema, wizard UI component, dialog integration, and reference fixtures/docs), so that each can undergo an independent Top-Down cycle.

## Definition of Done

PYPOST-1368 is considered done when:

1. Epic PYPOST-1284 scope and current codebase state are comprehensively analyzed.
2. Natural, cohesive work slices are identified with summaries, preferred Story Points (Fibonacci ≤ 5), dependencies, and acceptance criteria.
3. Decomposition notes are documented in `ai-tasks/PYPOST-1284/decomposition-notes.md`.
4. Child Jira tasks are created in Jira, linked to parent epic PYPOST-1284, and assigned to Sprint 2029 (executed in Step 4).
5. All required Step 1 artifacts exist (`ai-tasks/PYPOST-1368/00-roadmap.md` and `ai-tasks/PYPOST-1368/10-requirements.md`).
6. Quality gate (`make check`) passes.

## Task Description

### Problem Statement

Configuring library MCP servers currently relies on a basic flat form in `_McpServerEditor` (`_library_variables`) that presents each variable with a simple label and text input. Key gaps:
- No field exists in the `CollectionVariable` model for rich guidance (only basic short `description`).
- Users lack guidance on how to obtain credentials (e.g. Google Cloud Console OAuth setup, scope authorization).
- Secret inputs lack masking and toggling options in the wizard context.
- Validation for required variables is bare and lacks immediate feedback.
- Example collections do not demonstrate rich setup guidance.

### Scope (This Decomposition Task)

- Analyze the requirements and proposed scope of PYPOST-1284.
- Define 4 child stories covering the model layer, wizard UI, integration with MCP server dialog, and sample guidance/tests.
- Document requirements, acceptance criteria, and dependencies for each child story.
- Record decomposition documentation in `ai-tasks/PYPOST-1284/decomposition-notes.md` and `ai-tasks/PYPOST-1368/10-requirements.md`.
- In Step 4, create the child tickets in Jira, link them to PYPOST-1284, and place them in Sprint 2029.

### Out of Scope (This Decomposition Task)

- Implementing code changes to PyPost models or UI (deferred to child stories).
- Modifying unrelated MCP server features (e.g., proxy upstream handling or workspace collection management).
- Modifying other sprints or backlog epics outside PYPOST-1284.

### Functional Requirements (Decomposition)

- **FR1:** Each proposed child story must have a concise summary, detailed description, acceptance criteria, dependencies, and story points ≤ 5.
- **FR2:** Together, the child tasks must cover all 5 bullet points of epic PYPOST-1284's proposed scope:
  1. Extend `CollectionVariable` model with rich guidance support.
  2. Create variable setup wizard modal.
  3. Display expandable rich guidance/help panels for variables.
  4. Pre-populate defaults, secret masking, required validation, and save to configuration.
  5. Add sample guidance in library examples and automated tests.
- **FR3:** All created child Jira tasks must be associated with parent epic `PYPOST-1284` and assigned to sprint `2029`.

### Non-Functional Requirements

- **NFR-1 Granularity:** Story points must follow Fibonacci scale (1, 2, 3, 5) with a maximum of 5 SP per task.
- **NFR-2 Top-Down Suitability:** Each story must be independently verifiable and suitable for Top-Down steps 1–8.
- **NFR-3 Traceability:** Requirements and decomposition notes must cross-reference Jira keys once created.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **CollectionVariable** | Schema definition representing a configurable variable in a collection library |
| **Rich Guidance / Help Text** | Structured step-by-step instructions or documentation for acquiring variable values |
| **Variable Setup Wizard** | Interactive UI flow/modal assisting the user in setting up and validating variables |
| **MCP Server Configuration** | Persisted configuration record for an MCP server instance |
| **Variable Overlay / Secrets** | User-specific environment overrides and masked secret values |

---

### Proposed Child Story Breakdown (under PYPOST-1284)

The epic is decomposed into four discrete child tasks:

| Provisional ID | Created Jira Key | Summary | SP | Dependencies | Scope Description |
| --- | --- | --- | --- | --- | --- |
| **WIZARD-1** | [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) | Extend CollectionVariable model and schema with rich help guidance support | 3 | — | Model, validation, serialization, and backward compatibility |
| **WIZARD-2** | [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) | Implement variable setup wizard dialog with expandable guidance panels | 5 | PYPOST-1372 | Reusable UI wizard modal, expandable cards, secret masking, validation |
| **WIZARD-3** | [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) | Integrate variable setup wizard into MCP server configuration dialog | 5 | PYPOST-1373 | Hooking wizard into `_McpServerEditor`, overlay population, and save pipeline |
| **WIZARD-4** | [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) | Add sample help guidance to reference collections & comprehensive test suite | 3 | PYPOST-1372, PYPOST-1373, PYPOST-1374 | Reference fixtures (Google Drive), doc updates, end-to-end contract tests |

#### WIZARD-1 -> PYPOST-1372: Extend CollectionVariable model and schema with rich help guidance support
- **Issue Key**: [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)
- **Issue Type**: Story
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Estimated SP**: 3
- **Dependencies**: None
- **Acceptance Criteria**:
  - `CollectionVariable` model includes `help_text` (optional string or markdown instructions) and any necessary guidance metadata.
  - Backward compatibility is preserved: collections without `help_text` load and validate without error.
  - Model serialization and deserialization in `pypost/models/collection_variable.py` and manifest loaders preserve guidance fields.
  - Unit tests verify schema validation, default handling, and type safety.

#### WIZARD-2 -> PYPOST-1373: Implement variable setup wizard dialog with expandable guidance panels
- **Issue Key**: [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373)
- **Issue Type**: Story
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Estimated SP**: 5
- **Dependencies**: PYPOST-1372 (WIZARD-1)
- **Acceptance Criteria**:
  - A dedicated Qt dialog / wizard component is implemented for variable configuration.
  - Variables are rendered with their name, type, default, requirement status, and an expandable/collapsible guidance panel for `help_text`.
  - Secret variables support masked input with an eye toggle to reveal/hide.
  - Immediate feedback is provided for required missing fields or type mismatches.
  - Comprehensive unit and Qt UI tests verify user interactions, field toggles, and validation states.

#### WIZARD-3 -> PYPOST-1374: Integrate variable setup wizard into MCP server configuration dialog
- **Issue Key**: [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374)
- **Issue Type**: Story
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Estimated SP**: 5
- **Dependencies**: PYPOST-1373 (WIZARD-2)
- **Acceptance Criteria**:
  - When configuring a library collection MCP server in `McpServersDialog` / `_McpServerEditor`, users can trigger the variable setup wizard.
  - Existing overlay values and selected profile defaults are pre-populated into the wizard.
  - Applying the wizard updates the draft configuration overlays and validates required variables prior to saving the MCP server.
  - Seamless fallback or inline summary is displayed in the editor.
  - Integration tests verify the end-to-end flow from library selection to saving server configuration.

#### WIZARD-4 -> PYPOST-1375: Add sample help guidance to reference collections & comprehensive test suite
- **Issue Key**: [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)
- **Issue Type**: Story
- **Parent Epic**: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
- **Sprint**: Sprint 2029 (MCP Variable Setup Wizard)
- **Estimated SP**: 3
- **Dependencies**: PYPOST-1372 (WIZARD-1), PYPOST-1373 (WIZARD-2), PYPOST-1374 (WIZARD-3)
- **Acceptance Criteria**:
  - Example collections (such as `examples/collections/google_drive.json`) are updated with realistic, step-by-step guidance for obtaining credentials (e.g. Google Cloud Console OAuth setup).
  - End-to-end integration and contract tests verify that library collections with rich guidance display and function correctly in the wizard.
  - Developer documentation is added/updated in `doc/dev/` explaining how collection authors can provide variable help guidance.
  - Quality gates (`make check`) pass completely.

---

## Q&A

- **Q: Why split this epic into 4 stories instead of 2?**  
  **A:** Slicing into Model (3 SP), Wizard Component (5 SP), Editor Integration (5 SP), and Fixtures/Docs (3 SP) keeps each story strictly ≤ 5 SP and enables clean, modular development with focused test boundaries for each Top-Down cycle.
- **Q: Are child tasks created in Step 1?**  
  **A:** Following the Top-Down process (similar to PYPOST-1202), Jira task creation is executed during Step 4 (Development), while Step 1 establishes and formalizes the requirements and breakdown.
- **Q: Which sprint will the child tasks belong to?**  
  **A:** All child tasks will be assigned to Sprint 2029 ("MCP Variable Setup Wizard") as specified in the parent epic rules.
