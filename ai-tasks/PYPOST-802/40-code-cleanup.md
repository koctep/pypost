# PYPOST-802: Code Cleanup

## Changes Reviewed

- New module `pypost/core/request_fields.py` — single canonical dataclass + aliases.
- Removed duplicate class bodies from `http_client.py` and `sensitive_data_masking_policy.py`.
- Import paths preserved for existing consumers of `ResolvedRequestFields` from `http_client`.

## Cleanup Actions

- Dropped unused `dataclass` import from `sensitive_data_masking_policy.py`.
- Kept `from __future__ import annotations` in `request_fields.py` for consistency with core modules.
- No dead code or formatting issues introduced.

## Result

Minimal diff (~30 LOC net). No lint violations expected.
