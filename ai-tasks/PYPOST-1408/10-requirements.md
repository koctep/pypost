# PYPOST-1408: Decompose epic PYPOST-1407 into child tasks

## Goals

Epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) ("Collection-scoped variables for standalone MCP servers and workspace collection import") addresses critical design limitations in PyPost's collection library and Model Context Protocol (MCP) server workflows:

1. **Elimination of Global Library Variables**: Currently, collection libraries define variables and presets at the overall library manifest level ("library variables"). This anti-pattern mixes variables across unrelated collections into one shared global list, causing naming collisions, unnecessary credential exposure, and configuration confusion. Variables and preset configurations must belong strictly to individual collections, turning libraries into clean catalogs of self-contained collections.
2. **Frictionless Standalone MCP Server Execution**: When users create an MCP server from a library collection, the system currently forces them to select or create an Environment within their user workspace. Library collections should be fully autonomous and runnable out of the box using their own self-contained variables and presets, without requiring workspace environment scaffolding.
3. **Intuitive Variable Import into Workspace Environments**: When users copy a library collection into their workspace, they need a direct, intuitive way in the environment variables view to import the variables declared by that collection into their workspace environment.

This task ([PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)) decomposes parent epic PYPOST-1407 into granular, implementable, and independently verifiable child Jira tasks (each sized ≤ 5 Story Points using the Fibonacci scale 1, 2, 3, 5), each scoped for a full Top-Down development lifecycle (Steps 1–8), and assigns them all to the active sprint (**Sprint 2033: Collection-Scoped Variables**).

**Business Value**: By providing sprint planners and developers with focused, low-risk, well-estimated work packages, this decomposition enables parallel execution, prevents monolithic blockers, and ensures all core business goals and acceptance criteria of PYPOST-1407 are satisfied with high quality.

## Programming Language

- **This task (PYPOST-1408):** Markdown planning artifacts and Jira process management.
- **Child implementation stories under PYPOST-1407:** Python (PyPost models, core business logic, Qt UI components, MCP runtime, and pytest suites).

## User Stories

- As a **sprint planner**, I want epic PYPOST-1407 decomposed into small, well-estimated child tasks (≤ 5 Story Points each) linked to the epic and added to Sprint 2033, so that sprint execution is predictable, transparent, and manageable.
- As an **API collection author**, I want all variables, descriptions, types, secrets, and environment presets to be defined directly within my collection, so that my collection is completely self-contained and does not rely on or pollute global library namespaces.
- As a **library consumer / MCP operator**, I want to launch an MCP server from any library collection immediately without having to configure or choose an Environment in my personal workspace, so that out-of-the-box servers run with zero friction.
- As a **workspace user**, I want to copy a collection into my workspace and easily import its declared variables into my workspace environment via the environment variables view, so that I don't have to manually re-type variable names, defaults, or secret flags.
- As an **engineer executing the epic**, I want child tasks organized by cohesive architectural and functional boundaries (collection variable scoping, standalone MCP configuration and execution, workspace variable import UI, and end-to-end integration contracts) so that each story has crisp acceptance gates.

## Definition of Done

This task (PYPOST-1408) is considered done when:

1. Epic PYPOST-1407 scope, business requirements, and operational constraints are comprehensively analyzed.
2. Natural, cohesive work slices are identified, each sized ≤ 5 Story Points following the Fibonacci sequence (1, 2, 3, 5).
3. Decomposition documentation is published in `ai-tasks/PYPOST-1407/decomposition-notes.md`.
4. Child Jira tasks are created in Jira, linked as children to parent epic `PYPOST-1407`, and added to active `Sprint 2033` (executed in Step 4).
5. All required Step 1 artifacts exist (`ai-tasks/PYPOST-1408/00-roadmap.md` and `ai-tasks/PYPOST-1408/10-requirements.md`).
6. Quality gates (`make check`) pass cleanly.

## Task Description

### Problem Statement

In the existing PyPost architecture:
- **Library-Level Variable Pollution**: A collection library manifest defines variables and presets globally across all collections it contains. When a library contains multiple distinct collections (e.g., GitLab API, GitHub API, Jira API), their variables are pooled together in setup interfaces, forcing users to navigate irrelevant settings.
- **Mandatory Workspace Environment for MCP**: When starting an MCP server from a library collection, users must associate it with an Environment in their local workspace. This creates friction because library collections should be executable standalone using their own declared variables and presets.
- **Disconnected Workspace Import**: While collections can be copied into a workspace, there is no integrated action in the environment variables view to pull the collection's declared variables into a workspace environment.

### Scope (This Decomposition Task)

- Analyze the business requirements and acceptance criteria of parent epic PYPOST-1407.
- Define 4 focused child tasks covering:
  1. Elimination of library-level variables, migration to catalog-only libraries, and enforcement of self-contained collection variables and presets.
  2. Standalone MCP server configuration and execution without workspace environment prerequisites.
  3. Workspace environment variable import action from collections in the environment variables view.
  4. End-to-end integration contracts, backward-compatibility verification, and developer documentation.
