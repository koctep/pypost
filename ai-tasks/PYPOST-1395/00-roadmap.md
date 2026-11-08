# Roadmap: PYPOST-1395

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1395/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1395/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_reference_collection_masking_contract.py`
- [x] **STEP 4: Development**
  - [x] Configured `hidden_response_fields` (`["email", "two_factor_authentication", "plan.name"]`) on `github-get-authenticated-user` in `examples/collections/github_mcp.json` and verified with contract and regression tests
  - [x] Configured `hidden_response_fields` (`["email", "commit_email", "public_email"]`) on `gitlab-get-current-user` in `examples/collections/gitlab_mcp.json` and verified with contract and regression tests
  - [x] Configured `hidden_response_fields` on `jira-get-current-user` (`["emailAddress", "accountId"]`) and `jira-search-assignable-users` (`["[*].emailAddress", "[*].accountId"]`) in `examples/collections/jira_mcp.json` and verified with contract and regression tests
  - [x] Verified Step 3 contract test `tests/test_reference_collection_masking_contract.py` turns green across all assertions
  - [x] Verified existing collection test suites and quality gates pass (`make lint`, `make typecheck`, `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1395/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1395/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1395/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/hidden_response_fields.md`: Document sample `hidden_response_fields` across all bundled reference collections (Google Drive, GitHub, GitLab, Jira Cloud), selector patterns (bare keys, dotted paths, root array wildcards), dual-surface behavior (MCP irreversible redaction vs GUI click-to-reveal), and contract verification
  - [x] `doc/dev/github_mcp_collection.md`: Note `hidden_response_fields` configuration on `github-get-authenticated-user`
  - [x] `doc/dev/gitlab_mcp_collection.md`: Note `hidden_response_fields` configuration on `gitlab-get-current-user`
  - [x] `doc/dev/jira_mcp_collection_e2e.md`: Note `hidden_response_fields` configuration on `jira-get-current-user` and `jira-search-assignable-users`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1395/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1395/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1395/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1395/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1395/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
