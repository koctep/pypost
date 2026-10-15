# Roadmap: PYPOST-1410

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business goals, user stories, acceptance criteria, and domain entities for standalone MCP servers without workspace environment
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1410/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design standalone MCP server architecture decoupled from workspace environments
  - [x] Specify failing repro test design for Step 3 (`tests/test_mcp_standalone_execution_repro.py`)
  - [x] Create architecture artifact in `ai-tasks/PYPOST-1410/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_standalone_execution_repro.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Data model schema decoupling (`McpServerConfiguration` with optional `environment_id`)
  - [x] Iteration 2: Core runtime resolver decoupling (`LibraryRuntimeResolver` standalone resolution with preset/defaults)
  - [x] Iteration 3: Server registry lifecycle & supervision (`MCPServerRegistry.reconcile_references` standalone preservation)
  - [x] Iteration 4: UI configuration dialog & presentation (`_McpServerEditor` environment toggle & `McpServersDialog` em-dash rendering)
  - [x] Iteration 5: Verification & quality gates (7/7 repro GREEN, `make lint`, `make typecheck`, `make verify-ai-tasks` all passed)
- [x] **STEP 5: Code Cleanup**
  - [x] Code cleanup, formatting check, timeout verification, quality gates
  - [x] Create cleanup artifact in `ai-tasks/PYPOST-1410/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Document logging, secret redaction, and metrics in `ai-tasks/PYPOST-1410/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Document technical debt, shortcuts, quality analysis, and follow-ups in `ai-tasks/PYPOST-1410/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Document standalone MCP server configuration and execution in `doc/dev/collection_scoped_variables.md`
  - [x] Document `McpServerConfiguration.environment_id: Optional[str] = None`
  - [x] Document runtime resolution via collection presets and local overlay when `environment_id is None`
  - [x] Document server registry reference reconciliation behavior for standalone servers
  - [x] Document UI behavior in `_McpServerEditor` and `McpServersDialog`
  - [x] Update execution roadmap and child story tracking table in `doc/dev/collection_scoped_variables.md`
  - [x] Verify links and TOC in `doc/dev/README.md`
  - [x] Create documentation report in `ai-tasks/PYPOST-1410/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1410/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1410/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1410/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1410/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1410/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
