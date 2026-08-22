# Roadmap: PYPOST-1131

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1131-websocket-tls-security-policy

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements and document business scope in `ai-tasks/PYPOST-1131/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design TLS security policy, ephemeral trust decisions, and guardrails in `ai-tasks/PYPOST-1131/20-architecture.md`
  - [x] Specify automated Failing Repro design for Step 3
- [x] **STEP 3: Failing Repro Test**
  - [x] Author failing repro test suite in `tests/test_websocket_tls_policy.py`
- [x] **STEP 4: Development**
  - [x] Implement `pypost/core/websocket_security_policy.py` (Qt-free core security policy)
  - [x] Update `pypost/core/qt/websocket_transport.py` (secure QSslConfiguration, detailed QSslError extraction, eliminate blanket ignoreSslErrors)
  - [x] Update `pypost/core/qt/websocket_session.py` (ephemeral in-memory trust management and security classification signal emission)
  - [x] Verify all 15 tests pass in `tests/test_websocket_tls_policy.py`, along with static quality gates (`flake8`, `mypy`)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and formatting checks (flake8, mypy, line length <= 100)
  - [x] Create cleanup report in `ai-tasks/PYPOST-1131/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Implement structured debug logging and security status signals
  - [x] Add automated caplog tests in `tests/test_websocket_tls_policy.py`
  - [x] Create observability report in `ai-tasks/PYPOST-1131/50-observability.md`
  - [x] Add structured logging to `pypost/core/websocket_security_policy.py`, `pypost/core/qt/websocket_session.py`, and `pypost/core/qt/websocket_transport.py`
  - [x] Add caplog tests in `tests/test_websocket_tls_policy.py` verifying structured events and caplog error contract
  - [x] Document observability implementation and validation in `ai-tasks/PYPOST-1131/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts, missing tests, and performance considerations
  - [x] Document non-blocking follow-up tasks and dependencies
  - [x] Create technical debt report in `ai-tasks/PYPOST-1131/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Create comprehensive developer documentation in `doc/dev/websocket_tls_security.md` covering TLS policy, secure-by-default verification, diagnostic reports, ephemeral trust decisions, loopback detection, static guardrails, and troubleshooting
  - [x] Update `doc/dev/README.md` index with reference to `websocket_tls_security.md`
- [x] **COMMIT: Commit Changes**
  - Commit: `7c3e50fb4a7ccfd5da1bb2fe1f0497c2fc17384b` (`feat(websocket): PYPOST-1131 TLS and connection-security policy`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1131/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1131/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_tls_policy.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1131/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1131/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1131/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_tls_security.md`
- `doc/dev/README.md`

### COMMIT

- Commit hash: `7c3e50fb4a7ccfd5da1bb2fe1f0497c2fc17384b`
- Message: `feat(websocket): PYPOST-1131 TLS and connection-security policy`
- Branch: `feature/PYPOST-1131-websocket-tls-security-policy`
