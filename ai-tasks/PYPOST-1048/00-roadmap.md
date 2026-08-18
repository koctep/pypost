# Roadmap: PYPOST-1048

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_example_fixtures.py` —
    `test_jira_mcp_discoverability_rejects_stripped_delete_sprint_warning`
  - [x] `tests/test_example_fixtures.py` —
    `test_jira_mcp_discoverability_rejects_stripped_backlog_membership_guidance`
  - Red mode: `NameError: name 'assert_jira_mcp_discoverability_guidance' is
    not defined` on both tests only (23 pre-existing tests still pass); the
    lowercased premise assertions pass first, so the red is the missing guard,
    not a broken fixture.
- [x] **STEP 4: Development**
  - [x] Iteration 1 — `tests/test_example_fixtures.py`: added
    `JIRA_MCP_DISCOVERABILITY_SUBSTRINGS` (locked lowercase fragments per
    protected request id), the shared checker
    `assert_jira_mcp_discoverability_guidance()` (fifth `assert_jira_mcp_*`
    member; case-insensitive, message names the request id and all missing
    fragments sorted), and the parametrized positive lock over the shipped
    `examples/collections/jira_mcp.json`. Step 3 reds turned green; no
    fixture or `pypost/` change was needed — shipped descriptions already
    satisfy the table.
  - [x] Iteration 2 — Step 3 reviewer follow-ups: added the parametrized
    partial-strip mutation
    `test_jira_mcp_discoverability_rejects_each_single_stripped_fragment`
    (one case per locked fragment, proving each fragment is enforced
    independently) and tightened the two full-strip mutations plus the new
    one to pin the message contract (request id + sorted missing fragments,
    retained fragments absent).
  - [x] Verified: `make test PYTEST_ARGS='tests/test_example_fixtures.py -v'`
    → `31 passed`; `flake8 tests/test_example_fixtures.py` clean. Full
    `make test` failures (`test_solid_audit_baseline.py`,
    `test_verify_ai_task_artifacts.py`) are pre-existing and unrelated —
    they reproduce with this task's artifacts removed.
  - [x] Verified non-vacuity: four temporary checker weakenings
    (first-fragment-only, short-circuit on any hit, unsorted message,
    message without request id) each turn the new coverage red; file
    restored byte-identical afterwards.
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis & linter verification (`flake8 tests/test_example_fixtures.py` -> clean)
  - [x] Code formatting, imports, line length (<= 100 chars), timeouts, and quality verification
  - [x] Test suite execution (`pytest tests/test_example_fixtures.py` -> 32 passed)
  - [x] Cleanup documentation (`ai-tasks/PYPOST-1048/40-code-cleanup.md`)
- [x] **STEP 6: Observability**
  - [x] Observability requirements analysis (offline fixture contract tests only; no `pypost/` runtime changes)
  - [x] Production logging & metrics evaluation (N/A for static test fixtures; no syslog/Prometheus additions)
  - [x] Test diagnostic observability verification (`assert_jira_mcp_discoverability_guidance` failure messages name `request.id` and all sorted missing fragments)
  - [x] Observability documentation (`ai-tasks/PYPOST-1048/50-observability.md`)
- [x] **STEP 7: Review and Technical Debt**
  - [x] Technical debt analysis (shortcuts, compromises, code quality, missing tests, performance)
  - [x] Test timeout and safety review (`pytestmark = pytest.mark.timeout(30)`, no blocker)
  - [x] Technical debt documentation (`ai-tasks/PYPOST-1048/60-tech-debt.md`)
  - [x] Acceptance gate review and approval
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/testing.md` — extended section header to include PYPOST-1048;
    updated checker count from four to five; documented fifth
    `assert_jira_mcp_discoverability_guidance` checker and
    `JIRA_MCP_DISCOVERABILITY_SUBSTRINGS` table; added
    `test_jira_mcp_shipped_descriptions_carry_discoverability_guidance` to
    Usage test list; added discoverability troubleshooting row; added new
    subsection "Jira MCP discoverability contracts (PYPOST-1048)" with checker
    API, failure message contract, and maintainer rule.
  - [x] `doc/dev/jira_mcp_path_freshness.md` — updated See also links to
    point at the new section anchor and added a direct link to the
    discoverability contracts subsection.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: Python, extending the existing offline fixture-contract test
  suite for the curated jira-mcp collection.
- **Documentation**: English Markdown for this Top-Down workflow record.
- **Application behavior**: out of scope; this task protects existing
  agent-facing guidance rather than changing the jira-mcp collection's
  endpoints or operations.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1048/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1048/20-architecture.md` — locked `mcp_description`
  discoverability substrings via a shared `assert_jira_mcp_*` checker in
  `tests/test_example_fixtures.py`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1048/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1048/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1048/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Recommended Branch Name

`feature/PYPOST-1048-jira-mcp-description-contracts`