- Formulate acceptance criteria, dependencies, deliverables, and Fibonacci story point estimates (all ≤ 5 SP) for each child task.
- Document the decomposition plan in `ai-tasks/PYPOST-1407/decomposition-notes.md`.
- In Step 4, create the corresponding Jira tickets, link them to `PYPOST-1407`, and assign them to `Sprint 2033`.

### Out of Scope (This Decomposition Task)

- Modifying PyPost production code, models, or UI widgets directly (implementation belongs to child stories COLVAR-1 through COLVAR-4).
- Altering other backlog epics or unrelated sprints.

### Functional Requirements (Decomposition)

- **FR1:** The decomposition must split epic PYPOST-1407 into child stories where every story has an estimate of ≤ 5 SP.
- **FR2:** The child tasks must collectively satisfy all 4 business acceptance criteria of epic PYPOST-1407:
  1. Elimination of "library variables"; variables and presets belong strictly to collections.
  2. Library collections can run as MCP servers without requiring an Environment in the user workspace.
  3. Users can import declared collection variables into their workspace environment when copying or working with a collection.
  4. Setup dialogs present collection-specific variable configuration cleanly without confusing library-level variable lists.
- **FR3:** All created child Jira tasks must be associated with parent epic `PYPOST-1407` and assigned to active `Sprint 2033`.

### Non-Functional Requirements

- **NFR-1 Granularity:** Story points must follow the Fibonacci scale (1, 2, 3, 5), strictly capping any single ticket at 5 SP.
- **NFR-2 Slicing Integrity:** Each child story must be independently testable and capable of executing a full Top-Down development lifecycle (Steps 1–8).
- **NFR-3 Safety & Backward Compatibility:** Legacy library manifests with library-level variables must be handled gracefully without corrupting existing workspaces or crashing the application.
- **NFR-4 Usability:** Variable setup and import interactions must be clear, intuitive, and prevent accidental data loss or variable name collisions.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **Collection Library** | Catalog of available collections; does not declare global variables or presets |
| **Self-Contained Collection** | Autonomous collection containing requests, variable declarations, types, secrets, and presets |
| **Collection-Scoped Variable** | Variable definition (name, type, default value, description, help text, secret flag, required flag) owned by a collection |
| **Collection Preset** | Named profile within a collection defining preset variable values for specific execution contexts |
| **Standalone MCP Server** | MCP server instance configured and run directly from a collection's variables and presets without requiring a workspace environment |
| **Workspace Environment** | User-managed environment containing key-value pairs; supports importing variables from collections |

### Proposed Child Story Breakdown (under PYPOST-1407)

| Provisional ID | Title | SP | Dependencies | Scope Summary |
| --- | --- | --- | --- | --- |
| **COLVAR-1** | Eliminate library-level variables and establish collection-scoped variables and catalog manifest | 3 | None | Catalog-only library manifest, deprecate library-level variables, enforce collection-owned variables and presets in core resolution logic |
| **COLVAR-2** | Standalone MCP server configuration and execution without workspace environment | 5 | COLVAR-1 | Allow MCP server configurations to run standalone from collection variables/presets without `environment_id`, update setup dialogs and server runner |
| **COLVAR-3** | Workspace environment variable import action from collections | 3 | COLVAR-1 | Add action in environment variables view to import declared collection variables into workspace environments with conflict resolution |
| **COLVAR-4** | Integration test suite, compatibility matrix, and developer documentation | 3 | COLVAR-1, COLVAR-2, COLVAR-3 | End-to-end integration contracts (standalone MCP execution, variable import), legacy migration verification, developer documentation |

**Total Epic Effort:** 14 SP across 4 child stories.

## Q&A

**Q: Why should library-level variables be eliminated rather than made optional alongside collection variables?**  
A: Having two overlapping levels of variables (library-level and collection-level) introduces hierarchy ambiguities, provenance confusion, and cluttered UI forms. A library is fundamentally a catalog of collections. Scoping variables strictly to collections makes collections truly self-contained, portable, and reusable across libraries, workspaces, and standalone MCP servers.

**Q: Why is standalone MCP server creation estimated at 5 SP while the other tasks are 3 SP?**  
A: Standalone MCP server execution impacts multiple layers: the server configuration model (`McpServerConfiguration`), validation logic, runtime resolution services (`LibraryRuntimeResolver`), server startup processes, and the Qt UI dialogs (`mcp_servers_dialog.py` and variable setup wizards) where environment selection must be made optional or bypassed for library collections while preserving preset selection and secret entry.

**Q: When will the child Jira tickets be created?**  
A: In accordance with the Top-Down workflow standard, Step 1 establishes business requirements and decomposition notes. Step 2 defines the architectural blueprints and ticket specifications. Step 4 performs the Jira creation, linking each issue to epic PYPOST-1407 and assigning it to Sprint 2033.
