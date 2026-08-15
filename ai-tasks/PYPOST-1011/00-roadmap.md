# Roadmap: PYPOST-1011

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_environment_export.py::test_write_export_file_raises_on_non_serializable_payload` (red: unhandled `TypeError` instead of `EnvironmentExportError`)
- [x] **STEP 4: Development**
  - [x] Added `pypost/core/export_file_writer.py` with `write_json_export_file(path, payload, *, error_cls)`: the single real implementation (mkdir parents → `json.dumps(indent=2)` → `write_text(text + "\n", encoding="utf-8")`), catching `(OSError, TypeError, ValueError)` and re-raising as `error_cls(f"Could not write file: {exc}")`. Log-free, Qt-free, no import of either domain module.
  - [x] Converted `pypost/core/collection_export.py::write_export_file` and `pypost/core/environment_export.py::write_export_file` into thin wrappers delegating to `write_json_export_file` with `error_cls=CollectionExportError` / `error_cls=EnvironmentExportError` respectively, keeping each module's existing success `logger.info(...)` line unchanged. Public signatures/exception types unchanged; no cross-domain import introduced (verified by grep).
  - [x] This closes the Step 3 red test: `tests/test_environment_export.py::test_write_export_file_raises_on_non_serializable_payload` now passes because environment export routes through the shared helper, which catches `TypeError`/`ValueError` in addition to `OSError`.
  - [x] Added `tests/test_export_file_writer.py` with direct unit coverage of the new shared module: successful write (parent-dir creation, indented UTF-8 JSON with trailing newline), `OSError` wrapped into a caller-supplied `error_cls`, non-serializable payload (`TypeError`) wrapped into a caller-supplied `error_cls`, and a check that a *different* caller-supplied `error_cls` is honored (not a hardcoded type).
  - [x] No call-site changes: `pypost/ui/presenters/collection_export_actions.py` and `pypost/ui/widgets/environments/environment_list_widget.py` untouched (verified by grep — still import `write_export_file`/error classes from their existing domain modules).
  - [x] Verification: `make test PYTEST_ARGS="tests/test_environment_export.py tests/test_collection_export.py tests/test_export_file_writer.py -v"` — 27/27 passed. `make lint` clean. `make typecheck` — mypy baseline gate OK (219 known errors, no new ones introduced). A whole-suite `make test` run hit a native `Bus error: 10` inside `tests/test_settings_encryption_migration_ui.py::test_reencrypt_runs_when_confirmed` (a Qt thread-teardown test unrelated to export code); reproduced this test passing in isolation on the pre-change code (`git stash` + rerun), confirming it is pre-existing full-suite flakiness, not a regression from this change.
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean on `pypost/`; direct flake8 pass on touched `tests/test_environment_export.py` found and fixed pre-existing `F401`/`E402` (unused `json` import, `pytestmark` sandwiched between import blocks) — unrelated to Step 4's diff but caught while reviewing the touched file.
  - [x] No unused imports/variables, commented-out code, debug prints, or dead code found in `export_file_writer.py`, `collection_export.py`, `environment_export.py`, `test_export_file_writer.py`. No line-length (>100) violations. No merge-conflict markers.
  - [x] `make test PYTEST_ARGS="tests/test_environment_export.py tests/test_collection_export.py tests/test_export_file_writer.py -v"` — 27/27 passed. All three test files carry module-level `pytestmark = pytest.mark.timeout(60)`.
  - [x] `make typecheck` — mypy baseline OK (219 known errors, no new ones from the touched files).
  - [x] See `ai-tasks/PYPOST-1011/40-code-cleanup.md` for full report.
- [x] **STEP 6: Observability**
  - [x] Analyzed whether the refactor needed new logging/metrics: it does not. Verified via `git diff HEAD` that both domain `write_export_file` wrappers' error-wrap behavior (message format, `from exc` chaining) is byte-for-byte preserved for collection export, and intentionally widened (now also catching `TypeError`/`ValueError`) for environment export — the deliberate, already-reviewed Step 3/4 fix, not a Step 6 concern.
  - [x] Confirmed both UI call sites (`pypost/ui/presenters/collection_export_actions.py`, `pypost/ui/widgets/environments/environment_list_widget.py`) already catch `CollectionExportError`/`EnvironmentExportError`, log `logger.warning("..._failed reason=%s", exc)`, and surface the message to the user — no information lost through the shared helper.
  - [x] No code changes made. `export_file_writer.py` intentionally stays log-free/Qt-free/domain-agnostic per the Step 4 architecture decision.
  - [x] `make test PYTEST_ARGS="tests/test_environment_export.py tests/test_collection_export.py tests/test_export_file_writer.py -v"` — 27/27 passed.
  - [x] See `ai-tasks/PYPOST-1011/50-observability.md` for full report.
- [x] **STEP 7: Review and Technical Debt**
  - [x] Analyzed implementation against `20-architecture.md`: matches plan exactly (single
    real implementation in `export_file_writer.py`, thin wrappers in both domain modules,
    no cross-domain import, no call-site changes). No shortcuts/crutches found.
  - [x] Verified all in-scope test files carry explicit `pytest.mark.timeout(60)` module
    markers (`test_export_file_writer.py:10`, `test_environment_export.py:22`,
    `test_collection_export.py:23`) — no missing-timeout BLOCKER.
  - [x] Re-ran `make test PYTEST_ARGS="tests/test_environment_export.py
    tests/test_collection_export.py tests/test_export_file_writer.py -v"` — 27/27 passed.
    `make lint` clean. `make typecheck` — mypy baseline OK (219 known errors, no new ones).
  - [x] No missing tests, no hardcoded values, no performance concerns, no follow-up Jira
    tasks needed. One doc-freshness note flagged for Step 8 (dev docs don't yet mention
    the new shared `export_file_writer.py` module) — not a Step 7 action item.
  - [x] See `ai-tasks/PYPOST-1011/60-tech-debt.md` for full report.
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/collection_export.md` (architecture bullets + core-helpers table)
    and `doc/dev/environments_dialog.md` (Export environments bullet list) to mention that
    `write_export_file` delegates to the shared
    `pypost/core/export_file_writer.py::write_json_export_file(path, payload, *,
    error_cls)` helper (PYPOST-1011).
  - [x] No standalone `doc/dev/export_file_writer.md` created — the helper is a small
    (44-line), single-function, internal implementation detail already covered by direct
    unit tests (`tests/test_export_file_writer.py`) and by both call-site docs; a full
    Overview/Architecture/Usage/Configuration/Troubleshooting doc would be disproportionate
    to its scope.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language

Python

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1011/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1011/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1011/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1011/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1011/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Suggested branch name (reference only)

`chore/PYPOST-1011-shared-export-write-helper`
