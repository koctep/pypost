# Roadmap: PYPOST-46

**Jira:** [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46) — Introduce HTTPClient protocol and inject into RequestService

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-46-http-client-protocol`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `HTTPClientProtocol` in `pypost/core/http_client_protocol.py`
  - [x] Typed `RequestService.http_client` injection as `HTTPClientProtocol`
  - [x] Added `tests/test_http_client_protocol.py`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-46/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-46/20-architecture.md`

### STEP 3: Development

- `pypost/core/http_client_protocol.py`
- `pypost/core/request_service.py`
- `tests/test_http_client_protocol.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-46/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-46/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-46/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-46/70-dev-docs.md`
- `doc/dev/testability.md`
- `doc/dev/solid_audit.md`
