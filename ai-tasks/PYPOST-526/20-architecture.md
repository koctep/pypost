# PYPOST-526: Architecture

## Change

`verify_decrypt_access()` calls `build_inventory(settings)` instead of duplicating
`_read_raw_environments` + `_scan_raw_environments` + `_check_missing_kids`.

Decrypt validation remains verify-only via `_deserialize_all()` →
`load_environments_with_errors()`.

## Tests

`test_verify_decrypt_access_uses_build_inventory` — spy on `build_inventory`.
