# Roadmap: PYPOST-1533

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1533/10-requirements.md`
  - Policy: keep repeats. `set_data` and edits trim whitespace, drop blank
    selectors, preserve order, and do not collapse duplicate selector text.
    The single unsaved trailing blank stays. Saved lists are not uniquified.
    Case remains significant. PYPOST-1386 says uniquify only if the product
    wants it; no such want is recorded. PYPOST-1377 restores the ordered saved
    list as saved. The model already keeps repeats. Changing that would alter
    saved collections.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1533/20-architecture.md`
  - No production change. `set_data` and `setData` already keep repeats,
    trim whitespace, drop blank selectors, preserve order, and keep case.
    The single unsaved trailing blank stays. Saved lists stay ordered lists.
    Step 3 is N/A — no behavioral change.
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change. The accepted rule is already the runtime
    behavior. `set_data` and `setData` already keep duplicate selector text,
    so there is no missing product behavior to force red. No red test was
    written.
- [x] **STEP 4: Development**
  - [x] No production change was required. `set_data` and `setData` already
    trim, drop blanks, preserve order, keep duplicate selector text, and keep
    one unsaved trailing blank. Existing hidden-fields tests passed:
    `tests/test_hidden_fields_virtualization_repro.py` and
    `tests/test_request_hidden_fields_model_and_ui.py`.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1533/40-code-cleanup.md`
  - No source diff to format, lint, or clean. Production modules and tests stay unchanged.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1533/50-observability.md`
  - None added. No new logs or metrics. Duplicate selectors stay. Production
    code and tests stay unchanged.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1533/60-tech-debt.md`
  - None. Keep duplicate selectors. No production change. No uniquify
    follow-up. Production code and tests stay unchanged.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_fields_table.md` — duplicate-selector policy beside
    `set_data` / `get_data`. Records existing behavior.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1533/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1533/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change. The accepted rule is already the runtime
  behavior verified in `20-architecture.md`. `HiddenFieldsTableModel` already
  keeps duplicate selectors. No failing test was added. Production code and
  tests stay unchanged.

### STEP 4: Development

- No production change. `HiddenFieldsTableModel.set_data` and `setData`
  already match the keep-repeats policy.
- Existing tests:
  `tests/test_hidden_fields_virtualization_repro.py`,
  `tests/test_request_hidden_fields_model_and_ui.py`.

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1533/40-code-cleanup.md`
- No source diff to format, lint, or clean. Production modules and tests stay unchanged.

### STEP 6: Observability

- `ai-tasks/PYPOST-1533/50-observability.md`
- None added. No new logs or metrics. Production code and tests stay unchanged.

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1533/60-tech-debt.md`
- None. Keep duplicate selectors. No production change. No uniquify
  follow-up. Production code and tests stay unchanged.

### STEP 8: Dev Docs

- `doc/dev/hidden_fields_table.md` — duplicate-selector policy beside `set_data` / `get_data`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
