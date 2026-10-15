# Roadmap: PYPOST-1409

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business goals, user stories, acceptance criteria, and domain entities for collection-scoped variables and catalog manifests
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1409/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design catalog manifest schema and deprecate library-level variables
  - [x] Design collection-scoped variable authority and 3-tier resolution engine
  - [x] Specify automated failing repro test for Step 3 in `ai-tasks/PYPOST-1409/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_scoped_variables_repro.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Deprecate `variables` and `presets` on `LibraryManifest`, emit `DeprecationWarning` on ingestion of legacy manifests, and omit empty deprecated fields during serialization
  - [x] Iteration 2: Establish collection-first variable and preset authority in `LibraryVariableResolver`, implement 3-tier precedence hierarchy, and eliminate cross-collection namespace pollution
  - [x] Iteration 3: Update `LibraryRuntimeResolver` to prioritize collection presets over manifest presets without mutating catalog manifests
  - [x] Iteration 4: Resolve review gaps by handling secret variables gracefully in `LibraryRuntimeResolver._resolve`, synchronize dev lockfile, and verify full test suite and quality gates (`make test`, `make lint`, `make typecheck`, `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] Format and clean modified files, verifying 100-character line length limits and test timeouts
  - [x] Run static analysis and test gates (`make lint`, `make typecheck`, `make verify-ai-tasks`, `make test`)
  - [x] Create cleanup report in `ai-tasks/PYPOST-1409/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - Document logging, metrics, diagnostics, and provenance in `ai-tasks/PYPOST-1409/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - Document catalog manifest deprecation, collection-scoped variable authority, 3-tier resolution engine, cross-collection namespace isolation, and secret masking during MCP runtime resolution in `doc/dev/collection_scoped_variables.md`
  - Maintain documentation links and table of contents in `doc/dev/README.md`
  - Record dev docs summary in `ai-tasks/PYPOST-1409/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1409/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1409/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_scoped_variables_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1409/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1409/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1409/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_scoped_variables.md`
- `ai-tasks/PYPOST-1409/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
