# PYPOST-1412: Integration test suite, compatibility matrix, and developer documentation

## Goals

The parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) introduces a major architectural transformation to PyPost: transitioning collection libraries to pure catalog manifests, establishing collections as the authoritative single source of truth for variables and presets, enabling standalone tool execution without workspace environments, and providing an interactive variable import bridge into workspace environments.

Prior child tasks implemented these features in focused phases:
1. [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) eliminated library-level variables and established catalog-only manifests and collection-scoped authority.
2. [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) decoupled server configuration and execution from workspace environments, enabling standalone execution.
3. [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) added an interactive variable import action with conflict resolution and secret masking in the workspace environment variables view.

While each preceding phase validated its specific components in isolation, a comprehensive consolidation and verification effort is necessary to guarantee end-to-end operational integrity across the entire application:
1. **End-to-End Workflow Verification**: The system lacks an overarching integration test suite validating realistic, multi-step user workflows where library catalog indexing, standalone server execution, collection copying, workspace environment variable import, and parameterized request execution interact together.
2. **Backward Compatibility Matrix**: Existing users rely on historical library manifests (which declare root-level variables and presets), legacy collection formats, and existing workspace environments. The system must prove that legacy installations continue to load and function predictably with non-fatal deprecation notices and without data loss or crashes.
3. **Failure Scenarios and Diagnostic Contracts**: Comprehensive end-to-end tests must verify edge cases, including missing required variables, incomplete presets, conflicting variable definitions, and malformed catalog manifests, ensuring user-facing diagnostic messages are clear and actionable.
4. **Developer Documentation & Architectural Reference**: The project's developer documentation must be systematically updated to provide a cohesive architectural guide, clear operational references, and testing standards for collection-scoped variables, standalone servers, and workspace variable synchronization.

The goal of this task is to deliver a robust end-to-end integration test suite, establish and verify the backward compatibility matrix, update test fixtures, and deliver comprehensive developer documentation in the developer documentation tree.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **application maintainer**, I want a comprehensive end-to-end integration test suite that exercises catalog loading, standalone server startup, collection copying, and variable import together, so that regressions in cross-subsystem interactions are detected immediately.
- As an **existing PyPost user with legacy library manifests**, I want my existing libraries containing top-level variables and presets to load seamlessly and resolve variables gracefully with clear deprecation warnings, so that my existing workflows and tool configurations remain functional without manual intervention.
- As a **developer creating or extending API collections**, I want clear and consolidated architectural documentation and developer guides in `doc/dev/`, so that I understand how collection-scoped variables, catalog manifests, standalone execution, and environment imports work together.
- As a **QA / release engineer**, I want an explicit compatibility matrix validating supported catalog versions, collection formats, and environment schemas, so that platform stability and migration safety are guaranteed for new releases.
- As an **autonomous agent / automated test runner**, I want integration test suites to adhere to strict timeout constraints, clean test isolation, and deterministic execution, so that CI/CD pipelines run reliably without hangs or flaky state leaks.

## Definition of Done

This task is considered complete when:
1. An end-to-end integration test suite is implemented that validates complete user journeys:
   - Ingesting a catalog-only collection library.
   - Configuring and running a standalone tool server with collection presets and local secrets without a workspace environment.
   - Copying a collection into a user workspace.
   - Importing collection variables into an active workspace environment with conflict policies and secret masking.
   - Executing parameterized operations with the resolved environment state.
2. A compatibility matrix is validated through automated tests covering:
   - Modern catalog manifests referencing self-contained collections.
   - Legacy library manifests declaring top-level variables and presets (verifying graceful fallback and deprecation logging).
   - Mixed configurations with both legacy and modern collection references.
   - Existing workspace environments interacting with imported collection variables.
3. Negative and failure cases are rigorously verified:
   - Unmet required variables prevent execution with clear diagnostic feedback.
   - Invalid variable identifiers or malformed manifests fail gracefully without application crashes.
   - Conflicting variables adhere strictly to chosen collision policies (skip vs. overwrite).
