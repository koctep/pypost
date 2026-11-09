# Roadmap: PYPOST-1538

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1538/10-requirements.md`
  - Language: Python
  - Business goal: a header selector is recognized the same way when it is
    validated, when it selects response data, and when sensitive header text
    is sanitized
  - Done when the three uses share one header-selector prefix and a divergence
    of that prefix is caught
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1538/20-architecture.md`
  - Chosen design: leaf module `pypost/core/header_selector_prefix.py`
    owns `HEADER_SELECTOR_PREFIX` and `header_selector_name`; validation,
    `JsonSelectorEngine._compile`, and `sanitize_headers` recognize headers
    only by calling that function
  - Current spellings match (`header:`, case-insensitive) and are three
    private definitions (`field_selector_syntax.py:14`,
    `json_selector_engine.py:13`, `sensitive_text_sanitizer.py:68`)
  - `header:Authorization` keeps its current meaning
  - Step 3 is a red test of the missing shared definition at
    `tests/test_header_selector_prefix.py` (not N/A)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_header_selector_prefix.py`
- [x] **STEP 4: Development**
  - [x] Implemented the shared header-selector prefix in
    `pypost/core/header_selector_prefix.py`. `validate_field_selector`,
    `JsonSelectorEngine._compile`, and `sanitize_headers` recognize a header
    only by calling `header_selector_name`.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1538/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1538/50-observability.md`
  - No logs or metrics added. Header-prefix recognition is not logged.
    `validate_field_selector` and `sanitize_headers` have no log on this
    path. `JsonSelectorEngine._compile` already logs integer compile counts
    only (`json_selector_engine.py` lines 161-168), with no selector or
    header text.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1538/60-tech-debt.md`
  - No new debt. The source assertion and the patched-prefix check stay the
    accepted design. The test module already declares
    `pytestmark = pytest.mark.timeout(30)`. Literal `..` rejection stays with
    PYPOST-1539, and specialized invalid messages stay with PYPOST-1540.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_fields_table.md` — Header row names shared `HEADER_SELECTOR_PREFIX` and PYPOST-1538; example stays `header:Authorization`
  - `doc/dev/json_selector_engine.md` — body selection ignores a header selector via shared `header_selector_name`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1538/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1538/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_header_selector_prefix.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1538/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1538/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1538/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
