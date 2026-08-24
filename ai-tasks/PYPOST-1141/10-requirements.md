# PYPOST-1141: WS: Add batch eviction calculation API to MessageStream to decouple StreamListModel

## Programming Language

Python is the implementation language for the core stream buffer, Qt list model, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost's WebSocket message stream (Epic PYPOST-1123, WS-3) provides a bounded in-memory ring buffer (`MessageStream`) and a virtualized Qt list model (`StreamListModel`) that synchronizes row insertion and FIFO eviction signals during high-throughput batch ingestion.

During WS-3 implementation, `StreamListModel.append_batch` duplicated eviction simulation logic and accessed `MessageStream` private attributes (`_entries`, `_retained_bytes`) to coordinate Qt `beginRemoveRows`/`beginInsertRows` signaling with buffer mutations. This coupling violates the architectural boundary between the Qt-free core buffer and the UI model layer, makes eviction math harder to test headlessly, and risks divergence if buffer internals change.

The goal of this tech-debt task is to **decouple eviction planning from the UI model** by exposing a public batch-eviction calculation API on `MessageStream`, so `StreamListModel` no longer needs to know eviction math or reach into private buffer state.

## User Stories

- As a **developer maintaining the WebSocket stream buffer**, I want batch eviction math centralized on `MessageStream`, so that capacity and memory-budget FIFO eviction rules stay consistent between single-entry `append` and UI batch ingestion.
- As a **UI engineer working on `StreamListModel`**, I want a public API that returns how many existing rows will be evicted and which new entries will be appended, so that I can emit precise Qt row signals without accessing private buffer members.
- As a **test author**, I want to verify batch eviction plans in pure Python without instantiating Qt, so that regression tests for eviction edge cases run quickly and headlessly.
- As an **architect reviewing WS-3 layering**, I want `StreamListModel` to depend only on public `MessageStream` methods, so that the Qt-free core module remains independently testable and evolvable.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Public Batch Eviction API on `MessageStream`:**
   - `MessageStream` exposes `calculate_batch_evictions(entries)` that simulates FIFO dual eviction (capacity count and memory budget) for a proposed batch without mutating the buffer.
   - The result includes: count of existing front rows to remove, per-cause drop counts (`capacity`, `memory_budget`), total evicted count, and the tuple of new entries to append after simulation.
2. **Public Batch Apply API on `MessageStream`:**
   - `MessageStream` exposes a method to apply a prior eviction plan (remove front rows, update drop counters, append new entries) so the UI model does not mutate `_entries` or `_retained_bytes` directly.
3. **`StreamListModel` Decoupling:**
   - `StreamListModel.append_batch` uses only public `MessageStream` APIs for eviction planning and buffer mutation.
   - `StreamListModel` no longer references `MessageStream._entries` or `MessageStream._retained_bytes`.
4. **Behavioral Preservation:**
   - Existing `StreamListModel.append_batch` eviction signaling, drop accounting, and stable `seq` identity behave identically to pre-refactor behavior.
   - Existing `MessageStream.append` single-entry behavior is unchanged.
5. **Automated Verification:**
   - Headless unit tests cover `calculate_batch_evictions` for capacity-only, memory-budget-only, and combined eviction scenarios.
   - An architectural test asserts `StreamListModel` does not access forbidden private members.
   - All affected WebSocket stream tests pass under `make test`.

## Task Description

### Problem Statement

`StreamListModel.append_batch` currently copies `list(self._stream._entries)`, simulates FIFO eviction inline, and then directly calls `popleft`, `append`, and `_retained_bytes` mutations on the underlying `MessageStream`. This duplicates eviction logic already present in `MessageStream.append` and tightly couples the UI model to buffer implementation details documented as technical debt in `ai-tasks/PYPOST-1130/60-tech-debt.md`.

### Scope

**In Scope:**

- Add `BatchEvictionPlan` (or equivalent) result type and `calculate_batch_evictions(entries)` on `MessageStream`.
- Add `apply_batch_evictions(plan)` (or equivalent) on `MessageStream` for atomic buffer mutation per plan.
- Refactor `StreamListModel.append_batch` to delegate eviction math and buffer writes to the new public APIs.
- Headless unit tests and architectural coupling test.
- Update `doc/dev/websocket_message_stream.md` to document the new API.

**Out of Scope:**

- Changing eviction policy (still dual FIFO: max entries + memory budget).
- Optimizing simulation to avoid list copy (deferred follow-up).
- Caching UTF-8 byte sizes on `StreamEntry` (separate tech debt).
- Changing `StreamListModel` as the sole UI writer invariant.

### Constraints and Assumptions

- `MessageStream` remains Qt-free; no PySide6 imports in `pypost/core/websocket_stream.py`.
- `StreamListModel.append_batch` remains the sole UI-thread mutation entry point for the ring buffer.
- Memory budget cost continues to use `len(entry.payload.encode("utf-8"))` consistent with existing `append` behavior.
- No user-visible behavior change; this is an internal API refactor.

## Functional Requirements

- **FR-1:** `calculate_batch_evictions(entries)` returns a structured plan with `existing_evicted`, `dropped_capacity`, `dropped_memory_budget`, `total_evicted`, and `entries_to_append`.
- **FR-2:** Empty `entries` input yields a zero-eviction plan with no entries to append.
- **FR-3:** `apply_batch_evictions(plan)` mutates the buffer exactly as the plan specifies and updates drop counters.
- **FR-4:** `StreamListModel.append_batch` emits the same Qt signals and returns the same `(inserted_count, evicted_count)` tuple as before.

## Non-Functional Requirements

- **NFR-1:** Headless testability — eviction planning testable without `QApplication`.
- **NFR-2:** Layering — no new Qt imports in core stream module.
- **NFR-3:** Minimal diff — preserve existing logging and observability events in `StreamListModel`.

## Main Entities

- **MessageStream:** Bounded FIFO ring buffer with dual eviction limits.
- **BatchEvictionPlan:** Immutable result of simulating a batch append (rows to remove, drop counts, entries to append).
- **StreamListModel:** Qt list model that coordinates batch ingestion with model signals.

## User Scenarios

### Scenario 1: Capacity eviction during batch append

1. A `MessageStream` with `max_entries=3` holds entries seq 1, 2, 3.
2. The UI model receives a batch of two new entries (seq 4, 5).
3. `calculate_batch_evictions` returns `existing_evicted=2`, `entries_to_append=(e4, e5)`.
4. `StreamListModel` emits `beginRemoveRows(0, 1)`, applies the plan, then `beginInsertRows` for the two new rows.
5. The model displays seq 3, 4, 5 with correct drop counters.

### Scenario 2: Headless unit test of memory-budget eviction

1. A test creates `MessageStream(max_entries=100, memory_budget_bytes=100)` pre-filled near budget.
2. It calls `calculate_batch_evictions` with a large payload entry.
3. The test asserts memory-budget evictions without starting Qt.

## Q&A

| Question | Answer |
| --- | --- |
| Why not move all of `append_batch` into `MessageStream`? | Qt row signals (`beginRemoveRows`, `beginInsertRows`) must be emitted by `StreamListModel`; only the eviction math and buffer mutation belong in the core buffer. |
| Why keep simulation-based eviction rather than deque-index math? | Behavioral parity with existing WS-3 logic is required; deque-index optimization is out of scope for this 1 SP debt item. |
| Does this change the sole-writer invariant? | No. `StreamListModel.append_batch` remains the only UI path that mutates `MessageStream`. |