4. Automated tests adhere to repository testing contracts (bounded execution, timeout enforcement, clean fixture teardown, and secret-safe logging).
5. Developer documentation in `doc/dev/` is consolidated, updated, and verified:
   - Comprehensive guide on collection-scoped variables, catalog manifests, standalone execution, and workspace import.
   - Cross-references and index entries updated in [README.md](file:///home/src/doc/dev/README.md).
   - Documentation passes all repository documentation validation gates (`make lint-docs` and `make check-docs-links`).
6. All repository quality gates (`make check`, including linting, typing, tests, and task verification) pass cleanly.

## Task Description

### Problem Statement

During the execution of epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407), significant changes were introduced across multiple distinct architectural domains:
- Catalog manifest parsing and collection-first variable precedence engine.
- Server configuration schema and standalone runtime execution engine.
- Interactive user interface and domain logic for importing collection variables into workspace environments.

While each child story implemented focused unit tests and isolated reproduction harnesses, individual unit tests cannot guarantee that all components operate harmoniously when integrated into end-to-end workflows. Furthermore, verifying backward compatibility across legacy manifest formats requires dedicated multi-version fixtures and test scenarios. Finally, architectural knowledge must be documented in a central, well-maintained developer guide so that contributors and maintainers have complete visibility into design decisions, precedence rules, and compatibility contracts.

### Scope

- **End-to-End Integration Suite**:
  - Implement automated integration tests simulating realistic multi-step user workflows spanning catalog loading, standalone tool execution, collection copying, environment variable import, and variable substitution.
  - Verify isolation: standalone execution operates with zero workspace environments; workspace import operates cleanly without mutating source collections.
- **Compatibility Matrix & Test Fixtures**:
  - Provide and test catalog fixtures representing:
    - Pure catalog manifests referencing self-contained collections.
    - Legacy manifests containing root-level variables and presets.
    - Legacy manifests where collections override root-level variables.
  - Verify that legacy manifests generate informative deprecation warnings while maintaining runtime behavior.
- **Failure and Diagnostic Verification**:
  - Test missing required variables, malformed manifests, missing referenced collection files, and invalid variable values.
  - Validate that error reports provide clear diagnostics without exposing secret values in logs or exception messages.
- **Developer Documentation Consolidation**:
  - Consolidate and expand developer documentation in `doc/dev/` detailing collection scoping, standalone server lifecycles, and environment synchronization.
  - Update documentation indexes and ensure all links, markdown structures, and references adhere to repository documentation standards.

### Out of Scope

- Implementing new UI widgets or dialogs (completed in preceding child tasks).
- Changing the underlying network or transport protocol implementations.
- Modifying encryption key management or environment storage persistence formats.

### Functional Requirements

- **FR1 (End-to-End Workflow Integration)**: The system must successfully execute an integrated workflow encompassing catalog discovery, collection variable resolution, standalone server startup without a workspace environment, copying a collection to a workspace, importing variables into a workspace environment with conflict policies, and substituting variables in active requests.
- **FR2 (Compatibility Matrix Enforcement)**: The system must support the full matrix of catalog and collection versions:
  - Modern Catalog Manifest + Self-Contained Collection: Variables and presets resolve directly from the collection.
  - Legacy Library Manifest (top-level variables) + Modern Collection: Collection variables take precedence; top-level variables serve as fallback with a deprecation notice.
  - Legacy Library Manifest + Legacy Collection: Resolved using legacy hierarchy with non-fatal deprecation logging.
- **FR3 (Standalone Server Validation)**: When launching a standalone server from a library collection without a workspace environment, the server runtime must correctly resolve defaults, active presets, and machine-local secrets, refusing startup only when required non-secret variables are unfulfilled.
- **FR4 (Workspace Import Integrity)**: When importing collection variables into a workspace environment, the system must respect selected keys, apply the chosen collision policy (skip existing keys vs. overwrite existing values), and enforce automatic secret masking in the destination environment.
- **FR5 (Diagnostic & Error Handling Standards)**: The system must provide human-readable diagnostic messages when required variables are absent or when manifests reference non-existent collections, without leaking secret values into logs or traces.
- **FR6 (Documentation Completeness & Accuracy)**: The developer documentation must accurately describe the end-to-end architecture, variable resolution precedence, standalone execution model, workspace import procedures, and compatibility contracts.

