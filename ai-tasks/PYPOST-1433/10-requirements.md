# PYPOST-1433: Modular Harness Architecture and Mixin Decomposition

## Goals

Test suites spanning collection variables, library catalog discovery, workspace environments, and standalone MCP server execution rely on the shared integration harness `CollectionVariablesIntegrationHarness` (established in [PYPOST-1417](https://pypost.atlassian.net/browse/PYPOST-1417)). While centralizing test infrastructure into a single shared helper eliminated duplication across test files, the existing harness bundles multiple independent domain concerns into a single monolithic class:
1. **Library & Manifest Management**: Creating local library catalogs, v1/v2 manifests, collections, and overlay secrets.
2. **Environment & Storage Management**: Managing workspace directory trees, persistent environment stores, variables, and hidden keys.
3. **Server Registry & Process Lifecycle**: Managing MCP server configurations, dynamic TCP port binding, process startup, readiness synchronization, and active connection termination.
4. **End-to-End Orchestration**: Driving multi-subsystem lifecycles spanning discovery through template substitution.

From a business, engineering, and maintenance perspective, this monolithic design introduces several key issues:
- **God-Object Anti-Pattern**: As PyPost integrates additional capabilities (e.g. wire IPC, client session dispatch, Git synchronization), coupling all fixture behaviors into one class makes test scaffolding increasingly brittle, harder to understand, and difficult to extend without accidental side effects.
- **Unnecessary Overhead & Coupling**: Tests that only require library catalog generation or workspace environment variables are forced to instantiate the entire harness, including server registry subsystems, directory scaffolding, and teardown handlers they do not need.
- **Limited Fixture Reusability**: Test authors cannot easily compose only the specific fixture capabilities required for their target scenario (such as using server registry lifecycle testing without full library disk scaffolding, or environment variable resolution without MCP registry overhead).

The primary goal of this task is to decompose `CollectionVariablesIntegrationHarness` into modular, composable mixins (`LibraryFixtureMixin`, `ServerRegistryFixtureMixin`, `EnvironmentFixtureMixin`) or a composable fixture pattern. This architecture must:
1. Separate concerns into cohesive, single-responsibility modules.
2. Allow targeted test fixture composition so tests can select only the capabilities they require.
3. Decouple filesystem management from MCP server registry lifecycle.
4. Maintain 100% backward compatibility for all existing tests and pytest fixtures that consume `CollectionVariablesIntegrationHarness`.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **PyPost test author**, I want modular, single-responsibility fixture mixins (`LibraryFixtureMixin`, `ServerRegistryFixtureMixin`, `EnvironmentFixtureMixin`), so that I can compose only the test fixtures my test suite needs without incurring the cognitive and performance overhead of unrelated subsystems.
- As a **developer writing focused subsystem tests**, I want to use library catalog creation or workspace environment management without initializing an MCP server registry, so that my unit and integration tests remain lightweight, fast, and free of unnecessary filesystem directories.
- As a **developer testing server registry and process lifecycles**, I want a dedicated server registry fixture mixin that provides safe port allocation, process startup, and guaranteed teardown without requiring full library manifest disk scaffolding.
- As a **codebase maintainer**, I want `CollectionVariablesIntegrationHarness` to retain its full existing public API and behavior through mixin composition, so that all existing integration test suites continue to pass without any breaking changes or required migration.
- As a **QA / CI engineer**, I want each modular mixin to uphold strict resource hygiene and automated teardown contracts, so that background processes, sockets, and temporary directories are reliably cleaned up regardless of whether mixins are used individually or combined.

## Definition of Done

This task is considered complete when:
1. The monolithic responsibilities of `CollectionVariablesIntegrationHarness` are decomposed into distinct, cohesive mixins:
   - `LibraryFixtureMixin`: Encapsulates test library creation, catalog manifests, collection structures, and local overlay persistence.
   - `EnvironmentFixtureMixin`: Encapsulates workspace environment creation, variable storage, and secret masking.
   - `ServerRegistryFixtureMixin`: Encapsulates standalone MCP server candidate configuration, dynamic port assignment, server startup/readiness tracking, and server teardown.
2. `CollectionVariablesIntegrationHarness` is refactored to compose these mixins while preserving 100% backward compatibility for all existing attributes, methods, context manager contracts, and pytest fixtures (`collection_integration_harness`, `collection_harness`).
3. Individual mixins can be composed independently or used in combination without requiring the entire composite harness.
4. Resource lifecycle management (such as server registry teardown) remains safe, idempotent, and guaranteed upon test completion or exception, whether executed through the composite harness or the isolated server registry mixin.
5. All existing test suites consuming `CollectionVariablesIntegrationHarness` continue to pass without modification or regressions.
6. New or updated tests demonstrate and verify independent mixin usability and composite harness backwards compatibility.
7. Quality gates pass cleanly:
   - Static analysis, linting, and type checking (`make lint`, `make typecheck`).
   - Fast and integration test suites (`make test`, `make check`).
   - AI task artifacts validation (`make verify-ai-tasks`).

## Task Description

### Problem Statement

In [PYPOST-1417](https://pypost.atlassian.net/browse/PYPOST-1417), the integration test harness was extracted into `tests/helpers/collection_integration_harness.py`. While this established a reusable home for test fixtures, it retained an all-in-one monolithic class structure. As noted in the [PYPOST-1417 Technical Debt Analysis](file:///home/src/ai-tasks/PYPOST-1417/60-tech-debt.md):
> `CollectionVariablesIntegrationHarness` directly couples library directory creation, connection store management, overlay persistence, workspace environment storage, runtime resolution, template rendering, and MCP server registry lifecycle into a single monolithic class. As additional subsystems are integrated... the harness risks growing into an unwieldy god object. Decomposing the class into modular mixins... would improve cohesion and separation of concerns.

Decomposing this infrastructure into focused, composable mixins decouples filesystem management from process lifecycle management, simplifies future test authoring, and sets a clean pattern for future subsystem integration.

### Scope

- **In Scope**:
  - Decompose `CollectionVariablesIntegrationHarness` into modular, reusable mixin components:
    - Library and catalog management (`LibraryFixtureMixin`)
    - Environment and storage management (`EnvironmentFixtureMixin`)
    - Server registry and lifecycle management (`ServerRegistryFixtureMixin`)
  - Retain `CollectionVariablesIntegrationHarness` as a composite class combining these mixins, preserving its complete existing interface (`create_library`, `create_workspace_environment`, `create_overlay`, `start_standalone_server`, `run_unified_lifecycle`, `teardown`, `close`, `__enter__`, `__exit__`).
  - Ensure individual mixins can be cleanly combined into custom test fixtures or used independently.
  - Preserve all existing pytest fixture bindings (`collection_integration_harness`, `collection_harness`).
  - Add tests validating that individual mixins operate independently and that the composite harness maintains full functional compatibility.
- **Out of Scope**:
  - Altering production runtime code in `pypost/`.
  - Modifying the underlying MCP server protocol or JSON-RPC handling.
  - Changing the behavior or test assertions of existing downstream test suites.

### Functional Requirements

- **FR1: Library Fixture Capability (`LibraryFixtureMixin`)**:
  - Must provide isolated catalog and collection creation capabilities, including modern v2 manifests and legacy v1 manifests with variables and presets.
  - Must provide local overlay persistence capabilities for active profiles and secrets.
  - Must connect created libraries to the library management service.
- **FR2: Environment Fixture Capability (`EnvironmentFixtureMixin`)**:
  - Must provide isolated workspace environment creation capabilities, supporting variables and hidden keys.
  - Must persist created environments through the storage management layer.
- **FR3: Server Registry Fixture Capability (`ServerRegistryFixtureMixin`)**:
  - Must provide standalone MCP server configuration, validation, and lifecycle startup capabilities.
  - Must support conflict-free dynamic TCP port allocation.
  - Must provide bounded readiness verification and status tracking.
  - Must provide idempotent server shutdown and teardown (`stop_all`).
- **FR4: Composite Integration Harness (`CollectionVariablesIntegrationHarness`)**:
  - Must compose `LibraryFixtureMixin`, `EnvironmentFixtureMixin`, and `ServerRegistryFixtureMixin` into a unified test harness.
  - Must preserve all existing method signatures, return types, and properties.
  - Must provide `run_unified_lifecycle` coordinating catalog creation, standalone server execution, variable importation, and template substitution.
  - Must provide context manager support (`__enter__`/`__exit__`) and explicit cleanup (`teardown`/`close`).
- **FR5: Independent Mixin Composability**:
  - Mixins must be modular and designed to be composed together or used selectively in test classes and custom fixtures without circular dependencies.
- **FR6: 100% Backwards Compatibility**:
  - All existing tests importing `CollectionVariablesIntegrationHarness`, `UnifiedLifecycleResult`, or the pytest fixtures `collection_integration_harness` / `collection_harness` must continue to function with zero code changes and identical runtime behavior.

### Non-Functional Requirements

- **NFR1: Cohesion & Separation of Concerns**: Each mixin must have a single, well-defined domain responsibility, eliminating god-object tendencies in test helper code.
- **NFR2: Resource Hygiene & Teardown Safety**: Server lifecycle resources, sockets, and background execution states must be deterministically released upon teardown, preventing resource leaks or test flakiness.
- **NFR3: Performance & Bounded Execution**: Modular decomposition must not introduce performance regressions. Harness initialization and execution must remain fast (< 500ms for standard workflows).
- **NFR4: Type Safety & Documentation**: All mixins and composite classes must include complete type annotations adhering to PEP 484/561 and Google-style docstrings, passing `make typecheck` and `make lint` without warnings.
- **NFR5: Tooling Standard Compliance**: All operations must be verified through standard repository `make` targets (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`).

### System Entities & Domain Perspective

- **Library Fixture Component**: Domain capability responsible for generating ephemeral library catalogs, collection definitions, manifest files, and local overlay secret records in temporary storage.
- **Environment Fixture Component**: Domain capability responsible for creating, initializing, and persisting isolated workspace environments and their scoped variables.
- **Server Registry Fixture Component**: Domain capability responsible for configuring, validating, launching, and safely terminating standalone MCP servers with dynamic network bindings.
- **Composite Integration Harness**: High-level test fixture aggregating all individual fixture capabilities and offering unified multi-subsystem workflow execution.
- **Unified Lifecycle Result**: Structured value object representing the outcome of multi-subsystem workflow execution (server status, imported variable counts, and rendered template strings).

### User Scenarios & Use Cases

- **Scenario 1: Full Multi-Subsystem Integration Testing (Existing Behavior)**:
  A developer writes an end-to-end integration test using `collection_integration_harness` or `CollectionVariablesIntegrationHarness`. The harness provides access to library creation, overlay management, environment persistence, server startup, and unified lifecycle execution. All servers are automatically stopped when the test finishes.
- **Scenario 2: Lightweight Library & Manifest Testing (Modular Mixin)**:
  A developer needs to test manifest parsing, collection serialization, or overlay resolution without spinning up an MCP server registry or background threads. The developer uses `LibraryFixtureMixin` in a focused test fixture, avoiding unnecessary registry setup.
- **Scenario 3: Isolated Server Registry Lifecycle Testing (Modular Mixin)**:
  A developer tests server registry error handling, port collision retry, or concurrent server lifecycles using `ServerRegistryFixtureMixin`. The mixin manages port allocation and process termination independently from library manifest file generation.
- **Scenario 4: Selective Composition of Mixins**:
  A developer creates a specialized test harness combining only `EnvironmentFixtureMixin` and `LibraryFixtureMixin` to test variable import and preset inheritance without any server registry overhead.

## Q&A

- **Q: Why decompose `CollectionVariablesIntegrationHarness` if it is already working?**
  A: The current harness bundles library filesystem management, overlay configuration, workspace environment persistence, and background server process management into one monolithic class. As identified in [PYPOST-1417 Technical Debt](file:///home/src/ai-tasks/PYPOST-1417/60-tech-debt.md), this violates the single-responsibility principle and turns the harness into a god object that is harder to maintain and forces tests to incur full setup overhead even when only a subset of capabilities is needed.
- **Q: Will existing tests need to be updated?**
  A: No. A core acceptance criterion is 100% backward compatibility. `CollectionVariablesIntegrationHarness` will compose the new mixins and expose the exact same public methods, properties, and pytest fixtures. Existing tests in `tests/test_collection_scoped_variables_integration.py` and downstream suites will continue to run unchanged.
- **Q: How does this improve test execution and maintenance?**
  A: Decomposing into mixins allows test authors to create targeted fixtures tailored to specific subsystems (e.g. catalog tests, environment tests, or registry lifecycle tests). This improves test clarity, reduces unnecessary filesystem/server overhead, and makes adding new test capabilities modular and isolated.
