# Sprint 134 — Roadmap

> Date: 2026-03-25
> Methodology: Top-Down (Requirements → Architecture → Dev → Cleanup → Observability → Review →
> Docs → Commit)

## Sprint Steps

- [x] **STEP 1** — Sprint planning & backlog creation → `ai-sprints/134/10-sprint-backlog.md`
- [x] **STEP 2** — Junior Engineer sprint execution (agent-do.sh per issue) → `ai-sprints/134/40-sprint-execution.md`
- [x] **STEP 3** — Team Lead sprint report → `ai-sprints/134/90-sprint-report.md`

---

## Issue Progress

### Completed (Sprint 134 — Wave 1)

| Key | Summary | Status |
|-----|---------|--------|
| PYPOST-403 | [HP] Fix failing tests in CI | Done |
| PYPOST-404 | [Bug] Font size settings not applied on application startup | Done |
| PYPOST-405 | Open request in new independent tab | Done |

### New — Tech Debt (Sprint 134 — Wave 2)

| # | Key | Summary | Status |
|---|-----|---------|--------|
| 1 | PYPOST-89 | [PYPOST-52] No CI pipeline for tests | Done |
| 2 | PYPOST-88 | [PYPOST-52] No pytest cov-fail-under threshold | Done |
| 3 | PYPOST-83 | [PYPOST-52] Fragile positional call_args in test_request_service | Done |
| 4 | PYPOST-84 | [PYPOST-52] ScriptExecutor patch targets class not instance | Done |
| 5 | PYPOST-85 | [PYPOST-52] Private _collections mutation in reload test | Done |
| 6 | PYPOST-86 | [PYPOST-52] FakeStorageManager.saved_collections names only | Done |
| 7 | PYPOST-87 | [PYPOST-52] iter_content mock returns strings not bytes | Done |
| 8 | PYPOST-58 | [PYPOST-41 TD-1] HistoryManager tests bypass constructor via __new__ | Done |
| 9 | PYPOST-59 | [PYPOST-41 TD-2] Repeated import tempfile in test_history_manager | Done |
| 10 | PYPOST-60 | [PYPOST-41 TD-3] Vestigial tmp_path=None on test_load_missing_file | Done |
| 11 | PYPOST-79 | [PYPOST-44 TD-7] No unit tests for MetricsManager tracking | Done |
| 12 | PYPOST-92 | [PYPOST-10] Unit tests for tree state save/restore logic are missing | Done |
| 13 | PYPOST-93 | [PYPOST-10] No tests for edge cases | Done |
| 14 | PYPOST-95 | [PYPOST-10] Write tests to verify UI state preservation | Done |
| 15 | PYPOST-100 | [PYPOST-11] Unit tests for JsonHighlighter are missing | Done |
| 16 | PYPOST-103 | [PYPOST-11] Add tests for JsonHighlighter | Done |
| 17 | PYPOST-104 | [PYPOST-12] No tests: automated tests skipped | Done |
| 18 | PYPOST-108 | [PYPOST-12] Tests for CodeEditor | Done |
| 19 | PYPOST-110 | [PYPOST-12] Create tests for CodeEditor | Done |
| 20 | PYPOST-117 | [PYPOST-13] Unit tests for VariableHoverHelper and widgets are missing | Done |
| 21 | PYPOST-118 | [PYPOST-13] UI Tests: No automatic UI tests checking tooltip appearance | Done |
| 22 | PYPOST-121 | [PYPOST-13] Write unit tests for VariableHoverHelper | Done |
| 23 | PYPOST-125 | [PYPOST-14] No unit tests for save logic or settings persistence | To Do |
| 24 | PYPOST-130 | [PYPOST-15] Unit tests for VariableHoverHelper.resolve_text are missing | To Do |
| 25 | PYPOST-131 | [PYPOST-15] UI Tests: No automated UI tests to verify tooltip appearance | To Do |
| 26 | PYPOST-133 | [PYPOST-15] Write and commit unit tests for VariableHoverHelper | To Do |
| 27 | PYPOST-139 | [PYPOST-16] No automated tests for MCP server interaction | To Do |
| 28 | PYPOST-142 | [PYPOST-16] Add tests using an MCP client mock | To Do |
| 29 | PYPOST-56 | Add Qt-level UI tests for EnvironmentDialog | To Do |

