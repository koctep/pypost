# PYPOST-1435: In-Memory Virtual Filesystem Backend for Integration Test Harness

## Goals

Integration and compatibility test suites in PyPost (such as variable resolution, multi-subsystem workflows, catalog discovery, and workspace environment synchronization) rely heavily on `CollectionVariablesIntegrationHarness`. To guarantee isolation, each test run dynamically provisions isolated directory trees on physical disk or temporary storage (via pytest's `tmp_path`), writing catalog manifests, collection definitions, local overlay configurations, and workspace environment JSON documents.

While isolating tests with physical filesystem directories guarantees sandbox safety, it introduces significant business, operational, and development challenges during high-frequency integration testing:
1. **Filesystem Latency and Test Suite Duration**: High-frequency matrix runs and comprehensive test suites execute hundreds of integration tests. Repeated physical disk operations (file creation, directory recursion, metadata flushing, and file deletion) introduce measurable I/O latency, slowing down local developer verification loops and elongating CI pipeline completion times.
2. **Disk I/O Contention in Parallel Execution**: Running test suites across parallel workers (e.g. multi-process test runners like `pytest-xdist`) leads to heavy concurrent read/write contention on the shared host disk, leading to non-deterministic execution times and occasional I/O timeouts.
3. **Inode Exhaustion and Disk Footprint Risks**: In constrained CI container environments and shared build runners, repeated creation of ephemeral directory hierarchies risks temporary partition exhaustion and inode depletion, causing abrupt build failures unrelated to application code quality.
4. **Filesystem Cleanup Overhead and File Lock Hazards**: Physical directory cleanup requires recursive disk traversal and file unlinking. On platforms or file systems with lingering file handles or delayed lock release, cleanup operations can trigger permission errors or leave abandoned temporary artifacts behind.

The primary goal of this task is to define requirements for an optional in-memory virtual filesystem backend or virtual storage adapter for `CollectionVariablesIntegrationHarness`. This capability allows integration test suites to execute entirely in memory, eliminating physical disk I/O, preventing filesystem contention, and dramatically speeding up test execution while maintaining 100% functional fidelity and complete backward compatibility with physical disk paths.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **PyPost test author**, I want an optional in-memory storage mode for `CollectionVariablesIntegrationHarness`, so that my integration tests execute rapidly in memory without incurring physical filesystem latency.
- As a **CI / DevOps engineer**, I want high-frequency test matrix runs to avoid physical disk writes, so that CI pipelines run faster, consume fewer disk I/O operations, and never fail due to runner inode or temporary storage exhaustion.
- As a **developer running parallel test suites**, I want isolated in-memory filesystems for each test harness instance, so that parallel workers do not contend for shared disk resources or suffer from filesystem lock conflicts.
- As an **integration test maintainer**, I want the in-memory virtual filesystem backend to maintain full behavioral and API parity with disk-based storage, so that test assertions and business logic verification produce identical results regardless of the storage backend.
- As a **codebase maintainer**, I want existing tests that pass physical filesystem paths (such as `tmp_path`) to continue working with zero modifications, so that adoption of the in-memory backend is completely safe and backward-compatible.
- As a **QA engineer**, I want teardown of in-memory test fixtures to be immediate and deterministic, so that all memory structures are released without requiring physical disk cleanup routines.

## Definition of Done

This task is considered complete when:
1. Business and functional requirements for an optional in-memory virtual filesystem backend and storage adapter are fully defined and documented.
2. The functional boundaries, scope, user stories, acceptance criteria, and domain entities are clearly specified without low-level implementation details.
3. Functional requirements ensure that `CollectionVariablesIntegrationHarness` and its constituent fixtures can operate against an in-memory storage backend with zero physical disk I/O.
4. Functional requirements ensure 100% backward compatibility for all existing tests and fixtures using physical paths (`tmp_path`).
5. Acceptance criteria clearly define behavioral parity between physical disk and in-memory storage for catalog manifests, collections, overlays, and workspace environments.
6. Acceptance criteria define deterministic lifecycle and cleanup expectations for in-memory resources upon harness exit or teardown.
7. Non-functional requirements specify performance improvements, concurrency isolation, and compliance with project quality standards.
8. Artifacts pass project verification (`make verify-ai-tasks` and `make check`).

## Task Description

### Problem Statement

Currently, `CollectionVariablesIntegrationHarness` provisions a physical directory tree rooted at a provided `tmp_path` (or equivalent filesystem path). During test lifecycle execution:
- It creates subdirectories: `libraries/`, `libraries_data/`, and `workspace/`.
- It writes connection configuration files (e.g. `connections.json`).
- It writes collection files (e.g. `<collection_id>.json`) and catalog manifests.
- It writes overlay secret records and profile metadata.
- It persists workspace environment JSON files through `StorageManager`.

While functional, this model forces every test to incur physical disk I/O overhead. In continuous integration environments and extensive matrix validation, this overhead aggregates into significant execution latency. Furthermore, running multi-worker test suites against physical filesystems leads to I/O bottlenecks and potential inode exhaustion. An in-memory virtual storage adapter provides the necessary abstraction to conduct test workflows in volatile memory, yielding immediate performance gains, reducing environmental dependencies, and guaranteeing clean resource isolation.

### Scope

- **In Scope**:
  - Requirements for an optional in-memory filesystem backend / virtual storage adapter for `CollectionVariablesIntegrationHarness`.
  - Requirements for supporting in-memory storage across all harness capabilities:
    - Library catalog creation and manifest storage.
    - Collection serialization and file retrieval.
    - Local overlay persistence and secret storage.
    - Workspace environment persistence and variable management.
  - Requirements for selecting between physical disk storage (default / legacy) and in-memory virtual storage.
  - Requirements for 100% backward compatibility with existing tests, methods, and fixture bindings (`collection_integration_harness`, `collection_harness`).
  - Requirements for deterministic disposal and memory reclamation upon harness teardown.
- **Out of Scope**:
  - Replacing the production storage layer default (production runtime persists to user data directories on disk).
  - Altering the standalone MCP server process transport or network protocol (MCP servers communicating via dynamic TCP sockets continue their standard communication).
  - Modifying external dependency contracts or breaking downstream test suites.

### Functional Requirements

- **FR1: Optional In-Memory Storage Backend Selection**:
  - The integration harness must provide an explicit, optional mechanism to enable in-memory storage instead of requiring a physical directory path.
  - When in-memory mode is activated, all filesystem operations managed by the harness must take place entirely in volatile memory with zero physical disk writes.
- **FR2: In-Memory Library and Manifest Management**:
  - The in-memory backend must support creating, reading, and enumerating library catalog structures, v1/v2 manifests, and collection definitions in memory.
  - Path traversal and file existence checks for collection and manifest files must behave identically to physical filesystem operations.
- **FR3: In-Memory Local Overlay Persistence**:
  - The in-memory backend must support saving and retrieving local library overlay profiles and secrets in memory.
  - Overlay retrieval must accurately reflect saved active profiles and secret dictionary states.
- **FR4: In-Memory Workspace Environment Management**:
  - The in-memory backend must support saving, loading, and querying workspace environment records and variables without writing JSON files to physical disk.
  - Environment variable encryption/decryption and secret masking workflows must remain fully functional in memory.
- **FR5: Complete Behavioral and API Fidelity**:
  - The in-memory backend must expose identical functional capabilities as the physical disk backend.
  - Method signatures, return types, and exceptions raised for missing or invalid data must match the behavior of the physical filesystem backend.
- **FR6: 100% Backward Compatibility**:
  - All existing tests passing a physical `Path` (such as pytest's `tmp_path`) to `CollectionVariablesIntegrationHarness` or using `collection_integration_harness` must continue to operate without code modifications or regressions.
  - Physical disk mode must remain available and fully functional.
- **FR7: Deterministic Cleanup and Resource Isolation**:
  - In-memory storage instances must be completely isolated between test harness runs to prevent state leakage across tests.
  - Harness teardown (via context manager exit or explicit `teardown()` / `close()`) must immediately drop in-memory references and release all allocated memory resources without leaving artifacts on disk.

### Non-Functional Requirements

- **NFR1: Performance & Zero Disk I/O**:
  - In-memory test execution must produce zero physical storage read/write calls for harness-managed files, reducing test execution latency and eliminating disk I/O wait times.
- **NFR2: Concurrency & Worker Isolation**:
  - Multiple test harness instances operating concurrently (e.g. across parallel pytest workers or threads) must maintain strictly partitioned in-memory states with zero cross-contamination.
- **NFR3: Memory Efficiency**:
  - In-memory storage footprint must remain minimal (< 10 MB per standard test harness instance) and be promptly garbage-collected upon teardown.
- **NFR4: Reliability & Robustness**:
  - In-memory storage operations must handle typical filesystem conditions (nested paths, overwrites, file existence checks, and non-existent lookups) reliably and consistently with standard POSIX path semantics.
- **NFR5: Maintainability and Tooling Standards**:
  - All requirements, architecture, code, and tests must adhere to project standards and pass all quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`).

### System Entities & Domain Perspective

- **Virtual Storage Adapter / Filesystem Driver**: Abstraction representing an ephemeral, in-memory filesystem capable of performing directory creation, file write, file read, and path resolution without physical storage interaction.
- **Ephemeral Storage Context**: The bounded domain context associated with an individual test harness execution, isolating its catalog files, overlay data, and workspace records from other tests.
- **Collection Variables Integration Harness**: The composite test orchestrator providing high-level test fixtures and end-to-end multi-subsystem workflows, adapted to operate against either a physical or in-memory storage backend.
- **Virtual Library Catalog Store**: In-memory domain entity holding test collection JSON documents, catalog manifests, and connection stores.
- **Virtual Overlay Store**: In-memory domain entity managing local profile overrides and secret mappings.
- **Virtual Workspace Environment Store**: In-memory domain entity managing environment variable collections and hidden key registries.

### User Scenarios & Use Cases

- **Scenario 1: High-Frequency Integration Matrix Test Execution**:
  A test runner executes a large matrix of collection variable resolution scenarios. Each test initializes `CollectionVariablesIntegrationHarness` configured with the in-memory backend. Catalogs, collections, and workspace environments are generated and queried purely in memory, completing the test suite without generating physical disk I/O and finishing significantly faster.
- **Scenario 2: Parallel Test Worker Execution Under xdist**:
  A developer runs `pytest -n auto` to execute tests across multiple CPU cores. Each worker provisions independent in-memory harness instances. Because no physical directories or temporary file locks are created on `/tmp`, workers run without storage contention, file collision, or runner slowdown.
- **Scenario 3: Legacy and Physical Path Compatibility**:
  An existing test suite uses `CollectionVariablesIntegrationHarness(tmp_path)` and inspects the generated directory structure on disk using standard `pathlib.Path` assertions. The harness recognizes the physical path input and executes using the standard disk-backed workflow without behavioral alterations.
- **Scenario 4: Resource-Constrained CI Runner Execution**:
  A continuous integration pipeline executes on a containerized runner with a small disk quota and restricted inode limits. Using the in-memory backend, the integration test suite runs to completion without allocating disk space or exhausting container inodes, and cleanly terminates without requiring temporary folder cleanup.

## Q&A

- **Q: Why is an in-memory virtual storage backend needed if pytest already uses `/tmp` or `tmp_path`?**
  A: While `tmp_path` provides directory sandboxing, it still interacts with physical storage (or tmpfs). In large integration matrix runs with hundreds of test cases and parallel workers, repeated directory creation, JSON serialization, and disk unlinking create I/O bottlenecks, risk inode exhaustion on CI runners, and incur filesystem cleanup overhead. An in-memory backend completely bypasses disk I/O, resulting in faster and more resilient test runs.
- **Q: Will switching to an in-memory backend break existing integration tests?**
  A: No. A mandatory requirement is 100% backward compatibility. The default or physical `tmp_path` constructor signature will continue to be fully supported, allowing existing test suites to run unchanged while enabling new or performance-critical tests to opt into in-memory execution.
- **Q: Does this change alter production storage behavior?**
  A: No. This task specifically targets the integration test infrastructure (`CollectionVariablesIntegrationHarness` and associated test fixture mixins). Production code continues to use standard persistent storage directories as configured.
- **Q: What entities in the harness require in-memory support?**
  A: All filesystem-dependent fixture components used during harness execution: library catalog directories, connection store files, collection JSON files, local overlay secret files, and workspace environment storage.
