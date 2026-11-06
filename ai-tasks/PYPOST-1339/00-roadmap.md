# Roadmap: PYPOST-1339

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1339/10-requirements.md`
  - Language: Python (test-suite / example-collection verification)
  - Parent debt: PYPOST-1334 TD-1
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1339/20-architecture.md`
  - Test-only architecture: correct GitHub/GitLab full-render marker body surface to raw
    `_render(request.body, …)`; twin for nested-object-final field; optional dispatch
    `ref`-before-`inputs` restore; no `pypost/` runtime change
  - Step 3 failing-repro plan documented (not N/A) — twin + recommended field-order restore
    to force RED under current `json.dumps(parsed)` scan
- [x] **STEP 3: Failing Repro Test**
  - Red twin: `tests/test_github_mcp_collection.py::test_github_mcp_nested_object_final_body_field_does_not_false_positive_markers`
  - Fixture force: `examples/collections/github_mcp.json` `github_dispatch_workflow` body emits `ref` then `inputs` (nested-object-final)
  - Also red under same defect: `tests/test_github_mcp_collection.py::test_github_mcp_full_render_leaves_no_template_markers` (`github_dispatch_workflow` `[full]`)
- [x] **STEP 4: Development**
  - [x] Iteration 1: GitHub + GitLab full-render marker checks (and nested-object twin)
    scan `_render(request.body, variables)` instead of `json.dumps(parsed)`; doc note
    updated for `ref`-then-`inputs`; twin + both full-render marker tests GREEN via
    `make test`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1339/40-code-cleanup.md`
  - `make lint` OK; `make typecheck` OK; no `make analyze` target
  - Relevant marker tests green via `make test`; no unused imports/debug left
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1339/50-observability.md`
  - N/A for production logging/metrics: change is test-suite + example fixture only
    (MCP collection marker scan / optional `ref`-then-`inputs` body order); no
    `pypost/` runtime path
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1339/60-tech-debt.md`
  - Parent PYPOST-1334 TD-1 closed by raw-body marker scan + twin + `ref`-then-`inputs`
  - Residual string-value substring risk accepted; scan duplication → existing PYPOST-1340
  - No BLOCKER timeout gaps; Phase D syncs follow-ups (do not create Jira in this step)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/github_mcp_collection.md` — Surviving template-marker checks section;
    test-layout / troubleshooting / resolved PYPOST-1339 note (field-order note from
    Step 4 kept)
  - `doc/dev/gitlab_mcp_collection.md` — mirrored marker-scan section, troubleshooting,
    follow-ups, See also → GitHub
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1339/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1339/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1339/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1339/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1339/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
