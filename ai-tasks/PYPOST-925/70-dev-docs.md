# PYPOST-925: Dev Docs

## Overview

Documented the strengthened Qt/EGL CI contract: maintainers edit the composite
`action.yml` only; pytest contract guards derive the expected package set from
that file via `_expected_qt_egl_packages()` (no duplicate frozenset in the test
module).

## Architecture

- **Composite action** — `.github/actions/install-qt-egl-runtime/action.yml`
  holds the apt `install` list for headless PySide6 on Ubuntu CI runners.
- **Derived contract** — `_expected_qt_egl_packages()` in
  `tests/test_ci_make_install_smoke_qt_runtime.py` parses the composite; tests
  assert non-empty set, `libegl1` sentinel, three-job `uses:`, and zero inline
  duplicate apt blocks.
- **Removed dual-edit** — `_PEER_QT_EGL_PACKAGES` hardcoded frozenset deleted;
  package changes require a single edit in `action.yml`.

## Usage

To add or remove a Qt/EGL runtime library for CI:

1. Edit package names in `.github/actions/install-qt-egl-runtime/action.yml` only.
2. Run the contract module:

```bash
make test PYTEST_ARGS='tests/test_ci_make_install_smoke_qt_runtime.py -v'
```

## Configuration

| Setting | Location |
| --- | --- |
| Apt package list (sole source) | `.github/actions/install-qt-egl-runtime/action.yml` |
| Expected set parser | `_expected_qt_egl_packages()` in `tests/test_ci_make_install_smoke_qt_runtime.py` |
| Job references | `.github/workflows/test.yml` (`uses:` on `test`, `make-install-smoke`, `agent-e2e`) |
| Headless platform | `QT_QPA_PLATFORM: offscreen` on each Qt-using job |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Contract fails after package change | Fix names in `action.yml`; do not add a parallel list to the test module |
| `test_qt_egl_contract_has_no_duplicate_authoritative_frozenset` fails | Remove reintroduced `_PEER_QT_EGL_PACKAGES`; derive from composite only |
| One CI job missing EGL libs | Confirm that job still has `uses: ./.github/actions/install-qt-egl-runtime` |
| Inline apt drift in workflow | Remove duplicate `sudo apt-get install` blocks from `test.yml` |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | CI Qt/EGL section and troubleshooting: `action.yml` sole edit point; derived contract; focused test command |
| `doc/dev/testing.md` | Parity table and `make-install-smoke` section: derived-only contract (PYPOST-925) |
