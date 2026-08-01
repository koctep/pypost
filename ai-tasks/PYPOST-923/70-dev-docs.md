# PYPOST-923: Dev Docs

## Overview

Documented CI Qt/EGL apt parity so `make-install-smoke` installs the same
Ubuntu runtime packages as the main `test` matrix and `agent-e2e`. Also notes
the lock/license inventory refresh delivered with this task.

## Architecture

- **Shared apt step** — `test`, `make-install-smoke`, and `agent-e2e` each run
  **Install Qt / EGL runtime** (`libdbus-1-3`, `libegl1`, `libfontconfig1`,
  `libfreetype6`, `libglib2.0-0`, `libgl1`, `libxcb-cursor0`, `libxkbcommon0`).
- **Contract lock** — `tests/test_ci_make_install_smoke_qt_runtime.py` asserts
  the smoke job package set matches the peer jobs.
- **Locks / inventory** — refreshed `requirements.txt`, `requirements-dev.txt`,
  and `LICENSES/transitive.csv` so `check-lock`, `check-lock-dev`, and license
  inventory `--check` stay green.

## Usage

No new make targets. Reproduce the contract and local gates with:

```bash
make test PYTEST_ARGS='tests/test_ci_make_install_smoke_qt_runtime.py -v'
make check-lock
make check-lock-dev
make check-license-inventory
```

## Configuration

None beyond `.github/workflows/test.yml` apt packages and existing lock files.
Jobs stay on GitHub-hosted `ubuntu-latest` (no Docker) so PySide6 can import
under `QT_QPA_PLATFORM=offscreen`.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| PySide6 / `libEGL` / fontconfig import fail on CI smoke only | Confirm `make-install-smoke` has the full peer Qt/EGL apt set |
| Contract test fails on missing packages | Align smoke job YAML with `test` / `agent-e2e`; update lock test only with docs |
| `check-lock` / `check-lock-dev` / license inventory red | Regenerate via `make lock` / `make lock-dev` / license inventory targets |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | CI Qt/EGL apt parity for smoke / test / agent-e2e; troubleshooting for missing `.so` |
| `doc/dev/testing.md` | Parity row in local-vs-CI table; `make-install-smoke` package-list + contract note |
| `requirements.txt` | Transitive lock refresh (certifi, mcp, sse-starlette, uvicorn, annotated-types) |
| `requirements-dev.txt` | Dev lock refresh (certifi, coverage, filelock, platformdirs, pip, types-pyyaml) |
| `LICENSES/transitive.csv` | License inventory refresh for updated pins |
