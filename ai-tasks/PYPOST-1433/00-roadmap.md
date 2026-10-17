# Roadmap: PYPOST-1433

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for modular harness architecture and mixin decomposition
  - [x] Document business goals, user personas, functional and non-functional requirements, acceptance criteria, and Q&A
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1433/10-requirements.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research harness decomposition boundaries and downstream consumers
  - [x] Define modular mixin boundaries (`LibraryFixtureMixin`, `EnvironmentFixtureMixin`, `ServerRegistryFixtureMixin`)
  - [x] Define composite harness inheritance and backward compatibility contracts
  - [x] Specify failing repro test strategy for Step 3 (`tests/test_collection_harness_mixins.py`)
  - [x] Create architecture artifact in `ai-tasks/PYPOST-1433/20-architecture.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_harness_mixins.py` (fails with ImportError: cannot import name 'LibraryFixtureMixin')
  - [x] Acceptance gate review PASS
- [x] **STEP 4: Development**
  - [x] Defined `LibraryFixtureMixin` implementing isolated library/overlay filesystem setup, manifest creation (`create_library`), and overlay persistence (`create_overlay`)
  - [x] Defined `EnvironmentFixtureMixin` implementing workspace filesystem setup and environment persistence (`create_workspace_environment`)
  - [x] Defined `ServerRegistryFixtureMixin` implementing MCP server registry lifecycle, candidate creation, dynamic port assignment, readiness polling, candidate registration, and teardown (`teardown`, `close`, `__enter__`, `__exit__`)
  - [x] Refactored `CollectionVariablesIntegrationHarness` to inherit from `LibraryFixtureMixin`, `EnvironmentFixtureMixin`, and `ServerRegistryFixtureMixin` with 100% backward compatibility
  - [x] Exported all mixins in `__all__`: `LibraryFixtureMixin`, `EnvironmentFixtureMixin`, `ServerRegistryFixtureMixin`, `CollectionVariablesIntegrationHarness`, `collection_integration_harness`, `collection_harness`
  - [x] Added `get_config` compatibility helper to `MCPServerRegistry` and `get_value` to `Environment`
  - [x] Verified Step 3 repro test green (`tests/test_collection_harness_mixins.py`)
  - [x] Verified consumer tests green (`tests/test_collection_integration_harness_repro.py`, `tests/test_collection_scoped_variables_integration.py`, `tests/test_mcp_concurrent_multiserver_repro.py`)
  - [x] Passed static analysis: `make lint`, `make typecheck`, `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Format and lint validation (`make lint`, `make typecheck`)
  - [x] Line length, formatting, and clean imports verification (all lines <= 100 chars; no unused imports or variables)
  - [x] Explicit test timeout markers verification (`pytestmark = pytest.mark.timeout(30)` per `do-testing`)
  - [x] Regression test suite verification (`make test PYTEST_ARGS="tests/test_collection_harness_mixins.py tests/test_collection_integration_harness_repro.py tests/test_collection_scoped_variables_integration.py tests/test_mcp_concurrent_multiserver_repro.py"`)
  - [x] Artifact integrity check (`make verify-ai-tasks`)
  - [x] Create `ai-tasks/PYPOST-1433/40-code-cleanup.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 6: Observability**
  - [x] Audit logging across modular test harness mixins (`LibraryFixtureMixin`, `EnvironmentFixtureMixin`, `ServerRegistryFixtureMixin`, `CollectionVariablesIntegrationHarness`)
  - [x] Verify syslog severity level mapping (DEBUG, INFO, WARNING, ERROR) and structured event formats
  - [x] Audit exception handling and diagnostics (manifest writing, port allocation, startup failure, teardown errors)
  - [x] Verify secret hygiene and zero token/credential leakage in log events
  - [x] Document metrics applicability and test harness observability scope
  - [x] Create `ai-tasks/PYPOST-1433/50-observability.md`
  - [x] Verify task artifact integrity with `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality issues, missing tests, and performance concerns
  - [x] Document non-blocker follow-up tasks linked to Jira issues (PYPOST-1435, PYPOST-1434, PYPOST-1437, PYPOST-1438)
  - [x] Create `ai-tasks/PYPOST-1433/60-tech-debt.md`
  - [x] Verify task artifact integrity with `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **STEP 8: Dev Docs**
  - [x] Document modular mixin architecture established in PYPOST-1433
  - [x] Document decomposed mixins (`LibraryFixtureMixin`, `EnvironmentFixtureMixin`, `ServerRegistryFixtureMixin`)
  - [x] Document composite class `CollectionVariablesIntegrationHarness` multiple inheritance and backward compatibility
  - [x] Document custom partial composition examples (e.g. `LibraryFixtureMixin` + `EnvironmentFixtureMixin`)
  - [x] Update Mermaid architecture diagram and filesystem layout
  - [x] Validate documentation formatting against `lint_user_docs.py` and `check_user_docs_links.py` (line length <= 100 chars, relative links valid)
  - [x] Verify task artifact integrity with `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1433/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1433/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_harness_mixins.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1433/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1433/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1433/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_integration_harness.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
