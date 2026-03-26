# Sprint 134 — Backlog

> Date: 2026-03-26
> Total issues: 32 (3 Wave 1 + 29 Wave 2); Wave 2 progress: 10/29 tech-debt items done (Groups A–B
> complete)
> Priority: Highest / High / Medium

## Completed Issues (carry-over, already Done)

| # | Key | Summary | Type | Priority | Status |
|---|-----|---------|------|----------|--------|
| — | PYPOST-403 | [HP] Fix failing tests in CI | Debt | Highest | Done |
| — | PYPOST-404 | [Bug] Font size settings not applied on application startup | Bug | High | Done |
| — | PYPOST-405 | Open request in new independent tab | Feature | High | Done |

---

## New Issues — Tech Debt (actionable, To Do)

| # | Key | Summary | Type | Priority | Status |
|---|-----|---------|------|----------|--------|
| 1 | PYPOST-89 | [PYPOST-52] No CI pipeline for tests | Debt | Medium | Done |
| 2 | PYPOST-88 | [PYPOST-52] No pytest cov-fail-under threshold | Debt | Medium | Done |
| 3 | PYPOST-83 | [PYPOST-52] Fragile positional call_args in test_request_service | Debt | Medium | Done |
| 4 | PYPOST-84 | [PYPOST-52] ScriptExecutor patch targets class not instance | Debt | Medium | Done |
| 5 | PYPOST-85 | [PYPOST-52] Private _collections mutation in reload test | Debt | Medium | Done |
| 6 | PYPOST-86 | [PYPOST-52] FakeStorageManager.saved_collections names only | Debt | Medium | Done |
| 7 | PYPOST-87 | [PYPOST-52] iter_content mock returns strings not bytes | Debt | Medium | Done |
| 8 | PYPOST-58 | [PYPOST-41 TD-1] HistoryManager tests bypass constructor via __new__ | Debt | Medium | Done |
| 9 | PYPOST-59 | [PYPOST-41 TD-2] Repeated import tempfile in test_history_manager | Debt | Medium | Done |
| 10 | PYPOST-60 | [PYPOST-41 TD-3] Vestigial tmp_path=None on test_load_missing_file | Debt | Medium | Done |
| 11 | PYPOST-79 | [PYPOST-44 TD-7] No unit tests for MetricsManager tracking | Debt | Medium | To Do |
| 12 | PYPOST-92 | [PYPOST-10] Unit tests for tree state save/restore logic are missing | Debt | Medium | To Do |
| 13 | PYPOST-93 | [PYPOST-10] No tests for edge cases (ID exists in settings but not in collection) | Debt | Medium | To Do |
| 14 | PYPOST-95 | [PYPOST-10] Write tests to verify UI state preservation | Debt | Medium | To Do |
| 15 | PYPOST-100 | [PYPOST-11] Unit tests for JsonHighlighter are missing | Debt | Medium | To Do |
| 16 | PYPOST-103 | [PYPOST-11] Add tests for JsonHighlighter | Debt | Medium | To Do |
| 17 | PYPOST-104 | [PYPOST-12] No tests: creation of automated tests was skipped by user request | Debt | Medium | To Do |
| 18 | PYPOST-108 | [PYPOST-12] Tests for CodeEditor | Debt | Medium | To Do |
| 19 | PYPOST-110 | [PYPOST-12] Create tests for CodeEditor | Debt | Medium | To Do |
| 20 | PYPOST-117 | [PYPOST-13] Unit tests for VariableHoverHelper and widgets are missing | Debt | Medium | To Do |
| 21 | PYPOST-118 | [PYPOST-13] UI Tests: No automatic UI tests checking tooltip appearance | Debt | Medium | To Do |
| 22 | PYPOST-121 | [PYPOST-13] Write unit tests for VariableHoverHelper | Debt | Medium | To Do |
| 23 | PYPOST-125 | [PYPOST-14] No unit tests were added for the save logic or settings persistence | Debt | Medium | To Do |
| 24 | PYPOST-130 | [PYPOST-15] Unit tests for VariableHoverHelper.resolve_text are missing | Debt | Medium | To Do |
| 25 | PYPOST-131 | [PYPOST-15] UI Tests: No automated UI tests to verify tooltip appearance | Debt | Medium | To Do |
| 26 | PYPOST-133 | [PYPOST-15] Write and commit unit tests for VariableHoverHelper | Debt | Medium | To Do |
| 27 | PYPOST-139 | [PYPOST-16] No automated tests for MCP server interaction | Debt | Medium | To Do |
| 28 | PYPOST-142 | [PYPOST-16] Add tests using an MCP client mock | Debt | Medium | To Do |
| 29 | PYPOST-56 | Add Qt-level UI tests for EnvironmentDialog | Debt | Medium | To Do |

