# PYPOST-1452: Forward cancellation through nested get_connection/list_connections

## Goals

When an end-user or system process cancels a library operation (such as collection variable import, catalog discovery, or collection content inspection), the application must halt background processing promptly across all phases of the operation. In PYPOST-1425, low-level transport abort and cooperative cancellation tokens were introduced for remote collection fetches and catalog discovery. However, an operational gap was identified in nested helper routines: when higher-level workflows resolve individual library connections or look up manifest metadata, the nested connection resolution helpers perform store reads and discovery without receiving or forwarding the outer cancellation token.

From a business, UX, and operational perspective:
1. **Prompt User Responsiveness**: Users who dismiss import dialogs, rapidly switch selected collections, or cancel active background discoveries should not be subjected to delays while nested helper routines finish uncancellable disk reads or registry lookups.
2. **Elimination of Orphaned Work**: Uncancellable nested helper tasks consume CPU cycles, disk I/O, and worker thread capacity after the user has already requested cancellation, degrading overall application responsiveness.
3. **Consistency of Cooperative Cancellation Contracts**: A cancellation request issued at the workflow level must consistently propagate through every intermediate and nested helper layer down to the underlying store operations.
4. **Preservation of System Stability and Backward Compatibility**: Existing internal and external callers that invoke connection lookups without specifying cancellation parameters must continue to work seamlessly without regressions or unexpected signature incompatibilities.

## Programming Language

- **Implementation language**: Python

## User Stories

1. **Prompt Cancellation on Dismissal**: As a workspace user who cancels or closes the Collection Import dialog while connection metadata is being resolved, I want background processing to cease immediately so that the UI does not hang or delay dialog teardown.
2. **Responsive Switching of Selections**: As a workspace user quickly selecting different remote libraries or collections, I want previously initiated connection lookups to abort as soon as they are superseded, ensuring system resources remain focused on my current selection.
3. **Graceful Cancellation Reporting**: As a workspace user, when I cancel an operation during a nested library lookup, I want the system to cleanly acknowledge the cancellation without surfacing confusing errors or partial failure messages.
4. **Unbroken Backward Compatibility**: As a developer or maintainer calling connection lookup utilities, I want older call sites and test doubles that do not supply a cancellation token to continue functioning identically without requiring immediate refactoring.
5. **Deterministic Verification**: As an engineer maintaining the library subsystem, I want comprehensive test coverage demonstrating that cancellation signals are faithfully propagated through nested helpers and that operations exit promptly when cancelled.

## Definition of Done

1. **Nested Helper Cancellation Propagation**:
   - Every nested connection retrieval and listing helper within the library management and import workflows accepts and honors a cancellation token.
   - When a cancellation token is active, nested lookup routines forward the token into underlying connection listing, store loading, and predefined library discovery operations.
2. **Immediate Interruption on Cancellation**:
   - If a cancellation token is already in a cancelled state when a nested lookup is initiated, the operation halts immediately without performing disk I/O, store loading, or directory inspections.
   - If cancellation is requested while an iterative connection lookup or manifest inspection is in progress, the operation halts at the earliest cooperative checkpoint.
3. **Backward Compatibility**:
   - All connection lookup and listing methods remain callable without supplying a cancellation token, maintaining default non-cancelling execution.
   - Helper wrappers dynamically adapt when interacting with legacy services, mocks, or third-party doubles that do not accept cancellation parameters, avoiding unexpected keyword argument errors.
4. **Behavioral Integrity**:
   - For normal (non-cancelled) execution paths, return values, connection records, manifests, and diagnostic outputs remain identical in structure and content.
   - Cancelled lookups do not leave background operations in an inconsistent state or leak dangling resources.
5. **Quality Gates & Test Coverage**:
   - Automated unit tests verify both positive completion and early cancellation abort across nested connection lookup paths.
   - All repository static analysis, linting, typechecking, and test suites pass via `make check`.

## Task Description

### Problem Statement

During collection import and catalog discovery workflows, higher-level services invoke helper routines (such as resolving a specific connection or inspecting a manifest) that in turn call connection listing and storage loading functions. In the current implementation, outer operations accept a cooperative cancellation token, but when calling nested helpers to retrieve specific connection records or read manifests, the cancellation token is omitted.

As a result, store access, filesystem resolution, and predefined library discovery triggered inside these nested lookups run uncancellably. If a user cancels an operation while the system is resolving a connection or inspecting a manifest, execution continues until the nested store loading finishes, stalling worker teardown and wasting system resources.

### Business Reason

Maintaining a snappy, fluid desktop experience requires that user intent (such as hitting "Cancel" or closing a modal) takes precedence immediately. Even short delays caused by uncancellable nested filesystem or registry reads compound into noticeable latency, particularly on slower storage media or network-mounted volumes. Forwarding cancellation tokens across all intermediate helper layers guarantees uniform cancellation guarantees throughout the entire lifecycle of library operations.

### Functional Requirements

1. **Cancellation Token Forwarding**:
   - Higher-level library workflows must propagate the cancellation token to any nested connection lookup, manifest retrieval, or collection listing helper they invoke.
   - The connection lookup helper must forward the cancellation token to the underlying connection listing and storage access mechanisms.
