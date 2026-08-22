# Roadmap: PYPOST-1127

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1127-websocket-transport-session-engine

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gathered business requirements, user stories, system boundaries, and Definition of Done for WS-1
  - [x] Defined core domain entities, non-functional requirements, and detailed user scenarios
  - [x] Established architectural isolation constraints (Qt-free core protocols, single Qt adapter, unmasked raw frames, no stream/env coupling in controller)
  - [x] Created `ai-tasks/PYPOST-1127/10-requirements.md` referencing PYPOST-1124 RFC specs (A-13.1)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Architectural research: verified PySide6.QtWebSockets runtime facts, LOC caps, layering constraints
  - [x] System module diagram and module breakdown (transport protocol, session policy, Qt transport adapter, Qt session controller)
  - [x] State machine transition rules, sequence diagrams, and signal ordering specification
  - [x] Interface definitions, API signatures, and architectural pattern selections
  - [x] Step 3 failing repro test design and implementation plan
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_session_engine_repro.py`
  - [x] `tests/test_websocket_import_isolation.py`
- [x] **STEP 4: Development**
  - [x] Implemented Qt-free transport protocol seam and immutable data models (`pypost/core/websocket_transport_protocol.py`)
  - [x] Implemented pure state machine, transition validation, and exponential backoff scheduler (`pypost/core/websocket_session_policy.py`)
  - [x] Implemented quarantined PySide6.QtWebSockets adapter (`pypost/core/qt/websocket_transport.py`)
  - [x] Implemented headless Qt session controller coordinating state transitions, heartbeat/reconnect QTimers, and unmasked raw frames (`pypost/core/qt/websocket_session.py`)
  - [x] Verified all red tests from Step 3 and added integration test suite with loopback `QWebSocketServer` (`tests/test_websocket_session_controller.py`)
  - [x] Verified zero flake8 warnings in `pypost/` and passed all test suites
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed shortcuts, code quality issues, missing tests, performance concerns, and follow-up tasks
  - [x] Created `ai-tasks/PYPOST-1127/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Created developer documentation in `doc/dev/websocket_session_engine.md` covering architecture, 4-module breakdown, API usage, state machine, quarantine constraints, and troubleshooting
  - [x] Indexed new documentation in `doc/dev/README.md`
  - [x] Verified documentation links with `scripts/check_user_docs_links.py` and lint checks
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1127/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1127/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1127/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1127/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1127/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_session_engine.md`
- `doc/dev/README.md`

### COMMIT

- `feat(websocket): PYPOST-1127 implement transport seam and Qt-native session engine`
