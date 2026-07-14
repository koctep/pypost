# PYPOST-741: Code cleanup

- No new lint issues in `pypost/core/http_client.py` or `tests/test_http_client.py`.
- Reused existing `sanitize_text` instead of duplicating redaction logic.
- ERROR log message prefixes unchanged (allowlist compatible).
