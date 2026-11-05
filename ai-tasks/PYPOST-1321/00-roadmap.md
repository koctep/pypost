# Roadmap: PYPOST-1321

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1321/10-requirements.md`
  - Business goal: app close during collection import must interrupt and release
    import work within the shared shutdown budget (gap left by PYPOST-1264 Risk 5)
  - Language: Python
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1321/20-architecture.md`
  - Admit `window.collections` into `main_window_lifecycle` owners (before `env`)
  - Align `CollectionsPresenter` to `begin_teardown` + `TeardownResult` (actions stay `bool`)
  - Failing repro design: `tests/test_main_window_collections_shutdown_repro.py`
  - PYPOST-1325 naming optional; fair share via existing allocator
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_main_window_collections_shutdown_repro.py` (red: collections omitted from main-window owner list)
- [x] **STEP 4: Development**
  - [x] Iteration 1: Admit `window.collections` into `main_window_lifecycle.teardown` owners (before `env`) — Step 3 red tests green
  - [x] Iteration 2: Add `collections_presenter_lifecycle` + `begin_teardown` / `TeardownResult` on presenter; fence import admission; register lifecycle owner; update bool callers + composition harness
  - [x] Iteration 3: Include `CollectionsPresenter` in idle idempotent owner contract test; lint/typecheck clean
  - [x] Iteration 4: Keep `collections_presenter.py` at 534 LOC (≤535 cap) via lazy lifecycle state
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1321/40-code-cleanup.md`
  - Deduped admission fencing (`_fence_admission`); getattr/setattr for lazy lifecycle fields (mypy)
  - Import order + green-contract docstring on Step 3 repro
  - `make lint` / `make typecheck` OK; focused teardown tests passed
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1321/50-observability.md`
  - Verified Step 4 `lifecycle_teardown_*` + legacy `collections_presenter_teardown_*` lines
  - Fixed `_LIFECYCLE_OWNERS` missing `collections_presenter` (metrics were `unknown`)
  - Added lifecycle observability regression + updated main-window aggregate harness (`owner_count=5`)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1321/60-tech-debt.md`
  - No do-testing timeout blockers; residual: lazy lifecycle attrs (LOC 534/535), dual logs, admission-fence unit gap
  - Already-ticketed: PYPOST-1324 / 1325 / 1322
  - 5 NON-BLOCKER pre-existing make-test failures (packaging seed models/views/workers, dialog LOC inventory, requirements-dev) — no new Jira keys invented
- [x] **STEP 8: Dev Docs**
  - `doc/dev/presenter_teardown.md` — collections owner, order, budget share, API, tests
  - `doc/dev/collection_import.md` — PYPOST-1321 shutdown ownership section; removed stale "not registered" claims; API/`TeardownResult`/observability updates
  - `doc/dev/presenter_architecture.md` — CollectionsPresenter shutdown cross-link
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1321/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1321/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_main_window_collections_shutdown_repro.py` (3 red tests; collections omitted from owner list)

### STEP 4: Development

- `pypost/ui/main_window_lifecycle.py` — collections owner before env
- `pypost/ui/presenters/collections_presenter_lifecycle.py` — new helper
- `pypost/ui/presenters/collections_presenter.py` — `begin_teardown` + `TeardownResult`
- `pypost/ui/presenters/collection_import_actions.py` — admission fence
- `pypost/core/lifecycle.py` — `CollectionsPresenter` owner map
- Tests updated: composition harness, bool→outcome callers, idle idempotent owners

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1321/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1321/50-observability.md`
- `pypost/core/metrics_registry.py` — `collections_presenter` in `_LIFECYCLE_OWNERS`
- `tests/test_lifecycle_observability.py` — collections correlated logs/metrics + main-window owner_count=5

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1321/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/presenter_teardown.md`
- `doc/dev/collection_import.md`
- `doc/dev/presenter_architecture.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
