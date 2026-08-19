# PYPOST-1057: Architecture Design

## Lock and License Synchronization Architecture

1. **Lock Compilation**:
   - `requirements.in` -> `requirements.txt` via `uv pip compile --upgrade --python-version 3.11`.
   - `requirements-dev.in` -> `requirements-dev.txt` via `uv pip compile --upgrade --python-version 3.11`.
   - `requirements-otel.in` -> `requirements-otel.txt` via `uv pip compile --upgrade --python-version 3.11`.

2. **License Inventory Regeneration**:
   - Executes `scripts/generate_license_inventory.py` to extract production package licenses via `pip-licenses` and format `LICENSES/transitive.csv`.

3. **CI Quality Gates**:
   - `check-lock`, `check-lock-dev`, `check-lock-otel`, and `check-license-inventory` verify exact byte equivalence after comment header stripping.
