# Roadmap: PYPOST-1017

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change
  - Rationale (from `20-architecture.md`): This story ships importable
    JSON fixtures under `examples/` and Markdown discoverability docs
    only. Application import/export runtime is unchanged and already
    covered by existing collection/environment import tests.
    Requirements introduce no new product code path to assert with a
    red test. No fake red product test was written. Optional green
    fixture-contract check (parse + placeholders + `hidden_keys`) is
    Step 4 only, after fixtures are finalized — see Architecture
    Implementation Plan.
- [x] **STEP 4: Development**
  - [x] Review/finish Jira Cloud pair; keep `mcp.json`; verify `.gitignore`
  - [x] Add `examples/README.md`; wire root README + User Guide pointers
  - [x] Reviewed `jira_mcp.json` (12 MCP tools) and `jira_cloud.json`
    (placeholders + `hidden_keys` + `enable_mcp`); both import via native
    loaders; no real secrets
  - [x] Kept `mcp.json` probe role; clarified in `examples/README.md` and
    User Guide collection pointer
  - [x] Verified `.gitignore` exceptions track `examples/**/*.json`
  - [x] Added `examples/README.md` (inventory, import order, secret rules)
  - [x] Wired discoverability: root README, `doc/user/collections.md`,
    `doc/user/environments.md`, optional Related/workflows pointers
  - [x] Optional green contract test: `tests/test_example_fixtures.py`
    (3 passed via `make test`)
  - [x] Step 4 review: stripped PYPOST-1015 tutorial rewrites from
    `doc/user/collections.md` / `environments.md`; kept Example fixtures
    pointers only; contract test re-run green
- [x] **STEP 5: Code Cleanup**
  - [x] Lint / format / fixture sanity on PYPOST-1017 scope only
  - [x] Contract test type hints + timeout marker verified
  - [x] `ai-tasks/PYPOST-1017/40-code-cleanup.md` written
- [x] **STEP 6: Observability**
  - [x] N/A — fixtures/docs only; no runtime logs or metrics added
  - Artifact: `ai-tasks/PYPOST-1017/50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-1017/60-tech-debt.md` written (SAFE TO CLOSE)
  - [x] Timeout markers present on contract tests (not a blocker)
  - [x] No merge-blocking debt; follow-ups TD-1..TD-3 documented for later sync
- [x] **STEP 8: Dev Docs**
  - [x] No new `doc/dev/` feature page (fixtures/docs-only; hub is
    `examples/README.md`)
  - [x] `doc/dev/testing.md` — Jira pair + `tests/test_example_fixtures.py`
    contract section; `mcp.json` role cross-link
  - [x] Close-out: `ai-tasks/PYPOST-1017/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: JSON for importable example fixtures under `examples/`, plus
  English Markdown for import/use documentation (`.cursor/lsr/do-markdown.md`)
- **Application code**: none in scope unless a tiny fixture/docs-only fix is
  required; no new product features

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1017/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1017/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (fixture/docs-only; no red product test;
  rationale in Step Status and `20-architecture.md`)
- Confirmed: no automated red test under `tests/`; no production code
  changed in this step

### STEP 4: Development

- `examples/collections/jira_mcp.json` (finish/review, track)
- `examples/environments/jira_cloud.json` (finish/review, track)
- `examples/collections/mcp.json` (keep; role clarified in docs)
- `.gitignore` exceptions (verify-keep)
- `examples/README.md` (primary fixture docs)
- Root `README.md` + `doc/user/collections.md` /
  `doc/user/environments.md` pointers (optional Related elsewhere)
- `tests/test_example_fixtures.py` (optional green contract test;
  not a Step 3 red)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1017/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1017/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1017/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (brief example-fixtures contract note)
- `ai-tasks/PYPOST-1017/70-dev-docs.md` (N/A for new pages + change log)
- No new `doc/dev/<feature>.md` — architecture: fixture docs live under
  `examples/README.md` and User Guide pointers
