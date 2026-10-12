# PYPOST-1359: Technical Debt Analysis

## Shortcuts Taken

- **Makefile Fallback Syntax**: In `Makefile`, `UV ?=` was extended using shell evaluation (`UV ?= $(shell command -v uv 2>/dev/null || ( [ -x $(BIN)/uv ] && echo $(BIN)/uv ) || echo uv)`) to enable seamless execution in environments without `uv` globally on `PATH`. While practical and resilient, embedding shell subshell discovery directly in variable assignments is a pragmatic shortcut rather than establishing an isolated, dedicated tooling bootstrap wrapper script or centralized virtualenv tool runner.
- **Transitive Lock Re-resolution Scope**: Transitive packages in `requirements-dev.txt` were re-resolved via `make lock-dev` against live PyPI package indexes. We relied on `uv pip compile` default resolution rather than creating separate pinned lower-bound constraints for transitive dependencies in `requirements-dev.in`.

## Code Quality Issues

- **Duplicated Retry Logic in Makefile**: The retry loop, exponential backoff, header stripping (`tail -n +3`), and temporary artifact cleanup logic is duplicated across `check-lock`, `check-lock-dev`, and `check-lock-otel` in `Makefile`. A shared Makefile macro, shell helper, or centralized script (e.g. `scripts/verify_lockfile.sh`) would eliminate redundancy and reduce maintenance overhead across the lock verification targets.
- **Repro Test Process Execution**: `tests/test_lockfile_verification.py` invokes `make check-lock-dev` as an external subprocess. While necessary to assert the Make interface and return code semantics contractually, invoking Make from pytest tests has higher overhead than in-process assertions and relies on the shell environment.

## Missing Tests

- **None for the Implemented Scope**: The new repro and verification test `tests/test_lockfile_verification.py` covers the exact failure contract of `check-lock-dev` and includes explicit test timeouts (`pytestmark = pytest.mark.timeout(60)` and subprocess `timeout=45`).
- **Absence of Negative Verification Test**: There is currently no automated test that artificially introduces a mismatch into `requirements-dev.txt` to assert that `check-lock-dev` continues to fail closed (exit code 1) on drift; the existing test only verifies the clean zero-drift state.

## Performance Concerns

- **Network Compilation Overhead**: Running `uv pip compile` during lock verification checks queries the network index (PyPI) unless wheels or metadata are pre-cached. On cold runners or restricted networks, `make check-lock-dev` takes 1-3 seconds per run. A network interruption or transient PyPI latency relies on the 3-attempt exponential backoff retry loop.
- **Subprocess Execution in Verification Tests**: Subprocess execution of `make check-lock-dev` within `tests/test_lockfile_verification.py` takes ~1.4 seconds, which is acceptable for isolated verification but adds cumulative runtime if executed frequently during local fast-test cycles.

## Follow-up Tasks

- **Production Requirements Lock Drift**:
  - `make check-lock` for production requirements (`requirements.txt`) currently fails with drift relative to `requirements.in` if recompiled with fresh PyPI (e.g., newer patch releases of `cryptography`, `mcp`, `pydantic`, `pyside6`, `requests`, `urllib3`, `uvicorn`).
  - Follow-up ticket needed to refresh and verify production `requirements.txt` via `make lock` without introducing runtime regressions.
- **Deduplication of Makefile Lock Verification Logic**:
  - Refactor Makefile targets `check-lock`, `check-lock-dev`, and `check-lock-otel` to use a parameterized macro or shared verification script (`scripts/verify_lockfile.sh`) to eliminate ~70 lines of duplicated shell logic.
- **Pre-existing Failing Tests Triage**:
  - The following 5 test failures were observed during full test suite runs (`make test`), predating this task's scope (`NON-BLOCKER — pre-existing`):
    - `tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test` (Failure due to baseline test lint errors in bare venv setup)
    - `tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install` (Failure due to baseline test lint errors in temporary workspace)
    - `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` (Pre-existing dialog audit report inventory drift)
    - `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` (Pre-existing LOC report discovery drift)
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` (Pre-existing markdown metrics snapshot discrepancy)
