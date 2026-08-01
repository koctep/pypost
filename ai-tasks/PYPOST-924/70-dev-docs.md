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
  the composite exists, all three jobs reference it, and no inline duplicate
  apt blocks remain.

## Usage

To add or remove a Qt/EGL runtime library for CI:

1. Edit package names in `.github/actions/install-qt-egl-runtime/action.yml`.
2. Update `_PEER_QT_EGL_PACKAGES` in
   `tests/test_ci_make_install_smoke_qt_runtime.py` (until PYPOST-925 derives
   the set from the composite alone).
3. Run the contract module:

```bash
make test PYTEST_ARGS='tests/test_ci_make_install_smoke_qt_runtime.py -v'
```

## Configuration

| Setting | Location |
| --- | --- |
| Apt package list | `.github/actions/install-qt-egl-runtime/action.yml` |
| Job references | `.github/workflows/test.yml` (`uses:` step per Qt job) |
| Headless platform | `QT_QPA_PLATFORM: offscreen` on each Qt-using job |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| PySide6 / `libEGL` import fail on one CI job only | Confirm that job still has `uses: ./.github/actions/install-qt-egl-runtime` |
| Contract test fails on package set | Align `action.yml` with `_PEER_QT_EGL_PACKAGES` in the contract module |
| Inline apt drift reappears | Remove duplicate `sudo apt-get install` blocks from `test.yml`; keep packages in the composite only |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | Name composite path for CI Qt/EGL provisioning; troubleshooting points at `action.yml` |
| `doc/dev/testing.md` | Parity table and `make-install-smoke` section reference the composite instead of inline apt |
