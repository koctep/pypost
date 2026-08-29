# PYPOST-1108: Decouple Environment-to-MCP state propagation with domain Qt signals

## Goals

This task addresses architectural debt identified during the modularization of the presentation layer (PYPOST-1082). The business and maintainability goals are:

- **Domain Isolation and Boundary Integrity**: Separate the Environment domain from direct orchestration of the MCP (Model Context Protocol) subsystem. The Environment domain should manage environment lifecycle and variable data without directly controlling downstream presentation components.
- **Centralized Event Architecture**: Adopt an event-driven notification pattern where environment lifecycle events are published as domain signals and wired centrally by the application, standardizing how components communicate across boundaries.
- **Zero Behavioral Regressions**: Ensure that user workflows depending on environment-to-MCP synchronization—such as updating active environment variables, switching environments, modifying environment configurations, and tracking activity metrics—remain completely intact and reliable.
- **Improved Testability and Maintainability**: Enable independent unit testing of the Environment and MCP presentation components without requiring one presenter to mock or manage internal calls to the other.

## User Stories

- **As an Application User**, I want changes to my environment (switching environments, updating variables via scripts, or saving edits in the environment manager) to automatically and reliably synchronize with MCP tool references and servers, so that my AI workflows and API calls always reflect the active configuration without error or delay.
- **As a Developer / Maintainer**, I want the Environment component to emit clear domain lifecycle events rather than directly calling into MCP presenter methods, so that the code remains modular, easy to understand, and extensible.
- **As a Developer / Maintainer**, I want all cross-presenter signal wiring to be centrally defined in the application's signal router, so that data flows between subsystems are transparent, observable, and easy to audit.
- **As a Quality Assurance Engineer**, I want the Environment and MCP subsystems to be independently verifiable with automated tests, ensuring high test coverage without tight coupling or brittle mocking.

## Definition of Done

- Environment state changes (active environment selection, environment deselection, variable updates from scripts or user actions, and environment manager updates) are published as domain events rather than direct method invocations on MCP controls.
- MCP controls receive and process environment state transitions via centralized application event wiring.
- All environment-dependent MCP functions—including tool button updates, active environment tracking, server environment updates, and tool reference reconciliation—continue to function seamlessly across all user flows.
- Direct invocation coupling from the Environment presenter to MCP controls is eliminated.
- Automated tests verify that environment lifecycle events are correctly emitted and that the MCP controls respond appropriately when wired through the application's central signal connections.
- Existing functionality is fully preserved with zero user-visible behavioral or performance regressions.
- All quality gate checks (`make check` / linting, testing, and AI task artifacts verification) pass.

## Task Description

### Problem Statement

In the current desktop application, the Environment management component maintains a direct reference to the MCP controls component and directly calls several of its methods whenever environment state changes occur:
1. When variables are updated via post-request test scripts or manual user input, the environment component directly invokes an environment refresh on MCP controls.
2. When the user switches the active environment (or clears the selection), the environment component directly invokes active environment selection handling and metric tracking on MCP controls.
3. When the environment manager dialog closes after creating, editing, or deleting environments, the environment component directly invokes reference reconciliation and environment refresh on MCP controls.

This direct method invocation bypasses the established application pattern of decoupled, signal-based communication. It ties the Environment management logic directly to the implementation details and lifecycles of MCP controls, complicating refactoring and hampering isolated component testing.

### Scope & System Boundaries

- **In Scope**:
  - Definition of domain lifecycle events emitted by the Environment component for environment selection, variable updates, and manager completion.
  - Centralized connection of these environment domain events to the corresponding MCP control handlers in the application's signal wiring layer.
  - Removal of direct MCP control method calls from the Environment management component.
  - Verification that MCP servers and tools maintain accurate environment state across all lifecycle scenarios.
  - Updating and expanding unit and integration tests to validate decoupled event emission and reception.
- **Out of Scope**:
  - Changing the visual presentation, styling, or layout of the environment toolbar or MCP widgets.
  - Modifying how environment variables are resolved or stored on disk.
  - Altering the MCP protocol, server execution model, or tool discovery algorithms.
  - Refactoring unrelated toolbar presenters or dialog internals.

### Functional Requirements

1. **Active Environment Selection Propagation**:
   - When an environment is selected or deselected by the user, a domain event must notify interested components with the selected environment state.
   - MCP controls must respond by adjusting active server configurations, updating UI tool counts, and logging/tracking active environment transitions.

2. **Variable Mutation Notification**:
   - When environment variables are updated (e.g. from script execution or variable assignment), a domain event must broadcast the affected environment update.
   - MCP controls must respond by refreshing the environment state within active MCP servers and updating references.

3. **Environment Management Batch Update Notification**:
   - When the user finishes modifying environments in the Environment Manager dialog (creating, editing, deleting, or importing environments), a domain event must signal that environment definitions have changed.
   - MCP controls must respond by reconciling references and refreshing configurations for all active and affected environments.

### Non-Functional Requirements

- **Loose Coupling**: Components must communicate across domain boundaries exclusively via asynchronous/decoupled event mechanisms without holding hard dependencies on each other's operational methods.
- **Performance**: Event dispatching must introduce zero noticeable UI lag during rapid environment changes or batch variable updates.
- **Reliability & Order of Operations**: State synchronization must occur deterministically to ensure that MCP servers never execute tools against stale environment variables.
- **Maintainability & Documentation**: Event definitions and routing must be self-describing and documented in developer architecture guides.

### Constraints & Assumptions

- **Implementation Language**: Python.
- **Architecture Standard**: Must follow the project's Model-View-Presenter (MVP) architecture and centralized signal routing standards.
- **Backward Compatibility**: All user-facing behaviors, shortcuts, and dialog interactions must behave identically to before the refactoring.

### Main Business Entities

- **Environment Domain**: Manages environment definitions, variable storage, active selection, and variable resolution.
- **MCP Controls Domain**: Manages MCP server lifecycles, tool discovery, UI status indicators, and tool reference mapping.
- **Application Signal Router**: The central hub responsible for wiring domain events between independent presenters and panels.

## Q&A

### Why should environment-to-MCP synchronization use domain signals instead of direct calls?

Direct method calls between presenters create tight coupling, making components dependent on each other's internal structure and lifecycles. Emitting domain signals allows the Environment component to focus purely on managing environments while letting the application orchestrate how downstream features—like MCP controls—react to environment changes.

### Will this change how users interact with environments or MCP tools?

No. The user experience remains completely unchanged. Switching environments, running scripts that update variables, and managing environments in the dialog will continue to update MCP tools and servers exactly as before, with no visual or functional differences.

### What programming language is used for implementation?

Python.
