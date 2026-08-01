# Roadmap: PYPOST-986

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red test: `tests/test_environment_import.py` (failed at collection with
    `ModuleNotFoundError: pypost.core.environment_import` before Step 4; now green)
- [x] **STEP 4: Development**
  - [x] Implemented `pypost/core/environment_import.py` (pure, no Qt):
    `EnvironmentImportFileError`, `ImportConflictDecision`, `ImportPlanResult`,
    `load_import_candidates`, `find_conflicts`, `generate_import_copy_name`,
    `plan_import`, `format_import_result` — reuses
    `StorageManager.deserialize_environment_records` and
    `environment_ops.clone_environment` per architecture. All 12 tests in
    `tests/test_environment_import.py` pass (Step 3 red test now green).
  - [x] Added import dialogs to `pypost/ui/collection_item_dialogs.py`
    (`prompt_import_environments_file` via `QFileDialog`,
    `show_import_invalid_file_error`, `prompt_import_conflict` with
    Overwrite/Keep Both/Skip buttons plus an "apply to all remaining conflicts"
    checkbox, `show_import_result`) and matching strings in
    `pypost/core/environment_messages.py`.
  - [x] Wired `EnvironmentListWidget.import_environments()`: file picker →
    `read_import_file` callable → zero-candidates/invalid-file guard (routes to
    the same "nothing changed" error dialog) → per-conflict prompt loop with
    "apply to all" shortcut → `plan_import` → in-place list update → `load_list()`
    → `format_import_result` → `show_import_result`. New `Import…` button next
    to `Add`, identified via new `ENV_IMPORT_BUTTON` in `pypost/ui/widget_ids.py`.
    Structured logging (`environment_import_file_invalid`,
    `environment_import_completed ...`) follows the existing convention.
  - [x] Forwarded `read_import_file` through `EnvironmentDialog` (plus an
    `import_environments()` passthrough) and wired it in
    `EnvPresenter._open_env_manager` as
    `lambda path: load_import_candidates(path, self._storage)` — no change to
    the existing post-dialog save path, so the atomic whole-list rewrite and
    the current encryption setting are inherited unchanged.
  - [x] Added `tests/test_environment_list_widget.py` (9 Qt-level tests):
    happy path, cancelled file picker, invalid file, zero-candidates,
    single-conflict prompt, "apply to all" shortcut, partial-parse success,
    no-op without `read_import_file`, and the `environment_import_completed`
    log line.
  - [x] Full suite: `make test` — 1954 passed, 1 pre-existing unrelated failure
    (`test_agent_e2e_harness_table_matches_marked_modules`, about
    `tests/test_agent_ui_actions_mcp.py`'s `agent_e2e` mark vs. doc table; not
    touched by this task, confirmed pre-existing via `git status`/`git log`).
  - Residual: `doc/user/environments.md` "Import environments" section is
    Step 8 (Dev Docs) per the roadmap artifacts list — not done in this step.
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean on all PYPOST-986 `pypost/` files.
  - [x] Fixed 5× `E731` in `tests/test_environment_list_widget.py`
    (lambda-assignment fixtures → `def`).
  - [x] `make test` — 1954 passed, 1 pre-existing unrelated failure
    (`test_agent_e2e_harness_table_matches_marked_modules`); PYPOST-986-scoped
    run — 86 passed.
  - [x] `make typecheck` baseline reviewed: no net-new mypy errors in touched
    files (pure line-shift of already-baselined Qt stub errors); the single
    baseline-count mismatch traces to an untouched file
    (`tabs_presenter_worker.py`) and is left unregenerated per
    `ai-tasks/PYPOST-831` precedent.
  - See `ai-tasks/PYPOST-986/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - [x] Verified and documented existing Step 4 structured logging
    (`environment_import_file_parsed`, `environment_import_file_invalid`,
    `environment_import_completed`) — no new logging/metrics needed; all log
    lines already covered by `caplog`-based tests.
  - See `ai-tasks/PYPOST-986/50-observability.md`.
- [x] **STEP 7: Review and Technical Debt**
  - [x] Analyzed for shortcuts, code quality, missing tests, performance,
    architecture deviations, hardcoded values — no blockers found; 5
    actionable follow-ups recorded (incl. the ciphertext-envelope-reuse-cache
    × import-Overwrite interaction nuance).
  - [x] No architecture deviations; doc update (`doc/user/environments.md`)
    correctly deferred to Step 8 per this roadmap's artifact list.
  - See `ai-tasks/PYPOST-986/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - [x] Added an "Import environments" section to `doc/user/environments.md`
    (file shape, single-object/list acceptance, Overwrite/Keep Both/Skip
    conflict prompt with "apply to all remaining conflicts", the summary
    dialog, and the Hidden/encryption and invalid-file guarantees).
  - [x] Extended the existing `doc/dev/environments_dialog.md` with an
    "Import environments (PYPOST-986)" section documenting
    `pypost/core/environment_import.py`'s public surface, the
    `EnvironmentListWidget.import_environments()` orchestration, the
    identity-preserving Overwrite decision, and the relevant tests — no new
    `doc/dev` file created, consistent with PYPOST-449/PYPOST-496 extending
    this same file for other changes to the same widget family.
  - [x] Created `ai-tasks/PYPOST-986/70-dev-docs.md`.
  - See `ai-tasks/PYPOST-986/70-dev-docs.md`.

## Language

- **Programming language**: Python (existing pypost desktop application)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-986/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-986/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-986/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-986/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-986/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/user/environments.md`
- `doc/dev/environments_dialog.md`
- `ai-tasks/PYPOST-986/70-dev-docs.md`

## Suggested branch name

`feature/PYPOST-986-import-environments`
