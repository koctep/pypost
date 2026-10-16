# PYPOST-1417: Reusable Multi-Subsystem Integration Harness Helper

## Goals

Integration tests verifying interactions across collections, library manifests, standalone MCP servers, environment variables, and execution engines require complex scaffolding across multiple subsystem boundaries. In [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412), `CollectionVariablesIntegrationHarness` was introduced directly within `tests/test_collection_scoped_variables_integration.py` to orchestrate isolated catalogs, filesystem directories, local overlays, and server registries.

However, leaving integration harness logic embedded within a single test module creates technical debt and operational risks:
1. **Scaffolding Duplication Across Suites**: Future end-to-end integration and repro test suites (e.g., standalone execution, wire IPC, workspace variable synchronization, and concurrent server lifecycles) duplicate filesystem setup, service bootstrapping, and teardown logic.
2. **Resource Leakage and Test Flakiness**: Without standardized fixture lifecycle integration, tests rely on manual `try ... finally` blocks to shut down background servers, release network sockets, and clean up filesystem directories. Unhandled exceptions or omitted finally blocks risk leaking background threads and bound sockets, causing flaky port collisions in subsequent tests or CI runner timeouts.
3. **Inconsistent Test State Isolation**: Multi-subsystem tests require coordinated temp paths, storage managers, and connection stores. A centralized helper ensures uniform isolation boundaries and prevents cross-test contamination.

The goal of this task is to extract and generalize `CollectionVariablesIntegrationHarness` into a reusable, shared test helper located at `tests/helpers/collection_integration_harness.py`, equipped with idiomatic pytest fixture lifecycle management, guaranteed automated registry teardown, and seamless backward compatibility for existing integration tests.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **PyPost test author**, I want a reusable multi-subsystem integration harness helper in `tests/helpers/`, so that I can write end-to-end integration tests without duplicating catalog setup, storage initialization, or server registry coordination.
- As a **QA / CI engineer**, I want all integration tests consuming multi-subsystem harnesses to guarantee automated teardown of servers, threads, and sockets upon completion or failure, so that CI test runners do not suffer from port exhaustion, thread leakage, or cascading test failures.
- As a **codebase maintainer**, I want `tests/test_collection_scoped_variables_integration.py` and downstream test suites to import and consume the centralized harness helper seamlessly without regressions or behavioral discrepancies.
- As a **developer testing standalone MCP servers and collection variables**, I want fluent utilities for programmatically creating test libraries, collections, variables, presets, and overlays, so that test scenarios remain concise, readable, and maintainable.

## Definition of Done

This task is considered complete when:
1. `CollectionVariablesIntegrationHarness` is extracted from `tests/test_collection_scoped_variables_integration.py` into `tests/helpers/collection_integration_harness.py` as a reusable component.
2. The shared helper coordinates the initialization and lifecycle of core multi-subsystem services:
   - Filesystem directories (libraries, workspace, overlay data)
   - `StorageManager`
   - `LibraryConnectionStore`
   - `LocalOverlayManager`
   - `LibraryManagerService`
   - `LibraryRuntimeResolver`
   - `MCPServerRegistry`
   - `TemplateService`
   - `RequestService` integration or mock dispatch capabilities
3. Idiomatic pytest fixture bindings are provided (e.g. `collection_harness` fixture or context-manager helper) ensuring guaranteed teardown (`registry.stop_all()`, thread cleanup, and temporary resource release) even when test assertions fail.
4. Programmatic library and collection creation utilities allow flexible definition of:
   - Modern catalog-only manifests and legacy manifests with root variables/presets
   - Self-contained collection files with variables, presets, and requests
   - Local overlay secrets and active profiles
   - Workspace environments with variables and hidden keys
5. Standalone MCP server registration and execution utilities are supported:
   - Conflict-free dynamic port allocation
   - Server registration, candidate validation, and lifecycle startup/status tracking
6. Unified end-to-end lifecycle execution orchestration (`run_unified_lifecycle`) is supported with customizable input parameters and structured execution outcome reporting.
7. Existing integration tests in `tests/test_collection_scoped_variables_integration.py` are refactored to consume the shared helper without any behavioral regressions or test failures.
8. Non-functional quality gates pass:
   - All tests execute within bounded timeouts (< 30s per `do-testing` contracts).
   - Strict typing annotations and comprehensive Google-style docstrings are applied.
   - All repository checks (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) pass cleanly.

## Task Description

### Problem Statement

