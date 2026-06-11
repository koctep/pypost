# PYPOST-572: Architecture

## Approach

Extend the PYPOST-567 offline log parser into a CI gate. No pytest plugins — capture stdout
after pytest and verify offline.

## Data flow

```
pytest (log_cli=true)
        │
        ▼
   pytest.log (tee in CI)
        │
        ▼
verify_test_log_guardrails.py
        │
        ├─ parse_log() ──► ERROR entries
        ├─ match rules in expected_log_allowlist.yaml
        ├─ fail if unknown ERROR
        └─ fail if count > 72 + 5
```

## Components

| Component | Role |
| --- | --- |
| `tests/expected_log_allowlist.yaml` | Logger + message_prefix rules; baseline and margin |
| `scripts/verify_test_log_guardrails.py` | Load allowlist, verify capture, exit 0/1 |
| `scripts/parse_test_log_inventory.py` | Shared `parse_log` / `classify_group` |
| `.github/workflows/test.yml` | `tee pytest.log` + verifier step |
| `tests/test_verify_test_log_guardrails.py` | Unit tests for matcher and thresholds |

## Allowlist rule matching

- **Logger + prefix:** entry logger equals rule logger AND message starts with prefix.
- **Prefix only:** message starts with prefix (any logger).
- Prefixes are structured event names from PYPOST-567 inventory (e.g.
  `request_execution_failed`, `mcp_operation_failed`).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | All ERROR lines allowed; count within margin |
| 1 | Unlisted ERROR and/or count exceeds baseline + margin |
