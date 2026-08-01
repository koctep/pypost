# PYPOST-924: Dev Docs

## Overview

Documented the shared Qt/EGL CI provisioner so maintainers edit one composite
action instead of three inline apt blocks in `.github/workflows/test.yml`.

## Architecture

- **Composite action** — `.github/actions/install-qt-egl-runtime/action.yml`
  holds the eight-package `apt-get install` list for headless PySide6 on Ubuntu
  CI runners.
- **Job wiring** — `test`, `make-install-smoke`, and `agent-e2e` each use
  `uses: ./.github/actions/install-qt-egl-runtime` after checkout and before
  `actions/setup-python`.
- **Contract lock** — `tests/test_ci_make_install_smoke_qt_runtime.py` asserts
  the composite exists, all three jobs reference it, no inline duplicate apt
  blocks remain, and `_expected_qt_egl_packages()` parses the composite as the
  sole authoritative package set (PYPOST-925; no hardcoded frozenset).

## Usage

To add or remove a Qt/EGL runtime library for CI:

1. Edit package names in `.github/actions/install-qt-egl-runtime/action.yml`
   only — contract tests derive the expected set via `_expected_qt_egl_packages()`.
2. Run the contract module:

```bash
make test PYTEST_ARGS='tests/test_ci_make_install_smoke_qt_runtime.py -v'
```

## Configuration

| Setting | Location |
| --- | --- |
| Apt package list | `.github/actions/install-qt-egl-runtime/action.yml` |
| Expected set parser | `_expected_qt_egl_packages()` in `tests/test_ci_make_install_smoke_qt_runtime.py` |
| Job references | `.github/workflows/test.yml` (`uses:` step per Qt job) |
| Headless platform | `QT_QPA_PLATFORM: offscreen` on each Qt-using job |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| PySide6 / `libEGL` import fail on one CI job only | Confirm that job still has `uses: ./.github/actions/install-qt-egl-runtime` |
| Contract test fails on package set | Fix package names in `action.yml`; tests parse that file via `_expected_qt_egl_packages()` |
| Inline apt drift reappears | Remove duplicate `sudo apt-get install` blocks from `test.yml`; keep packages in the composite only |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | Name composite path for CI Qt/EGL provisioning; troubleshooting points at `action.yml` only (no test frozenset) |
| `doc/dev/testing.md` | Parity table and `make-install-smoke` section reference the composite instead of inline apt |
