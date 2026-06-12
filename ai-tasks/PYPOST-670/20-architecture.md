# PYPOST-670: Architecture

## Current State (PYPOST-572)

Architecture is documented in [PYPOST-572](../PYPOST-572/20-architecture.md). Summary:

```
pytest (log_cli=true) → pytest.log (tee in CI)
        → verify_test_log_guardrails.py
        → parse_log + allowlist match → exit 0 or 1
```

| Component | Role |
| --- | --- |
| `tests/expected_log_allowlist.yaml` | Logger + message_prefix rules; baseline and margin |
| `scripts/verify_test_log_guardrails.py` | Load allowlist, verify capture, exit 0/1 |
| `scripts/parse_test_log_inventory.py` | Shared `parse_log` / `classify_group` |
| `.github/workflows/test.yml` | `tee pytest.log` + verifier step (lines 64–66) |
| `tests/test_verify_test_log_guardrails.py` | Matcher and threshold unit tests |

## Verification Plan

1. Confirm CI workflow runs verifier after pytest with `pytest.log` input.
2. Confirm allowlist YAML and verifier script exist and unit tests pass.
3. Record closure in `ai-tasks/PYPOST-670/` — no architecture change required.

## Outcome

All checks pass. PYPOST-670 closes the PYPOST-570 follow-up; design and wiring are unchanged from
PYPOST-572.
