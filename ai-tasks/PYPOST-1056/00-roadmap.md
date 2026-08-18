# Roadmap: PYPOST-1056

## Task Metadata

- **Implementation language**: Python
- **Branch name**: test/PYPOST-1056-mutation-diagnostic-path-freshness

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1056/00-roadmap.md` — task roadmap
  - `ai-tasks/PYPOST-1056/10-requirements.md` — business requirements
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1056/20-architecture.md` — offline mutation-test architecture
- [x] **STEP 3: Failing Repro Test**
  - `N/A — no behavioral change`: the existing comparator already emits the
    required request id, locked fragment, and observed URL diagnostic for the
    selected drift mutation. No known behavior is missing, so a red test would
    not establish a production fix; Step 4 will instead add the planned green,
    test-only mutation-contract regression guard. Production changes remain a
    contingency only if that guard exposes a real diagnostic gap.
- [x] **STEP 4: Development**
  - [x] Added an offline mutation-contract regression guard for a missing
    `/rest/api/3/search/jql` path fragment; it requires the request id, locked
    fragment, and observed URL in the comparator diagnostic.
  - [x] Extended `check-jira-mcp-path-freshness` to run both the aligned and
    mutation contracts.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1056/40-code-cleanup.md` — code cleanup report
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1056/50-observability.md` — observability and diagnostic analysis
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1056/60-tech-debt.md` — technical debt analysis
- [x] **STEP 8: Dev Docs**
  - `doc/dev/jira_mcp_path_freshness.md` — documented URL-drift reject contract, diagnostics, and focused verification
  - `doc/dev/testing.md` — documented test_jira_mcp_critical_rest_paths_rejects_url_drift, diagnostic assertions, and check-jira-mcp-path-freshness
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1056/00-roadmap.md`
- `ai-tasks/PYPOST-1056/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1056/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1056/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1056/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1056/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/jira_mcp_path_freshness.md`
- `doc/dev/testing.md`
- `doc/dev/README.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