### Non-Functional Requirements

- **NFR1 (Test Performance & Reliability)**: All integration tests must complete well within standard pytest timeout boundaries (under 10 seconds per test) with zero flaky dependencies on external networks or sleep calls.
- **NFR2 (Security & Confidentiality)**: Secret masking must remain intact across the entire pipeline: secrets declared in collections must import as hidden variables and must be masked in log outputs and error reports.
- **NFR3 (Maintainability & Test Isolation)**: Integration test fixtures must be isolated using temporary workspaces and clean teardowns, preventing test pollution across test suites.
- **NFR4 (Documentation Standards)**: Developer documentation must pass all repository markdown linting (`make lint-docs`) and link verification (`make check-docs-links`) checks.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Catalog Manifest** | Pure catalog index referencing available collections in a library. | Identifier, display title, semantic version, description, list of collection paths. |
| **Self-Contained Collection** | Autonomous aggregate containing requests, tools, declared variables, and preset profiles. | Identifier, name, requests list, collection variables, profile presets, library linkage. |
| **Collection Variable** | Specification for a variable declared within a collection. | Name, data type, default value, description, required status, secret indicator. |
| **Profile Preset** | Named configuration profile within a collection offering predefined variable values. | Preset name (e.g., Staging, Production), key-value variable mappings. |
| **Standalone Server Configuration** | Configuration for running a collection as an external tool server without workspace environment binding. | Server identifier, display title, source collection reference, active preset name, machine-local secret overrides. |
| **Workspace Environment** | User-managed environment storing variable bindings and hidden key designations for active requests. | Environment identifier, environment name, variable dictionary, hidden/secret keys set. |
| **Compatibility Matrix Record** | Specification of supported catalog and collection schema combinations and their expected resolution behaviors. | Manifest format version, collection format version, fallback behavior, deprecation notice status. |

## Q&A

**Q: Why is a dedicated integration test suite necessary if unit tests already exist for PYPOST-1409, PYPOST-1410, and PYPOST-1411?**  
A: Unit tests and reproduction tests verify individual classes and isolated dialogs using focused mocks and artificial fixtures. An end-to-end integration test verifies the interoperability of all components across the entire chain: reading a catalog from disk, launching a server from that catalog's collection without an environment, importing that same collection's variables into a workspace environment, and validating that variable precedence, collision strategies, and secret masking operate consistently throughout the application.

**Q: What specific scenarios does the compatibility matrix cover?**  
A: The compatibility matrix covers:
1. Modern pure catalog manifests with modern self-contained collections.
2. Legacy library manifests containing root-level variables and presets paired with modern self-contained collections (verifying that collection variables take precedence and deprecation warnings are logged).
3. Legacy library manifests paired with legacy collections relying on root-level variables (verifying backward-compatible fallback).
4. Standalone servers saved without environment references vs. workspace servers with environment references.
5. Workspace environments imported from collections with both new and existing key collisions.

**Q: How does this task handle documentation requirements?**  
A: This task consolidates, expands, and verifies documentation in `doc/dev/`, specifically ensuring that [collection_scoped_variables.md](file:///home/src/doc/dev/collection_scoped_variables.md) is fully updated with the completed state of all child tasks, [README.md](file:///home/src/doc/dev/README.md) is updated with cross-references, and all documentation satisfies `make lint-docs` and `make check-docs-links`.

**Q: Will any production application code be altered in this task?**  
A: Primarily, this task produces integration tests, test fixtures, and documentation. However, if integration testing or compatibility matrix validation reveals unexpected gaps or edge-case inconsistencies in manifest parsing, error handling, or variable resolution across components, targeted bug fixes may be made to ensure full compliance with the epic's acceptance criteria.
