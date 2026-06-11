# PYPOST-572: Code Cleanup

## Scope

- `scripts/verify_test_log_guardrails.py` — new CLI; reuses existing parser.
- `tests/expected_log_allowlist.yaml` — data file.
- `tests/test_verify_test_log_guardrails.py` — unit tests.
- `.github/workflows/test.yml` — two-line CI wiring.

## Checks

- UTF-8, LF, max 100 char lines per `.cursor/lsr/do-python.md`.
- No trailing whitespace; single final newline.
- Scripts dir bootstrap for `parse_test_log_inventory` import (same pattern as other scripts).
