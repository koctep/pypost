# PYPOST-1071: Code Cleanup Report

Scope: only this task's own diff — the two new MCP modules, the four modified source/script
files, the changed tests, and the two `doc/dev/` pages. Caps, baselines and snapshots were
treated as frozen inputs and not regenerated in this step.

## Static Analysis

`make analyze` has no rule in this repository; static analysis is `make lint`
(flake8, `max-line-length = 100`, `extend-select = T201`) over `pypost/`, plus `make typecheck`
(mypy baseline gate).

- `make lint` — clean, exit 0.
- flake8 run explicitly over the in-scope `scripts/` and `tests/` files as well (not covered by
  the `pypost/`-only gate).

To separate this task's findings from the repository's pre-existing noise, every in-scope file
was linted at `HEAD` and in the working tree, and the per-file violation-code counts were
diffed. Exactly one delta existed across the whole diff:

- `tests/test_main_window.py` E402 6 → 7 — the added
  `from pypost.ui.mcp_server_controller import McpServerSettingsController`. **Kept as is**: the
  module deliberately places `pytestmark = pytest.mark.timeout(60)` above its imports, so every
  one of its imports is E402. The new line follows the established file pattern; "fixing" it
  would mean restructuring an untouched pre-existing convention.

Everything else reported by flake8 in these files (E402/E302/E304/E305, W293, E501, F401 in the
older test modules; T201 in the two `scripts/` CLIs, where `print` is the intended output) is
identical at `HEAD` and therefore out of scope.

## Linter Fixes

- Fixed: redundant `else` after an early `return` in
  `pypost/ui/mcp_server_controller.py::upsert_mcp_server`. The branch structure was carried over
  verbatim from `MainWindow` during the Step 4 extraction; the `else` block was unreachable-as-
  written dead structure. Dedented to a straight-line statement — behaviour identical.
- Fixed: one new over-length Markdown line, `doc/dev/solid_audit.md:118` (105 > 100). Shortened
  the link text from the full path to `mcp_controls_presenter.py`; the link target is unchanged.
  Verified with `scripts/check-line-length.sh`: `doc/dev/solid_audit.md` 8 → 7 long lines, the
  remaining 7 all pre-existing at `HEAD`.

## Code Formatting

- [x] Automatic code formatting — no reformatting needed; flake8 clean on `pypost/`.
- [x] Indentation and alignment fixes — the `else`-dedent above.
- [x] Line length correction — `doc/dev/solid_audit.md:118`.

## Code Cleanup

- Removed unused imports: **0**. Checked deliberately, because Step 4 moved large blocks out of
  two files. `pypost/ui/main_window.py` still legitimately uses `MCPServerManager` /
  `MCPServerRegistry` as constructor parameter annotations (lines 57–58);
  `pypost/ui/presenters/env_presenter.py` still uses `QLabel`, `QPushButton`, `AppSettings`,
  `MCPServerManager` and `MCPServerRegistry`. flake8 F401 confirms none are stale.
- Removed unused variables/attributes: **0**. `EnvPresenter._metrics` was verified still live
  after the MCP extraction (variable-validation metrics, lines 309–315).
- Removed commented-out code: none present.
- Removed debug prints: none. Grepped the four production files for
  `TODO/FIXME/XXX/breakpoint/pdb/print(` — no hits; T201 clean on `pypost/`.
- Removed dead code: the redundant `else` branch described above.

### Stale comment corrections

Two Step 3-era comments in `tests/test_verify_ai_task_artifacts.py` still described the verifier
in the present tense as *currently* demanding `70-dev-docs.md` and the new checks as *currently
red* — both untrue once Step 4 landed, so they misdescribed the code a reviewer would be
reading. Rewritten to past tense plus their present-day purpose (regression guards). No
assertion, node id, test name or behaviour changed.

- module comment above `OBSOLETE_DEV_DOCS_FILE`
- `TestCurrentStep8Contract` class docstring

## Validation Results

- [x] All tests passed — targeted affected modules: **113 passed**
  (`test_verify_ai_task_artifacts`, `test_solid_audit_baseline`, `test_main_window`,
  `test_env_presenter`, `test_mcp_server_manager`, `test_main_window_shutdown`,
  `test_main_window_alert_reload`, `test_main_window_encrypted_startup`,
  `test_apply_settings_font`, and the four `test_settings_*_main_window_e2e` modules).
  Full fast suite re-run after the edits: **2215 passed, 22 deselected** — unchanged from the
  pre-cleanup baseline.
- [x] All tests have explicit timeout markers — every changed test module carries a module-level
  `pytestmark = pytest.mark.timeout(...)` (30s for the verifier module, 60s for the window and
  presenter modules); no new test was added in this step.
- [x] No merge conflicts — no conflict markers in the diff.
- [x] Syntax is valid — flake8 parses every in-scope file.
- [x] Types are correct — see note below.
- [x] Cap check `scripts/audit_baseline_metrics.py --check` exits 0.
- [x] `make verify-ai-tasks` exits 0 (804 completed tasks; 227 grandfathered legacy gaps).

## Notes

**Typecheck is at the HEAD baseline, deliberately untouched.** `make typecheck` reports **8**
off-baseline errors. These are pre-existing at `HEAD` and are *not* part of this task: all 8 are
Qt `SignalInstance.connect` / worker `emit` overload complaints in
`pypost/core/qt/worker.py` (2), `pypost/ui/main_window_signals.py` (4),
`pypost/ui/presenters/collection_import_actions.py` (1) and
`pypost/ui/presenters/tabs_presenter.py` (1). Grepped the off-baseline list for this task's two
new modules — **zero** hits, so the extraction introduced no type regression. The mypy baseline
was **not** regenerated.

**Nothing regenerated.** No `--update-baseline`, no `--markdown`, no cap edit, no snapshot
rewrite in this step. `ai-tasks-artifacts-baseline.json`, `ai-tasks/PYPOST-376/baseline-metrics.md`
and `scripts/audit_baseline_metrics.py` caps are exactly as Step 4 left them.

**Out of scope, untouched.** `Makefile` and `tests/test_example_fixtures.py` carry unrelated
uncommitted PYPOST-1056/PYPOST-1048 work and were deliberately not modified, though they appear
in `git status`.

**For the reviewer.** The three edits in this step are small and behaviour-neutral; the diff to
read is the `else`-dedent in `mcp_server_controller.py`, the two comment rewrites in
`tests/test_verify_ai_task_artifacts.py`, and the one-line link shortening in
`doc/dev/solid_audit.md`.
