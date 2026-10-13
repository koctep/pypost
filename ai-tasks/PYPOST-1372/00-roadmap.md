# Roadmap: PYPOST-1372

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Analyze parent epic PYPOST-1284, architecture specification PYPOST-1368, and existing `CollectionVariable` model
  - [x] Define business goals, functional and non-functional requirements, constraints, and entities
  - [x] Author `ai-tasks/PYPOST-1372/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research Pydantic BaseModel, ConfigDict(populate_by_name=True), validation, and serialization in `pypost/models/collection_variable.py`
  - [x] Plan automated failing repro test suite (`tests/test_collection_variable_guidance_repro.py`)
  - [x] Design component architecture, schema diagram, and `help_text` field specification
  - [x] Formulate backward compatibility and downstream consumer integration strategy (PYPOST-1373, PYPOST-1374)
  - [x] Draft `ai-tasks/PYPOST-1372/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_variable_guidance_repro.py`
- [x] **STEP 4: Development**
  - [x] Extend `CollectionVariable` with `help_text: Optional[str] = Field(...)` and `@field_validator("help_text", mode="before")` in `pypost/models/collection_variable.py`
  - [x] Verify red repro test suite passes green (19/19 tests passed in `tests/test_collection_variable_guidance_repro.py`)
  - [x] Verify broader regression test suite passes green (`tests/test_collection_format_v2_repro.py`, `tests/test_collection_serializer.py`, `tests/test_library_manifest_and_overlay_repro.py`)
  - [x] Pass code quality checks (`make lint` and `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linting (`make lint`, `make typecheck`)
  - [x] Inspect code and repro tests for unused imports, dead code, docstrings, typing annotations, and PEP 8 compliance
  - [x] Verify test suite execution and timeout markers (`make test PYTEST_ARGS="tests/test_collection_variable_guidance_repro.py"`)
  - [x] Create cleanup report `ai-tasks/PYPOST-1372/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Analyze runtime observability requirements: pure Pydantic model validation with in-memory execution and zero network I/O
  - [x] Document logging rationale and sensitive masking principles (separation of public guidance `help_text` vs confidential `secret` values)
  - [x] Define downstream observability contract for wizard UI (`VariableSetupWizardDialog`, PYPOST-1373) and editor integration (`McpServersDialog`, PYPOST-1374)
  - [x] Document process observability (sprint task traceability, Jira links, token tracking at 100 tokens/min, subagent tracking, 19/19 passing test gate)
  - [x] Author `ai-tasks/PYPOST-1372/50-observability.md` per td-50-observability standard template
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Evaluate implementation shortcuts, architectural compromises, and technical trade-offs
  - [x] Assess code quality, typing rigor, and Pydantic V2 schema adherence
  - [x] Review test coverage completeness and pytest timeout annotations (19/19 tests)
  - [x] Analyze runtime performance characteristics and in-memory validation overhead
  - [x] Document downstream follow-up tasks (PYPOST-1373, PYPOST-1374, PYPOST-1375) in Sprint 2029
  - [x] Author `ai-tasks/PYPOST-1372/60-tech-debt.md` per td-60-tech-debt template
- [x] **STEP 8: Dev Docs**
  - [x] Update developer documentation in `doc/dev/collection_format_v2.md` documenting `help_text` schema extension, validation rules, YAML/JSON snippets, and backward compatibility
  - [x] Cross-reference `CollectionVariable.help_text` in `doc/dev/mcp_server_registry.md`
  - [x] Draft `ai-tasks/PYPOST-1372/70-dev-docs.md` capturing developer documentation decisions
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1372/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1372/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1372/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1372/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1372/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
