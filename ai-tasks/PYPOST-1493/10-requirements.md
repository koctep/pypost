# PYPOST-1493: Stabilize flaky MCP stdio harness stderr collection test

## Goals

Developers and CI must trust parallel `make test` for the shared MCP stdio test
harness. Captured child-process diagnostic output must be reliably observable
when a test asks for it, so intermittent empty-stderr failures do not obscure
real regressions or force noisy re-runs during the Test Gate Recovery sprint.

**Business reason (mandatory):** A flaky NON-BLOCKER
(`test_harness_stderr_collection`) already failed with empty `stderr_output`
under the full suite while passing alone and at base. Leaving the race
unfixed keeps the quality gate unreliable for MCP stdio IPC work that depends
on this harness.

**Implementation language:** Python

## User Stories

- As a **CI engineer**, I want
  `tests/test_mcp_stdio_harness.py::test_harness_stderr_collection` to pass
  consistently under parallel workers, so green builds reflect harness
  behavior rather than scheduling luck.
- As a **developer** writing MCP stdio tests, I want a bounded way to wait
  until expected stderr text appears, so I do not assert on an incomplete
  async drain snapshot.
- As a **maintainer** of the shared harness, I want stderr collection to be
  synchronized like response waits, so diagnostic assertions stay stable under
  load.

## Definition of Done

1. **Named flake green:** `test_harness_stderr_collection` passes reliably via
   `make test` (isolated and in the harness module suite).
2. **Deterministic contract:** An automated repro proves stderr emitted around
   a correlated response is observable through a bounded wait (not a bare
   immediate snapshot race).
3. **No unbounded waits:** All waits use explicit timeouts; module/tests keep
   `pytest.mark.timeout`.
4. **Make-only verification:** Confirmation uses `make test` / `make lint` (or
   `make check` as applicable)—no raw pytest/flake8 as the operator interface.
5. **Harness scope:** Fix lives in the test harness / tests; no change to
   production MCP server product behavior for end users.

## Task Description

### Problem

`McpStdioHarness` drains child stderr on a background thread. Callers that
`wait_for_response` then immediately call `get_stderr()` can observe an empty
string when the stderr worker has not yet appended drained lines—especially
under parallel pytest workers. Evidence: failed in full suite with empty
`stderr_output`; passed on re-run; passed at base
`4a40ff6b96994455e69d4da71ac02c8e235b89b0`.

**Exact identifier:**
`tests/test_mcp_stdio_harness.py::test_harness_stderr_collection`

**Repro command:** `make test PYTEST_ARGS=tests/test_mcp_stdio_harness.py`

### Scope (in)

- Stabilize stderr observation for the shared MCP stdio harness and its unit
  tests.
- Provide a bounded wait for expected stderr content (or equivalent
  synchronization).
- Document the stable usage pattern for developers.

### Scope (out)

- Disabling parallel pytest workers.
- Changing production MCP listen / product runtime semantics for end users.
- Unrelated flaky tickets outside this stderr collection race.

### Main Entities

- **Stdio Harness:** Test helper that owns a child process and async stream
  drains.
- **Stderr Snapshot:** Thread-safe accumulated child diagnostic text.
- **Correlated Response Wait:** Existing bounded wait for JSON-RPC responses
  on stdout.
- **Stderr Availability Wait:** Desired bounded wait until expected diagnostic
  text is present in the snapshot.

### Functional Requirements

- **FR-1:** After a child emits known stderr text, a test can wait (bounded)
  until that text is present in the harness stderr snapshot.
- **FR-2:** `test_harness_stderr_collection` must not fail due to empty
  stderr caused by async drain timing.
- **FR-3:** Immediate `get_stderr()` remains a non-blocking snapshot (no
  hidden infinite wait).

### Non-Functional Requirements

- **NFR-1 Reliability:** Stable under parallel `make test` workers.
- **NFR-2 Boundedness:** No unbounded sleeps or joins; explicit timeouts only.
- **NFR-3 Tooling:** Make-only repository operations.
- **NFR-4 Minimal surface:** Prefer small harness/test changes over broad
  refactors.

### Constraints and Assumptions

- **Constraint:** Jira scope is PYPOST-1493 only.
- **Constraint:** Make-only operator interface.
- **Assumption:** The underlying drain thread works; the defect is missing
  synchronization between drain completion and test assertions.
- **Assumption:** Filed flake is the same race class as post-response /
  concurrent stderr visibility, even when the child writes stderr before the
  response under lucky scheduling.

## Q&A

- **Q: Why is this Debt rather than a product bug?**
  **A:** It affects the test harness under parallel CI load; product MCP
  servers are unchanged. Triaged as NON-BLOCKER during PYPOST-1324.

- **Q: Why not only sleep in the flaky test?**
  **A:** Fixed sleeps do not close the race window and slow the suite.
  Bounded wait-for-content synchronizes on the actual drain.

- **Q: Who accepts Step 1?**
  **A:** Acceptance-gate owner after review; this execution leaves STEP 1
  as `[/]`.
