# PYPOST-1426: Developer Documentation Notes

## Updates

- Extended `doc/dev/workspace_environment_variable_import.md`:
  - Non-modal error section: flaky-network / corrupt-manifest recovery contracts
  - Testing section: `test_remote_collection_fault_injection_repro.py` and
    `tests/helpers/remote_collection_faults.py`

## Run

```bash
make test PYTEST_ARGS="tests/test_remote_collection_fault_injection_repro.py"
```
