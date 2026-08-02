# PYPOST-1051: Fix CI failures in run 30744058063 (check-license-inventory and check-lock)

## Research

1. `make check-lock` executes `uv pip compile requirements.in -o requirements.txt.check --python-version 3.11` and compares `requirements.txt` against `requirements.txt.check`. Currently `requirements.txt` is missing updated package resolutions.
2. `make lock` runs `uv pip compile requirements.in -o requirements.txt --python-version 3.11 --generate-hashes`.
3. `make check-license-inventory` executes `python scripts/generate_license_inventory.py --check` which verifies that `LICENSES/transitive.csv` matches the packages in `requirements.txt`.
4. `make generate-license-inventory` executes `python scripts/generate_license_inventory.py` to regenerate `LICENSES/transitive.csv` from `requirements.txt`.

## Implementation Plan

1. **Step 3 (Failing Repro)**:
   - Command: `make check-lock`
   - Expected status: Fails with exit code 2 because `requirements.txt` is stale relative to `requirements.in`.
   - Command: `make check-license-inventory`
   - Sequence: Confirm `make check-lock` fails, then execute `make lock` and `make generate-license-inventory`, and verify `make check-lock` and `make check-license-inventory` pass.

2. **Step 4 (Development)**:
   - Run `make lock` to update `requirements.txt`.
   - Run `make generate-license-inventory` to update `LICENSES/transitive.csv`.
   - Verify with `make check-lock` and `make check-license-inventory`.

## Architecture

No runtime architectural changes are required. The task targets build tooling configuration, lock file synchronization, and license tracking documentation.

## Q&A

- **Q**: Are changes to python source files in `pypost/` required?
- **A**: No, this is purely dependency lock synchronization and license inventory generation.
