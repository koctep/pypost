# Roadmap: PYPOST-1430

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1430/10-requirements.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1430/20-architecture.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_wire_fuzzing_negative.py` (fails with AssertionError on missing suite categories)
  - [x] Acceptance gate review PASS
- [x] **STEP 4: Development**
  - [x] Implemented all 6 negative fuzzing fault categories in `tests/test_mcp_wire_fuzzing_negative.py`:
    - `http_framing`: non-numeric/negative Content-Length, invalid chunk hex sizes, premature EOF mid-chunk, missing header terminators, mismatched lengths.
    - `truncated_json`: mid-key, mid-string, mid-number, and unclosed object/array payloads returning JSON-RPC Parse Error (-32700).
    - `syntactically_invalid_json`: unescaped control chars, invalid unicode escapes, Python literals, and unquoted identifiers with fragmented delivery.
    - `jsonrpc_schema_violations`: non-object root arrays/primitives, unsupported versions, missing methods, invalid id types.
    - `raw_binary_noise`: non-UTF-8 binary bursts, binary noise in request lines, and UTF-8 pre-validation in `StreamableHTTPASGIApp` (`pypost/core/mcp_streamable_http.py`) returning HTTP 400 (-32700).
    - `interleaved_stress_and_recovery`: alternating bursts of malformed payloads followed by post-fault recovery verifying operational continuity.
  - [x] Initial repro test `test_negative_wire_fuzzing_initial_repro` updated and passing GREEN.
  - [x] Quality gates passed: `make test PYTEST_ARGS="tests/test_mcp_wire_fuzzing_negative.py"`, `make lint`, `make typecheck`, and `make verify-ai-tasks`.
  - [x] Acceptance gate review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Format and lint validation (`make lint`, `make typecheck`)
  - [x] Line length, imports, and cleanup verification (removed unused logging/logger, verified line lengths <= 100)
  - [x] Test suite and timeout markers verification (`make test PYTEST_ARGS="tests/test_mcp_wire_fuzzing_negative.py"`, `pytestmark = pytest.mark.timeout(30)`)
  - [x] Artifact integrity check (`make verify-ai-tasks`)
  - [x] `ai-tasks/PYPOST-1430/40-code-cleanup.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 6: Observability**
  - [x] Analyze observability requirements for negative wire fuzzing and protocol error handling
  - [x] Audit diagnostics, deterministic JSON-RPC error codes (-32700, -32600, -32602), and HTTP 400 mapping
  - [x] Verify zero credential/secret leakage and suppress raw binary dumps in logs and error responses
  - [x] Document logging structure, syslog level mapping, and transport metrics in `ai-tasks/PYPOST-1430/50-observability.md`
  - [x] Verify AI task artifacts integrity (`make verify-ai-tasks`)
  - [x] Acceptance gate review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality issues, missing tests, and performance concerns
  - [x] Link sprint follow-up issues (PYPOST-1431, PYPOST-1432, PYPOST-1434, PYPOST-1438) with non-blocker classification
  - [x] Create `ai-tasks/PYPOST-1430/60-tech-debt.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/mcp_standalone_wire_ipc_stress.md` (Negative Fuzzing & Wire Malformation Suite)
  - [x] Acceptance gate review PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1430/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1430/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1430/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1430/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1430/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