2. **Cooperative Checkpoints in Nested Routines**:
   - Connection lookups and manifest loaders must inspect the cancellation token prior to initiating store reads or directory scans, and between discrete processing stages.
   - If cancellation is signaled, the helper must promptly terminate execution and raise the designated cancellation exception.
3. **Compatibility Fallback for Legacy Callers and Doubles**:
   - Helper callers must inspect target method capabilities (or employ safe invocation patterns) so that if a mock or legacy service does not support cancellation tokens, execution proceeds without error.
   - Existing public signatures must make the cancellation token an optional parameter with a default value of `None`.
4. **Clean Diagnostics and Observability**:
   - Operations terminated due to cancellation must record appropriate informational diagnostic logs without emitting false positive error-level alerts.

### Non-Functional Requirements

- **Latency / Promptness**: Cancellation response time through nested lookups must be near-instantaneous (sub-millisecond once the signal is asserted at a checkpoint).
- **Zero Overhead when Uncancelled**: Passing an optional cancellation token must introduce negligible overhead during normal, non-cancelled operation.
- **Robustness**: Thread cancellation signaling must be thread-safe and must not result in race conditions or orphaned background threads.
- **Maintainability**: Token forwarding conventions must follow consistent naming and parameter ordering across the codebase.

### System Boundaries and Scope

- **In Scope**:
  - `LibraryManagerService` connection lookup and manifest collection helpers.
  - `LibraryCollectionImportService` internal connection resolution and retrieval helpers.
  - Backward-compatible invocation patterns for cancellation tokens in nested helpers.
  - Unit and integration tests validating cancellation forwarding through nested helpers.
- **Out of Scope**:
  - Low-level network socket interrupt implementations (handled under PYPOST-1425 / PYPOST-1454).
  - Schema alterations for library manifests or connection records.
  - UI visual layout or widget modifications.

### Constraints and Assumptions

- Cooperative cancellation relies on explicit checkpoints; it does not forcibly terminate native blocking operating system calls unless paired with low-level abort callbacks.
- The standard `CancellationToken` abstraction from the core runtime is the authoritative mechanism for conveying cancellation state.
- Existing unit tests and mocks for `LibraryManagerService` and `LibraryCollectionImportService` may not supply cancellation tokens and must continue passing without modification.

### Edge Cases

1. **Pre-Cancelled Token**:
   - If the cancellation token has already been triggered before entering a nested lookup, the routine must immediately exit at the first checkpoint without performing store loading or filesystem I/O.
2. **Cancellation Mid-Lookup**:
   - If cancellation is signaled while the connection store is being iterated or after store load but before predefined library discovery, the next checkpoint must halt processing promptly.
3. **Missing or Stale Connection**:
   - If a connection record is not found during a lookup, the method must return its standard missing-record representation (`None` or designated exception) without masking or conflating with cancellation state.
4. **Caller Without Cancellation Support**:
   - When a helper interacts with a collaborator or mock object whose signature does not accept a cancellation token, the helper must fall back gracefully to calling the method without the token.
5. **No Token Provided (`None`)**:
   - When callers do not supply a cancellation token (passing `None` or relying on default arguments), the helpers must execute to full completion as standard non-cancellable operations.

### Backward Compatibility Rules

1. **Default Argument Rule**: Any signature change in public or internal helper methods must add `cancellation_token: CancellationToken | None = None` as an optional parameter with a default value of `None`.
2. **Mock Safety Rule**: Invocation of collaborator methods must not assume collaborator classes implement the new parameter; duck-typing or introspection should ensure compatibility with test mocks.
3. **Return Type Stability**: Return types, exception hierarchies for non-cancellation errors, and data structures must remain 100% unchanged.

## Main Entities

- **Cancellation Token (`CancellationToken`)**: Cooperative signaling object that carries cancellation state, supports callbacks, and provides check/throw methods when cancellation has been requested.
- **Library Connection Record (`LibraryConnectionRecord`)**: Authoritative entity describing a registered, cloned, or predefined library source (including its identity, local path, and metadata).
- **Library Manager Service (`LibraryManagerService`)**: Central business service managing the lifecycle, discovery, registration, and status of connected libraries.
- **Library Collection Import Service (`LibraryCollectionImportService`)**: Service responsible for discovering, resolving, and importing collection variables from connected libraries.
- **Connection Store (`LibraryConnectionStore`)**: Persistence and cache layer that reads and stores serialized library connection records.

## Q&A

- **Q: Why does `get_connection` need a cancellation token if it only fetches one record?**
  **A:** `get_connection` resolves records by calling `list_connections()`, which scans the connection store from disk and executes discovery for predefined libraries. On slower systems or network filesystems, this can block noticeably. Forwarding the token ensures these reads abort immediately if the user cancels.
- **Q: What happens if an older test mock for `LibraryManagerService` does not accept `cancellation_token` in `get_connection`?**
  **A:** The design enforces backward compatibility: callers will adaptively pass the cancellation token only when accepted by the callee, or fall back to calling without it, ensuring legacy test doubles do not break.
- **Q: Does this change the exception thrown when an operation is cancelled?**
  **A:** No. Cancellation raises the standard cooperative cancellation exception (`OperationCancelledError` / `CancellationError`), consistent with existing cancellation contracts across the project.
- **Q: Does this task modify UI presenter logic or dialogs?**
  **A:** Only in so far as passing existing tokens through presenter calls to the underlying service methods. No UI layouts, widgets, or user-facing strings are modified.
