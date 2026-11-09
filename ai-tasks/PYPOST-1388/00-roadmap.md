# Roadmap: PYPOST-1388

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1388/10-requirements.md`
  - Inspected `pypost/core/json_selector_engine.py`, consumer paths (GUI mask formatter, MCP sanitizer), and originating debt notes from PYPOST-1378 / related masking work
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1388/20-architecture.md`
  - Decision: in-module segment trie (exact + `*` edges) + mutable path breadcrumbs; public `JsonSelectorEngine` API frozen; GUI formatter + MCP `redact_tree` both adopt stack tracking
  - Failing-repro design: `tests/test_pypost_1388_failing_repro.py` (parity lock + allocation/scaling red asserts)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1388_failing_repro.py`
  - Semantic lock (4 green): bare/dotted/wildcards, shorthand + header ignore, redact/format parity, empty short-circuit
  - Efficiency red (3 fail as intended): hierarchical O(R) scan budget, `redact_tree` path-list identity, `JsonMaskFormatter` path-list identity
  - Confirmed via `make test PYTEST_ARGS="tests/test_pypost_1388_failing_repro.py -v"` → 3 failed, 4 passed; no production changes
- [x] **STEP 4: Development**
  - [x] Implemented `PathSelectorTrie` + rewritten `JsonSelectorEngine.matches` / `_redact_node` (segment trie, push/pop breadcrumbs)
  - [x] Aligned `JsonMaskFormatter` to mutable path breadcrumb push/pop
  - [x] `tests/test_pypost_1388_failing_repro.py` green (7/7); related masking + PYPOST-1394 suites green
  - [x] Triaged full-suite pre-existing/flaky failures (NON-BLOCKER): PYPOST-1492, 1534, 1535, 1397, 1474, 1475, 1541 — recorded in `60-tech-debt.md`
- [x] **STEP 5: Code Cleanup**
  - Focus: `pypost/core/json_selector_engine.py`, `pypost/ui/widgets/response_mask_controller.py`, `tests/test_pypost_1388_failing_repro.py`
  - Artifact: `ai-tasks/PYPOST-1388/40-code-cleanup.md`
  - Fixed flake8 E302 in `response_mask_controller.py`; refreshed stale Step-3 comments in repro tests
  - Validated: `make lint`, `make typecheck`, focused `make test` (1388 + 1394) green
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1388/50-observability.md`
  - Light DEBUG: `json_selector_engine_compiled` now includes `trie_size`;
    `PathSelectorTrie.size` exposed for compile diagnostics; redact completion
    DEBUG retained; no per-match hot-path logging
  - Observability assert extended in `tests/test_pypost_1394_failing_repro.py`
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1388/60-tech-debt.md` (full template)
  - Debt: dual compile list+trie, unused `matches_tokens`, private FR-2 probe, stale
    `doc/dev/json_selector_engine.md` (Step 8), recursive walk / shorthand second walk
  - Missing tests: no isolated trie unit table / wildcard fan-out / deep recursion;
    timeout markers OK on 1388 repro
  - Follow-ups: new NON-BLOCKER cleanups + pre-existing suite failures (1492, 1534,
    1535, 1397, 1474, 1475, 1541) + 1389/1396; **0 blockers**
- [x] **STEP 8: Dev Docs**
  - `doc/dev/json_selector_engine.md` — PathSelectorTrie, breadcrumbs, performance, API
  - Related: `doc/dev/hidden_response_fields.md`, `doc/dev/README.md`, `doc/dev/response_mask_worker.md`
  - Debt filed for unticketed follow-ups: PYPOST-1542, 1543, 1544, 1545 (links in `60-tech-debt.md`)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1388/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1388/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1388_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1388/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1388/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1388/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/json_selector_engine.md`
- `doc/dev/hidden_response_fields.md` (section 5)
- `doc/dev/README.md`
- `doc/dev/response_mask_worker.md`
- Debt links: `ai-tasks/PYPOST-1388/60-tech-debt.md` (PYPOST-1542–1545)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
