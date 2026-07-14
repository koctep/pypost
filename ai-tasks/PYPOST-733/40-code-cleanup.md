# PYPOST-733: Code Cleanup

## Lint / Format

- No new flake8 violations introduced.
- `# noqa: BLE001` retained only on the intentional last-resort handler in
  `deserialize_environment_records`.

## Files Changed

| File | Change |
| --- | --- |
| `pypost/core/storage.py` | Typed exception handlers |
| `pypost/core/alert_manager.py` | Typed exception handlers |
| `tests/test_storage_environments.py` | 3 new tests |
| `tests/test_storage_collections.py` | 2 new tests |
| `tests/test_alert_manager.py` | 1 new test |
