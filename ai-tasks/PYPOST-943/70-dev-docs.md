# PYPOST-943: Dev Docs

## Overview

Documented slow Makefile install smoke seed contract: isolated workspaces must mirror
committed packaging metadata (dynamic version attr, readme), not only dependency pins.

## Architecture

- **`_seed_installable_package`** — copies repo `pypost/version.py` and `README.md` into the
  slow-smoke `tmp_path` workspace atop the stub `pypost/__init__.py`.
- **`make_workspace_full_deps`** — wires real `pyproject.toml` + installable seed for
  `TestSlowInstallSmoke`.
- **Fast contract guard** — `tests/test_makefile_install_seed_contract.py` parses
  `pyproject.toml` and asserts seed paths before network install.

## Usage

Reproduce the contract and slow smoke locally:

```bash
make test PYTEST_ARGS='tests/test_makefile_install_seed_contract.py -v'
make test-slow
```

CI runs slow marker via the `make-install-smoke` job (Python 3.11).

## Configuration

None beyond committed `pyproject.toml` dynamic metadata and existing Makefile targets.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `ModuleNotFoundError: No module named 'pypost'` during slow `make install` | Seed missing `pypost/version.py` for dynamic version attr — extend `_seed_installable_package` |
| Seed contract test fails after `pyproject.toml` change | Add new install-time paths to seed helper and `_required_seed_paths_from_pyproject` |
| Slow smoke red but full-checkout CI install passes | Gap is fixture-only; peer jobs use full tree, smoke uses isolated workspace |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Slow smoke seed contract table, helpers, contract test command |
