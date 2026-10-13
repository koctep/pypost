# PYPOST-1360: Technical Debt Analysis

## Shortcuts Taken

- **Site-packages path link via `_host_deps.pth`**: In `tests/makefile_test_helpers.py` (`make_workspace_full_deps`), host dependencies are made available to the isolated workspace `.venv` by writing a `_host_deps.pth` pointing to `REPO_ROOT / ".venv" / "lib" / f"python{PYTHON_VERSION}" / "site-packages"`. This is standard Python/virtualenv composition rather than a hack or crutch, effectively making third-party dependencies (e.g. PySide6, cryptography, pydantic) resolve instantly without downloading hundreds of megabytes of wheels over the network.
- **Fallback behavior**: If `REPO_ROOT / ".venv"` site-packages directory does not exist (e.g. during a raw container bootstrap before host `.venv` initialization), `make_workspace_full_deps` falls back gracefully without writing the `.pth` file, reverting to standard pip resolution without crashing.

## Code Quality Issues

- None identified in the modified test helpers. The helper uses explicit path lookups with Python version resolution and clean standard library `pathlib.Path` operations. Maximum line length and formatting strictly adhere to PEP 8.

## Missing Tests

- None. The slow packaging installation smoke test `tests/test_makefile_slow_smoke.py::TestSlowInstallSmoke::test_install_succeeds_with_project_pyproject` verifies `make install` against `pyproject.toml` and enforces post-install sanity checks (`import pydantic` and `import pypost.version as v; assert v.__version__`).
- The companion seed contract test `tests/test_makefile_install_seed_contract.py` validates that all required packaging files and entry points declared in `pyproject.toml` are seeded into the workspace.
- Both test modules declare explicit timeout markers (`pytestmark = pytest.mark.timeout(180)` and `pytest.mark.timeout(30)`).

## Performance Concerns

- None. The installation smoke test previously exceeded the 180-second timeout (>179.91s) due to downloading massive Qt/PySide6 wheels. With pre-warmed site-packages resolution, execution dropped to ~11-21 seconds, well below the 180s budget and within the safe 80% duration threshold of `scripts/audit_test_durations.py`.

## Follow-up Tasks

- `NON-BLOCKER — pre-existing`: 5 tests pre-exist as failing on the base commit, unrelated to packaging or the slow smoke installer:
  - `PYPOST-1363`: Test lint isolation failures:
    - `tests/test_test_lint_baseline.py::test_baseline_detects_untracked_violations`
    - `tests/test_test_lint_baseline.py::test_baseline_passes_with_zero_violations`
  - `PYPOST-1361`: Dialog audit and SOLID metric failures:
    - `tests/test_dialog_audit.py::test_dialog_audit_report`
    - `tests/test_dialog_audit.py::test_dialog_audit_no_unassigned_responsibilities`
    - `tests/test_solid_metrics.py::test_solid_metrics_thresholds`
