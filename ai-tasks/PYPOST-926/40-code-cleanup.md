# PYPOST-926: Code Cleanup

## Changes

- Removed unused top-level `QApplication` import from `tests/conftest.py`; import now
  lives only inside `qapp`.
- New contract module uses `from __future__ import annotations`, module-level
  `pytestmark = pytest.mark.timeout(10)`, and a subprocess snippet constant (matches
  PYPOST-923/925 contract-test style).

## Verification

- `make lint` — no new issues in touched files.
- `make test PYTEST_ARGS='tests/test_conftest_lazy_qt_import.py -v'` — 2 passed.
- Spot GUI: `make test PYTEST_ARGS='tests/test_style_manager_appearance.py -q'` — green.

## Intentionally not changed

- Per-module PySide6 imports in GUI test files (out of scope).
- `tests/test_ci_make_install_smoke_qt_runtime.py` docstrings (still accurate for
  full-suite GUI collection).
