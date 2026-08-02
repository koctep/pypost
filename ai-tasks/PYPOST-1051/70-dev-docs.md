# PYPOST-1051: Developer Documentation

## Overview

Documentation for dependency lock synchronization and transitive license inventory generation.

## CI Checks and Commands

- **`make check-lock`**: Compiles `requirements.in` using `uv` to `requirements.txt.check` and verifies that `requirements.txt` matches.
- **`make lock`**: Re-generates `requirements.txt` from `requirements.in`. When upgrading or refreshing stale locks, remove `requirements.txt` prior to running `make lock` or pass `--upgrade` / `--refresh` to `uv pip compile`.
- **`make generate-license-inventory`**: Regenerates `LICENSES/transitive.csv` from `requirements.txt`.
- **`make check-license-inventory`**: Verifies that `LICENSES/transitive.csv` is up to date with `requirements.txt`.

## Maintenance Workflow

When dependencies in `requirements.in` are updated or stale:
1. Run `rm -f requirements.txt && make lock`
2. Run `make generate-license-inventory`
3. Run `make check-lock` and `make check-license-inventory`
4. Commit updated `requirements.txt` and `LICENSES/transitive.csv`.