During the implementation of collection-scoped variable architecture in PYPOST-1412, `CollectionVariablesIntegrationHarness` was co-located with `test_collection_scoped_variables_integration.py`. As identified in [PYPOST-1412 Technical Debt](file:///home/src/ai-tasks/PYPOST-1412/60-tech-debt.md), this in-test co-location creates significant code duplication for adjacent tasks (such as PYPOST-1416 and PYPOST-1418) and leaves resource lifecycle management vulnerable to manual error. Moving this harness into `tests/helpers/collection_integration_harness.py` establishes a standard integration foundation across the test suite.

### Scope

- **In Scope**:
  - Extract `CollectionVariablesIntegrationHarness` and `UnifiedLifecycleResult` into `tests/helpers/collection_integration_harness.py`.
  - Provide a pytest fixture binding with generator/context-manager teardown that stops all registered servers and cleans up resources.
  - Provide helper methods for generating test libraries, collections, manifests, workspace environments, and overlay secrets.
  - Provide helper methods for registering, validating, and starting standalone MCP servers with dynamic port binding.
  - Refactor `tests/test_collection_scoped_variables_integration.py` to import and utilize the shared helper and fixture.
  - Verify that all existing integration and unit tests pass without regressions.
- **Out of Scope**:
  - Altering production application business logic in `pypost/` modules.
  - Modifying the underlying JSON-RPC protocol transport implementations.
  - Re-architecting unrelated unit test suites outside integration harness consumers.

### Functional Requirements

- **FR1: Reusable Multi-Subsystem Harness Core**: The harness must encapsulate and coordinate the initialization of `StorageManager`, `LibraryConnectionStore`, `LocalOverlayManager`, `TemplateService`, `LibraryManagerService`, `LibraryRuntimeResolver`, `MCPServerRegistry`, and request execution services within an isolated temporary filesystem hierarchy.
- **FR2: Pytest Fixture Lifecycle & Automated Teardown**: The harness must provide an idiomatic pytest fixture binding that yields the initialized harness instance and guarantees automatic post-test teardown (stopping all registered servers, clearing background execution states, and releasing network resources), regardless of test outcome.
- **FR3: Programmatic Scoped Catalog & Collection Creation**: The harness must provide helper methods to programmatically generate valid directory structures, catalog manifests (both modern v2 catalog manifests and legacy v1 manifests with root variables/presets), collection JSON definitions with variables and requests, and local overlay secret files.
- **FR4: Programmatic Workspace Environment Creation**: The harness must provide helper methods to create and persist isolated workspace environments with predefined variables and secret-masking keys.
- **FR5: Standalone MCP Server Lifecycle Management**: The harness must provide helper methods to register, validate, and launch standalone MCP servers backed by library collections using dynamic non-conflicting TCP port allocation, verifying operational status transitions.
- **FR6: Unified Multi-Subsystem Lifecycle Orchestration**: The harness must provide an end-to-end execution workflow (`run_unified_lifecycle`) that coordinates catalog discovery, standalone server startup, collection variable importing, and template substitution, returning a structured result object.
- **FR7: Backward Compatibility & Test Migration**: `tests/test_collection_scoped_variables_integration.py` must be updated to import and utilize the extracted helper and fixture without altering existing assertion coverage or test semantics.

### Non-Functional Requirements

- **NFR1: Performance & Bounded Execution**: All test executions leveraging the harness must be deterministic, fast (< 500ms per test case on average), and strictly adhere to repository timeout contracts (explicit `@pytest.mark.timeout(30)`).
- **NFR2: Resource Hygiene**: Every test run using the harness must cleanly release all bound TCP sockets, terminate background server threads, and avoid leaking state across test runs.
- **NFR3: Typing & Documentation Standards**: The helper module must include complete type annotations adhering to PEP 484 / PEP 561, passing `make typecheck` cleanly, and must feature comprehensive docstrings following Google-style documentation conventions.
- **NFR4: Tooling Standard Compliance**: Verification of changes must strictly follow repository rules using `make` targets (`make check`, `make test`, `make lint`, `make typecheck`, `make verify-ai-tasks`).

### System Entities & Domain Interplay

- **Integration Harness**: The central coordinator orchestrating isolated directories, storage, library management, variable resolution, and server registry for a single test execution context.
- **Pytest Fixture Binding**: The lifecycle manager providing seamless dependency injection into test functions and ensuring guaranteed post-test cleanup.
- **Test Catalog & Collection**: Ephemeral, valid library and collection filesystem artifacts generated dynamically for testing manifest compatibility and variable inheritance.
- **Standalone Server Instance**: An in-process or local MCP server configured from a library collection and registered in the test registry.
- **Unified Lifecycle Result**: A structured value object summarizing the end-to-end execution outcome, including server status, variable import counts, and template rendering results.

### User Scenarios & Use Cases

- **Scenario 1: End-to-End Collection Variable Workflow Test**:
  A test function requests the `collection_harness` fixture, creates a library with custom variables and requests, starts a standalone server, imports variables into an environment, and verifies rendered template strings. Upon test completion, the fixture automatically shuts down the server.
- **Scenario 2: Compatibility Matrix Permutation Testing**:
  A parameterized test invokes the harness across diverse combinations of legacy and modern manifests. Each iteration runs in an isolated directory and ensures all registry entries are cleaned up prior to the next parameter iteration.
- **Scenario 3: Error and Diagnostic Safety Testing**:
  A test simulates missing required variables or invalid manifests using the harness. An expected exception is raised, and the fixture teardown ensures any partially initialized server or registry state is cleaned up without impacting subsequent tests.

## Q&A

- **Q: Why should `CollectionVariablesIntegrationHarness` be moved to `tests/helpers/` instead of staying in `tests/test_collection_scoped_variables_integration.py`?**
  A: Co-locating the harness in a test file prevents other integration test suites (e.g. standalone execution repros, wire IPC tests, concurrent server lifecycle tests) from reusing the setup logic without circular or unnatural imports. Placing it in `tests/helpers/` establishes a first-class shared helper module.
- **Q: How does the fixture lifecycle improve reliability over manual `try ... finally` blocks?**
  A: Manual cleanup blocks are easy to omit or misconfigure when new tests are added. A generator-based pytest fixture (`yield harness`) guarantees teardown execution even in the face of unexpected assertion errors or early returns, eliminating leaked background threads and stuck TCP ports.
- **Q: Should the helper modify production classes in `pypost/`?**
  A: No. The helper operates entirely within the test harness layer (`tests/helpers/`), consuming existing public and internal service contracts to orchestrate test scenarios without altering runtime production logic.
