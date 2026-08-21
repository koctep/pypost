# PYPOST-1062: Profile and Optionally Move Import Plan/Apply Off GUI Thread

## Goals

Ensure collection import remains responsive and does not degrade user experience during large or multi-collection import operations. Profile planning and application phases to establish whether main thread execution creates perceptible latency or if current synchronous plan/apply operations meet responsive interaction benchmarks.

## Background

In PYPOST-1005, collection file parsing was moved to background execution with busy cue feedback. However, post-parse operations (conflict resolution planning and applying changes to active collections) remained synchronous. This task validates whether processing large volumes of collection records introduces noticeable UI stalls during import planning or persistence.

## Scope

### In Scope
- Performance profiling and benchmarking of collection import planning and application workflows with realistic and stress-level dataset sizes (e.g., hundreds to thousands of collections and requests).
- Formulating concrete responsiveness criteria for the collection import process.
- Verifying whether plan and apply phases execute within acceptable interactive thresholds (< 100ms) or require background/chunked execution.
- Establishing test coverage that validates execution performance and ensures no regressions in import correctness.

### Out of Scope
- Redesigning conflict resolution dialog semantics or user interaction flows.
- Modifying storage formats or foreign collection importers (Postman/OpenAPI).

## Functional Requirements

1. **Import Execution Verification**: The system must accurately plan collection import actions (overwriting, keeping both, skipping, renaming duplicates) and persist applied collections without data corruption.
2. **Performance Measurement**: The system must measure and document timing characteristics for planning and applying collection imports across various workload sizes.
3. **Execution Strategy Alignment**:
   - If profiling demonstrates that plan/apply remains sub-millisecond or comfortably under GUI lag budgets for realistic collection collections, maintain synchronous simplicity with automated regression benchmarking.
   - If profiling exposes measurable UI stalls (> 100ms), establish off-thread execution or event loop yielding mechanisms.

## Non-Functional Requirements

1. **Responsiveness**: Collection import planning and application must not freeze or noticeably interrupt UI event processing for standard user workloads.
2. **Data Consistency**: Applying imported collections must guarantee transactional storage integrity; failure on one collection must not leave in-memory models out of sync with disk.
3. **Maintainability**: Profiling benchmarks and tests must be reproducible and execute efficiently within standard automated testing pipelines.

## User Scenarios

### Scenario 1: Importing Typical Workspaces
- **Given** a user imports a collection file containing 50-200 collections and several hundred requests.
- **When** the file is parsed and confirmed.
- **Then** the plan computation and application complete instantaneously with zero perceptible UI latency.

### Scenario 2: Stress-testing High-Volume Imports
- **Given** a user imports a bulk export containing thousands of collection items.
- **When** the plan is computed and applied.
- **Then** execution timings are measured and verified against responsiveness constraints.
