# Roadmap: PYPOST-1142

## Task Metadata

- **Implementation language**: Python (test infrastructure — `tests/websocket_echo_server.py`, PySide6 / Qt WebSockets, `cryptography` for ephemeral X.509 generation)
- **Branch name**: `test/PYPOST-1142-tls-test-server` *(reference only, do not switch)*

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1142/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1142/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - `tests/test_websocket_tls_echo_server.py` (red tests for missing TLS harness; green after Step 4)
- [/] **STEP 4: Development**
  - [x] Added `tests/tls_test_certs.py` with `TlsCertProfile` and ephemeral certificate generation
  - [x] Extended `ScriptedWebSocketServer` with optional `tls_profile` and `wss://` URL support
  - [x] Added `wss_test_server*` pytest fixtures in `tests/conftest.py`
  - [x] Added `tests/test_websocket_tls_echo_server.py` (9 tests, all green)
- [/] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1142/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1142/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1142/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - `doc/dev/websocket_test_harness.md` — TLS profiles and `wss_test_server` fixtures
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1142/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1142/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_tls_echo_server.py`

### STEP 4: Development

- `tests/tls_test_certs.py`
- `tests/websocket_echo_server.py`
- `tests/conftest.py`
- `tests/test_websocket_tls_echo_server.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1142/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1142/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1142/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_test_harness.md`

### COMMIT

- *(pending — commit prep only)*
