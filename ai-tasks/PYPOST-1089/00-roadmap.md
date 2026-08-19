# Roadmap: PYPOST-1089

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feat/PYPOST-1089-validate-mcp-tool-param-default-and-table-column

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document validation requirements for `McpToolParam.default` type consistency against `McpToolParam.type`
  - [x] Document UI requirements for editable Default column in `McpParamsTable` surviving parameter renames
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1089/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design type validation logic in `McpToolParam` and 5-column table architecture in `McpParamsTable`
  - [x] Specify type parsing, round-trip serialization, and rename survival flow
  - [x] Create architecture artifact `ai-tasks/PYPOST-1089/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Verification Test**
  - [x] Add failing tests in `tests/test_mcp_tool_contract.py` and `tests/test_request_editor_mcp_params.py`
  - [x] Confirm RED failure before production code changes
  - Tests: `tests/test_mcp_tool_contract.py::test_boolean_default_string_raises`
  - Tests: `tests/test_mcp_tool_contract.py::test_integer_default_float_raises`
  - Tests: `tests/test_mcp_tool_contract.py::test_valid_defaults_accepted`
  - Tests: `tests/test_request_editor_mcp_params.py::TestMcpParamsTableFiveColumns::test_mcp_params_table_has_five_columns`
  - Tests: `tests/test_request_editor_mcp_params.py::TestMcpParamsTableFiveColumns::test_default_column_survives_rename`
- [x] **STEP 4: Development**
  - [x] Implement `McpToolParam._validate_default_type()` in `pypost/models/models.py`; raises `ValueError` on type mismatch, `None` always permitted
  - [x] Implement 5-column `McpParamsTable` with editable Default column (`_set_row`, `_serialise_default`, `_parse_default`, `get_data`) in `pypost/ui/widgets/request_editor.py`
  - [x] All 22 tests pass GREEN (`pytest tests/test_mcp_tool_contract.py tests/test_request_editor_mcp_params.py`)
  - [x] `make lint` clean
  - [x] Review round 1: FAIL (2 fixable gaps vs architecture — missing `_COERCERS` dispatch dict, `number` default not preserving int/float); fix subagent closed both; review round 2: PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Run `make lint` — clean (flake8 on `pypost/`, markdown lint, relative link check)
  - [x] Verify all 22 tests in `tests/test_mcp_tool_contract.py` and
    `tests/test_request_editor_mcp_params.py` pass, each covered by an explicit
    module-level `pytestmark = pytest.mark.timeout(N)`
  - [x] Checked for merge conflict markers in the 2 changed production files and 2 changed
    test files — none found
  - [x] Produce `ai-tasks/PYPOST-1089/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Traced both error paths: `McpToolParam._validate_default_type()` ValueError
    (wrapped by Pydantic into `ValidationError`) is already caught and logged at
    every construction-from-untrusted-data boundary — `StorageManager.load_collections()`
    (`storage.py:153`, `logger.warning("storage_collection_load_failed ...")`) and
    `load_collection_import_candidates()` (`collection_import.py:141-151`, per-record
    `parse_errors` surfaced to the user via the import dialog, counts logged at INFO).
    In-app construction via `McpParamsTable.get_data()` cannot trigger it because
    `_COERCERS` guarantees a type-matched value before construction.
  - [x] Restyled the existing `_parse_default()` DEBUG fallback log in
    `pypost/ui/widgets/request_editor.py` from a free-text sentence to the
    project's `event_name key=value` structured convention
    (`mcp_param_default_coerce_failed value=%r param_type=%s`) — level and
    fallback-to-`None` behaviour unchanged. No other code changes were needed;
    `pypost/models/models.py` deliberately carries no logger, matching the sibling
    `Settings` model_validator convention of raise-only validators.
  - [x] Re-ran `tests/test_mcp_tool_contract.py` + `tests/test_request_editor_mcp_params.py`
    (22 passed) and `make lint` (clean) after the log-message edit
  - [x] Produce `ai-tasks/PYPOST-1089/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed technical debt and follow-up opportunities: `number` int/float
    coercion edge case (scientific notation silently dropped), `_coerce_default_boolean`
    fail-mode inconsistency vs. the other 6 `_COERCERS` entries, Default column has no
    type-aware editor (no checkbox for `boolean`), Type-combo change doesn't touch/clear
    the Default cell, `validate_assignment` not set on `McpToolParam` (latent, no active
    mutation site found), duplicated type-mapping across `models.py`/`request_editor.py`,
    6 test-coverage gaps (incl. the previously-noted missing `number` int/float
    round-trip test), and a documentation-only note that the validator is
    `model_post_init`, not a `@model_validator` decorator. No architecture deviations
    found. No performance concerns. No pre-existing test failures encountered.
  - [x] Produced `ai-tasks/PYPOST-1089/60-tech-debt.md`
  - [x] Re-confirmed 22/22 tests green
    (`tests/test_mcp_tool_contract.py`, `tests/test_request_editor_mcp_params.py`) and
    `make lint` clean; no production or test code changed in this step
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/mcp_integration.md`: new `### Default value type validation
    (PYPOST-1089)` section (model_post_init hook, not `@model_validator` — closes
    PYPOST-1098's documentation gap), rewrote `#### UI` under Tool metadata authoring
    for the 5-column `McpParamsTable` (Default column rename-safety mechanism,
    `_COERCERS` dispatch table with all 7 coercers, known limitations linking
    PYPOST-1095/1096/1099), and updated the now-stale `#### UI round-trip`,
    `#### Model field`, `#### Limitations`, and `## Limitations & Tech Debt` bullets
    that previously described both gaps as open. Confirmed via grep this is the only
    `doc/dev/*.md` file covering `McpParamsTable`/`McpToolParam`/`request_editor`, so
    no second file was needed.
  - [x] Produced `ai-tasks/PYPOST-1089/70-dev-docs.md`
  - [x] Re-ran `tests/test_mcp_tool_contract.py` + `tests/test_request_editor_mcp_params.py`
    (22 passed) and `make lint` (clean) after the docs-only change; no production or
    test code touched in this step
- [x] **COMMIT: Commit Changes**
  - Commit hash: `d4d7dd00` on `dev` — "feature(mcp): PYPOST-1089 validate McpToolParam default type and add editable Default column"
  - Branch name (reference only, not switched): `feature/PYPOST-1089-validate-mcp-tool-param-default-and-table-column`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-1089/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1089/20-architecture.md`

### STEP 3: Failing Repro / Verification Test
- `tests/test_mcp_tool_contract.py`
- `tests/test_request_editor_mcp_params.py`

### STEP 4: Development
- `pypost/models/models.py`
- `pypost/ui/widgets/request_editor.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1089/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1089/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1089/60-tech-debt.md`

### STEP 8: Dev Docs
- `doc/dev/mcp_integration.md`
- `ai-tasks/PYPOST-1089/70-dev-docs.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