---

## Execution Checklist

### PYPOST-403 · Fix failing tests in CI

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-403/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-403/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-403/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-403/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-403/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-403/70-dev-docs.md`
- [x] **Team Lead** — final commit (`afd2a58`)

### PYPOST-404 · Font size settings not applied on application startup

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-404/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-404/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-404/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-404/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-404/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-404/70-dev-docs.md`
- [x] **Team Lead** — final commit (`4ac96b8`, `cf45465`)

### PYPOST-405 · Open request in new independent tab

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-405/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-405/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-405/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-405/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-405/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-405/70-dev-docs.md`
- [x] **Team Lead** — final commit (`061a590`)

---

### Wave 2 — Tech Debt (29 issues)

#### Group A — Test Infrastructure (PYPOST-52)

##### PYPOST-89 · No CI pipeline for tests

- [x] **Junior Engineer** — implement CI pipeline for pytest
- [x] **Senior Engineer** — review & observability
- [x] **Team Lead** — final commit (`9f0a52d`)

##### PYPOST-88 · No pytest cov-fail-under threshold

- [x] **Junior Engineer** — add cov-fail-under to pytest config
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`df542ac`)

##### PYPOST-83 · Fragile positional call_args in test_request_service

- [x] **Junior Engineer** — refactor call_args assertions to keyword form
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`467c300`)

##### PYPOST-84 · ScriptExecutor patch targets class not instance

- [x] **Junior Engineer** — fix mock patch target
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`c65ebcd`)

##### PYPOST-85 · Private _collections mutation in reload test

- [x] **Junior Engineer** — replace internal mutation with public API
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`63c1a0d`)

##### PYPOST-86 · FakeStorageManager.saved_collections names only

- [x] **Junior Engineer** — extend fake to store full collection objects
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`8830703`)

##### PYPOST-87 · iter_content mock returns strings not bytes

- [x] **Junior Engineer** — fix mock to return bytes; HTTPClient decodes bytes in loop
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`d3189a0`)

#### Group B — HistoryManager Tests (PYPOST-41)

##### PYPOST-58 · HistoryManager tests bypass constructor via __new__

- [x] **Junior Engineer** — refactor to use proper constructor/fixture
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`a321608`)

##### PYPOST-59 · Repeated import tempfile in test_history_manager

- [x] **Junior Engineer** — deduplicate import
- [x] **Team Lead** — final commit (batched with PYPOST-58/60, `a321608`)

##### PYPOST-60 · Vestigial tmp_path=None on test_load_missing_file

- [x] **Junior Engineer** — remove dead parameter
- [x] **Team Lead** — final commit (batched with PYPOST-58/59, `a321608`)

#### Group C — MetricsManager Tests (PYPOST-44)

##### PYPOST-79 · No unit tests for MetricsManager tracking

- [x] **Junior Engineer** — write unit tests for MetricsManager
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`064eaa0`)

#### Group D — Tree State Tests (PYPOST-10)

##### PYPOST-92 · Unit tests for tree state save/restore logic are missing

- [x] **Junior Engineer** — write save/restore unit tests
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`51b9ab1`)

##### PYPOST-93 · No tests for edge cases

- [x] **Junior Engineer** — add edge-case tests
- [x] **Team Lead** — final commit (batched `51b9ab1`)

##### PYPOST-95 · Write tests to verify UI state preservation

- [x] **Junior Engineer** — add Qt-level state preservation tests
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`51b9ab1`)

#### Group E — JsonHighlighter Tests (PYPOST-11)

##### PYPOST-100 · Unit tests for JsonHighlighter are missing

- [x] **Junior Engineer** — document gap, prepare test plan (module docstring in test file)
- [x] **Team Lead** — final commit (batched with PYPOST-103)

##### PYPOST-103 · Add tests for JsonHighlighter

- [x] **Junior Engineer** — implement JsonHighlighter tests
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`cc171c3`)

#### Group F — CodeEditor Tests (PYPOST-12)

##### PYPOST-104 · No tests: automated tests skipped by user request

- [x] **Junior Engineer** — document gap, prepare test plan (module docstring)
- [x] **Team Lead** — final commit (batched with PYPOST-108/110)

##### PYPOST-108 · Tests for CodeEditor

- [x] **Junior Engineer** — write CodeEditor unit tests
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`f2b240c`)

##### PYPOST-110 · Create tests for CodeEditor

- [x] **Junior Engineer** — extend CodeEditor test suite
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`f2b240c`)

#### Group G — VariableHoverHelper Tests Batch 1 (PYPOST-13)

##### PYPOST-117 · Unit tests for VariableHoverHelper and widgets are missing

- [x] **Junior Engineer** — document gap, prepare test plan (module docstring)
- [x] **Team Lead** — final commit (batched with PYPOST-118/121)

##### PYPOST-118 · UI Tests: No automatic UI tests checking tooltip appearance

- [x] **Junior Engineer** — write Qt-level tooltip tests
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`827f16d`)

##### PYPOST-121 · Write unit tests for VariableHoverHelper

- [x] **Junior Engineer** — implement VariableHoverHelper unit tests
- [x] **Senior Engineer** — review
- [x] **Team Lead** — final commit (`827f16d`)

#### Group H — Settings Save Logic Tests (PYPOST-14)

##### PYPOST-125 · No unit tests for save logic or settings persistence

- [ ] **Junior Engineer** — write unit tests for save logic and settings persistence
- [ ] **Senior Engineer** — review
- [ ] **Team Lead** — final commit

#### Group I — VariableHoverHelper Tests Batch 2 (PYPOST-15)

##### PYPOST-130 · Unit tests for VariableHoverHelper.resolve_text are missing

- [ ] **Junior Engineer** — document gap, prepare test plan
- [ ] **Team Lead** — final commit (can batch with PYPOST-131/133)

##### PYPOST-131 · UI Tests: No automated UI tests to verify tooltip appearance

- [ ] **Junior Engineer** — write Qt-level tooltip tests for PYPOST-15 path
- [ ] **Senior Engineer** — review
- [ ] **Team Lead** — final commit

##### PYPOST-133 · Write and commit unit tests for VariableHoverHelper

- [ ] **Junior Engineer** — implement resolve_text unit tests
- [ ] **Senior Engineer** — review
- [ ] **Team Lead** — final commit

#### Group J — MCP Server Tests (PYPOST-16)

##### PYPOST-139 · No automated tests for MCP server interaction

- [ ] **Junior Engineer** — document gap, define mock strategy
- [ ] **Team Lead** — final commit (can batch with PYPOST-142)

##### PYPOST-142 · Add tests using an MCP client mock

- [ ] **Junior Engineer** — implement MCP client mock and test suite
- [ ] **Senior Engineer** — review
- [ ] **Team Lead** — final commit

#### Group K — EnvironmentDialog UI Tests

##### PYPOST-56 · Add Qt-level UI tests for EnvironmentDialog

- [ ] **Junior Engineer** — implement Qt-level dialog tests
- [ ] **Senior Engineer** — review
- [ ] **Team Lead** — final commit

---

## Project Manager Update

**Date**: 2026-03-26
**Phase**: `wave2_in_progress` — Group G (VariableHoverHelper batch 1) **complete**; next: Group H
  (PYPOST-125 settings save logic).

### Status

Sprint 134 Wave 1 is **complete** (3/3 done). Wave 2 **in progress** (22/29 done).

#### Wave 1 — Closed

| Key | Owner at Close | Final Commit | Result |
|-----|---------------|--------------|--------|
| PYPOST-403 | team_lead | `afd2a58` | Done — 5 CI failures resolved; test suite green (191 passed) |
| PYPOST-404 | team_lead | `4ac96b8`, `cf45465` | Done — Qt font-order bug fixed; 191 passed |
| PYPOST-405 | team_lead | `061a590` | Done — isolated-tab feature shipped |

#### Wave 2 — In Progress (22/29 done)

| Group | Issues | Status |
|-------|--------|--------|
| A — Test Infrastructure (PYPOST-52) | PYPOST-89 ✓, 88 ✓, 83 ✓, 84 ✓, 85 ✓, 86 ✓, 87 ✓ | Done |
| B — HistoryManager Tests (PYPOST-41) | PYPOST-58 ✓, 59 ✓, 60 ✓ | Done |
| C — MetricsManager Tests (PYPOST-44) | PYPOST-79 ✓ | Done |
| D — Tree State Tests (PYPOST-10) | PYPOST-92 ✓, 93 ✓, 95 ✓ | Done |
| E — JsonHighlighter Tests (PYPOST-11) | PYPOST-100 ✓, 103 ✓ | Done |
| F — CodeEditor Tests (PYPOST-12) | PYPOST-104 ✓, 108 ✓, 110 ✓ | Done |
| G — VariableHoverHelper Batch 1 (PYPOST-13) | PYPOST-117 ✓, 118 ✓, 121 ✓ | Done |
| H — Settings Save Logic (PYPOST-14) | PYPOST-125 | To Do |
| I — VariableHoverHelper Batch 2 (PYPOST-15) | PYPOST-130, 131, 133 | To Do |
| J — MCP Server Tests (PYPOST-16) | PYPOST-139, 142 | To Do |
| K — EnvironmentDialog UI Tests | PYPOST-56 | To Do |

#### Group A Completions (Wave 2)

| Key | Final Commit | Result |
|-----|--------------|--------|
| PYPOST-89 | `9f0a52d` | Done — GitHub Actions CI pipeline for pytest added |
| PYPOST-88 | `df542ac` | Done — cov-fail-under=50 threshold enforced |
| PYPOST-83 | `467c300` | Done — fragile positional call_args replaced with .kwargs assertions |
| PYPOST-84 | `c65ebcd` | Done — ScriptExecutor @staticmethod mock contract clarified |
| PYPOST-85 | `63c1a0d` | Done — `seed_collections()` public API; reload test decoupled from `_collections` |
| PYPOST-86 | `8830703` | Done — `saved_collections` holds full `Collection` instances |
| PYPOST-87 | `d3189a0` | Done — `iter_content` mocks yield bytes; HTTPClient decodes UTF-8 in loop |
| PYPOST-58/59/60 | `a321608` | Done — `history_path` injection; tests use constructor; tempfile import deduped |
| PYPOST-79 | `064eaa0` | Done — MetricsManager tracking tests; `request_errors` label uses category.value |
| PYPOST-92/93/95 | `51b9ab1` | Done — tree expand/restore round-trip, stale ids, subset `isExpanded` |
| PYPOST-100/103 | `cc171c3` | Done — JsonHighlighter tests via QTextLayout format ranges |
| PYPOST-104/108/110 | `f2b240c` | Done — CodeEditor reformat, paste, key indent/dedent tests |
| PYPOST-117/118/121 | `827f16d` | Done — VariableHoverHelper unit tests + QToolTip mouseMove tests |

### Carry-Forward Risks

- **RISK-1 (High)**: `AlertManager` not wired into `RequestWorker` (Sprint 100 TD-1, PYPOST-402).
  Alerts remain dead code in production. → Schedule alongside Wave 2 or next sprint.
- **RISK-2 (High)**: `default_retry_policy` has no runtime effect (Sprint 100 TD-2, PYPOST-402).
  Retry feature is inert end-to-end. → Schedule alongside Wave 2 or next sprint.

### New Backlog Items from Wave 1

| Ticket | Priority | Source |
|--------|----------|--------|
| PYPOST-406 | Medium | Unify left-click tree nav object-copying (PYPOST-405) |
| PYPOST-407 | Low | Deep-copy overhead watch (PYPOST-405) |
| PYPOST-408 | Medium | Stale-tab metadata sync event bus (PYPOST-405) |
| PYPOST-425 | Low | Remove redundant widget font loop (PYPOST-404 TD-1) |
| PYPOST-426 | Low | Add `AppSettings` type annotation to `apply_settings` (PYPOST-404 TD-2) |
| PYPOST-427 | Very Low | Document ConfigManager early-creation intent (PYPOST-404 TD-3) |
| — | Low | Investigate crash root cause (PYPOST-403) |
| — | Low | Replace SSE URL heuristic with content-type detection (PYPOST-403) |

### Next Action

- **Active**: PYPOST-125 — unit tests for settings save logic / persistence (Group H).
- Carry-forward: schedule PYPOST-402 TD-1 and TD-2 (AlertManager wiring, retry policy runtime).
