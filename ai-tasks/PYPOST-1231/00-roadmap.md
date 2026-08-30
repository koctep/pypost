# Roadmap: PYPOST-1231

## Task Metadata

- **Implementation language**: Markdown (documentation-only fix; verified/guarded by an existing
  Python test, `tests/test_agent_e2e_harness_table_doc.py`, which is not modified by this task).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Pre-existing test used as the Step 3 gate (no new test file needed):
    `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
    (the guard test named in Jira PYPOST-1231).
  - Repro command: `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py"`
  - Result: FAILED (1 failed in 0.30s), confirmed red for the intended reason — the
    `doc/dev/agent_e2e.md` harness table is missing rows for three `agent_e2e`-marked
    test modules (not a broken fixture/import error). Captured excerpt:

    ```
    tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules FAILED [216ms] [100%]

    =================================== FAILURES ===================================
    ____________ test_agent_e2e_harness_table_matches_marked_modules _____________
    tests/test_agent_e2e_harness_table_doc.py:103: in test_agent_e2e_harness_table_matches_marked_modules
        assert marked == documented, (
    E   AssertionError: agent_e2e mark set != harness table Module paths; only_in_marks=['tests/test_agent_session_event_settle.py', 'tests/test_agent_ui_actions_mcp_seed.py', 'tests/test_ui_actions_tree_no_model_mutation.py']; only_in_doc=[]
    E   assert frozenset({'t...url.py', ...}) == frozenset({'t...url.py', ...})
    E
    E     Extra items in the left set:
    E     'tests/test_ui_actions_tree_no_model_mutation.py'
    E     'tests/test_agent_session_event_settle.py'
    E     'tests/test_agent_ui_actions_mcp_seed.py'
    ============================== 1 failed in 0.30s ==============================
    ```

    Confirmed: `doc/dev/agent_e2e.md` was not edited in this step; no production
    or doc fix landed. This is the correct red gate for Step 4.
- [x] **STEP 4: Development**
  - [x] Doc fix: appended three missing rows to the "Harness modules under the
    marker" table in `doc/dev/agent_e2e.md` (no other part of the doc, and no
    other file, was touched):
    - `| \`tests/test_agent_session_event_settle.py\` | Post-ready flush and tree
      settlement contracts (1217) |`
    - `| \`tests/test_agent_ui_actions_mcp_seed.py\` | Seed/collection injection
      in sidecar session (993) |`
    - `| \`tests/test_ui_actions_tree_no_model_mutation.py\` | Load-bearing
      evidence for tree-no-model refusal guard (1042/972) |`
    - Descriptions were derived from each module's own docstring (PYPOST-1217,
      PYPOST-993, PYPOST-1042/972 respectively), matching the existing row
      format (`| \`tests/module.py\` | Covers description |`).
  - Before: `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -vv"`
    → FAILED, `only_in_marks=['tests/test_agent_session_event_settle.py',
    'tests/test_agent_ui_actions_mcp_seed.py',
    'tests/test_ui_actions_tree_no_model_mutation.py']; only_in_doc=[]` — matches
    the Step 3 red repro exactly.
  - After: `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -vv"`
    → PASSED (1 passed).
  - Broader sanity check: `make test-agent-e2e` run for best-effort validation;
    result recorded in chat/PR notes by the orchestrator (see task return).
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - Confirmed (no re-edit needed): `doc/dev/agent_e2e.md`'s harness table already
    contains all 3 rows for `tests/test_agent_session_event_settle.py`,
    `tests/test_agent_ui_actions_mcp_seed.py`, and
    `tests/test_ui_actions_tree_no_model_mutation.py` (added in Step 4).
  - Guard re-run: `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py"`
    → PASSED (1 passed).
  - Cross-check: grepped `doc/dev/` for the 3 module names. Two other legitimate
    references found — `doc/dev/testing.md` (regression-test detail section for
    `test_agent_session_event_settle.py`) and `doc/dev/agent_ui_actions_mcp.md`
    (run command for `test_agent_ui_actions_mcp_seed.py`) — both accurate and
    consistent with the harness table; no stale content, no additional
    cross-linking needed.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1231/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1231/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1231/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1231/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1231/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
