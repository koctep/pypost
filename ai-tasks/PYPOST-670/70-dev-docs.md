# PYPOST-670: Dev Docs

## Updated Files

None. Developer reference already updated in PYPOST-572.

## Pointer

See `doc/dev/testing.md` — **CI guardrails (PYPOST-571 / PYPOST-572)**:

- Allowlist path and rule semantics (`logger` + `message_prefix` vs prefix-only).
- Verifier CLI: `python scripts/verify_test_log_guardrails.py pytest.log`.
- Baseline 72 + margin 5 thresholds.
- PR guidance: add allowlist rules when introducing intentional ERROR-path tests.

## Verification

Dev docs match `tests/expected_log_allowlist.yaml`, `scripts/verify_test_log_guardrails.py`,
and `.github/workflows/test.yml` wiring. No further edits required for this closure ticket.