---

## Execution Order & Rationale

### Group A — Test Infrastructure (PYPOST-52)

Foundational test-infrastructure fixes must land first so all subsequent test-writing work
benefits from a stable, reliable pipeline.

#### 1 · PYPOST-89 — No CI pipeline for tests

**Rationale:** Highest priority among all new items. Without a CI pipeline, all newly added tests
will only run locally, defeating their purpose. Must be resolved before any other test is written.

#### 2 · PYPOST-88 — No pytest cov-fail-under threshold

**Rationale:** Enforces a coverage floor so future test additions have a quality gate. Set up
alongside CI (#1) as a one-pass infrastructure change.

#### 3 · PYPOST-83 — Fragile positional call_args in test_request_service

**Rationale:** Brittle assertions break on minor signature changes. Fix before adding more tests
in the same area to avoid propagating the pattern.

#### 4 · PYPOST-84 — ScriptExecutor patch targets class not instance

**Rationale:** Incorrect mock target means tests pass for the wrong reason. Fix to establish a
correct mock baseline used by later CodeEditor tests.

#### 5 · PYPOST-85 — Private _collections mutation in reload test

**Rationale:** Tests that mutate internal state are fragile and mask real bugs. Fix before adding
tree-state and storage tests.

#### 6 · PYPOST-86 — FakeStorageManager.saved_collections names only

**Rationale:** Incomplete fake leads to false-positive tests. Fix the fake before relying on it
in new tests (#12–#14).

#### 7 · PYPOST-87 — iter_content mock returns strings not bytes

**Rationale:** Type mismatch in mock causes silent failures when response body processing is
tested. Fix before expanding request-service test coverage.

---

### Group B — HistoryManager Tests (PYPOST-41)

Clean up existing HistoryManager tests now that CI is stable (PYPOST-403 already fixed the race
condition; these are code-quality issues in the test suite itself).

#### 8 · PYPOST-58 — HistoryManager tests bypass constructor via __new__

**Rationale:** Bypassing __init__ hides dependency injection bugs. Refactor to use a proper
constructor or fixture.

#### 9 · PYPOST-59 — Repeated import tempfile in test_history_manager

**Rationale:** Minor hygiene. Resolved in same pass as #8 to keep the file clean.

#### 10 · PYPOST-60 — Vestigial tmp_path=None on test_load_missing_file

**Rationale:** Dead parameter causes confusion. Remove in the same pass as #8–#9.

---

### Group C — MetricsManager Tests (PYPOST-44)

#### 11 · PYPOST-79 — No unit tests for MetricsManager tracking

**Rationale:** MetricsManager is an internal service with no test coverage. Add unit tests to
establish a baseline before any future changes to metrics collection.

---

### Group D — Tree State Tests (PYPOST-10)

#### 12 · PYPOST-92 — Unit tests for tree state save/restore logic are missing

**Rationale:** Core persistence logic for the tree widget has no unit tests. Start with the
happy-path save/restore cycle.

#### 13 · PYPOST-93 — No tests for edge cases (ID exists in settings but not in collection)

**Rationale:** Edge-case coverage for mismatched state. Add alongside #12 in the same test module.

#### 14 · PYPOST-95 — Write tests to verify UI state preservation

**Rationale:** Qt-level state preservation tests complement the unit tests in #12–#13.

---

### Group E — JsonHighlighter Tests (PYPOST-11)

#### 15 · PYPOST-100 — Unit tests for JsonHighlighter are missing

**Rationale:** Analysis/discovery ticket — confirms gap. Resolve by writing the tests in #16.

#### 16 · PYPOST-103 — Add tests for JsonHighlighter

**Rationale:** Implementation of the tests identified by #15. Pair together in a single pass.

---

### Group F — CodeEditor Tests (PYPOST-12)

#### 17 · PYPOST-104 — No tests: automated tests skipped by user request

**Rationale:** Documents the coverage gap for CodeEditor. Resolve by writing the tests in #18–#19.

#### 18 · PYPOST-108 — Tests for CodeEditor

**Rationale:** Adds unit-level test coverage for CodeEditor core behaviour.

#### 19 · PYPOST-110 — Create tests for CodeEditor

**Rationale:** Extends #18 with additional test scenarios identified during review.

---

### Group G — VariableHoverHelper Tests — Batch 1 (PYPOST-13)

#### 20 · PYPOST-117 — Unit tests for VariableHoverHelper and widgets are missing

**Rationale:** Gap analysis. Resolves alongside #21–#22.

#### 21 · PYPOST-118 — UI Tests: No automatic UI tests checking tooltip appearance

**Rationale:** Qt-level tooltip tests require a running QApplication. Add as a separate
test class within the same module.

#### 22 · PYPOST-121 — Write unit tests for VariableHoverHelper

**Rationale:** Implementation of the unit tests from #20–#21.

---

### Group H — Settings Save Logic Tests (PYPOST-14)

#### 23 · PYPOST-125 — No unit tests for save logic or settings persistence

**Rationale:** Settings persistence is user-critical functionality with zero test coverage.

---

### Group I — VariableHoverHelper Tests — Batch 2 (PYPOST-15)

PYPOST-15 introduced resolve_text; tests are missing. Batch 2 may overlap with Group G but
targets different methods.

#### 24 · PYPOST-130 — Unit tests for VariableHoverHelper.resolve_text are missing

**Rationale:** resolve_text is the key transformation method; must be unit-tested in isolation.

#### 25 · PYPOST-131 — UI Tests: No automated UI tests to verify tooltip appearance

**Rationale:** Qt-level verification for PYPOST-15 tooltip path.

#### 26 · PYPOST-133 — Write and commit unit tests for VariableHoverHelper

**Rationale:** Implementation commit for #24–#25.

---

### Group J — MCP Server Tests (PYPOST-16)

#### 27 · PYPOST-139 — No automated tests for MCP server interaction

**Rationale:** MCP integration is tested only manually. Document gap and introduce mock strategy.

#### 28 · PYPOST-142 — Add tests using an MCP client mock

**Rationale:** Implement the mock-based test suite for MCP server interaction identified in #27.

---

### Group K — EnvironmentDialog UI Tests

#### 29 · PYPOST-56 — Add Qt-level UI tests for EnvironmentDialog

**Rationale:** UI dialog with no automated tests. Placed last as it requires a stable Qt test
harness established by earlier groups.

---

## Notes

- Items PYPOST-89 through PYPOST-87 (Group A) are **Done**; remaining Wave 2 items are type
  **Debt**, priority **Medium**, status **To Do** unless noted in
  [00-roadmap.md](00-roadmap.md).
- Execution order follows: infrastructure → existing-test cleanup → new unit tests →
  new UI/integration tests.
- PYPOST-89 (CI pipeline) is the single highest-priority item; it unblocks the quality
  gate for all subsequent test work.
- Groups G and I both target VariableHoverHelper but for different feature branches
  (PYPOST-13 vs PYPOST-15); keep them in separate test modules to avoid merge conflicts.
