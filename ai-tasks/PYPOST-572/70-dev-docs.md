# PYPOST-572: Dev Docs

Updated `doc/dev/testing.md` **CI guardrails (PYPOST-571 / PYPOST-572)** section with:

- Allowlist file path and rule semantics (logger + prefix vs prefix-only).
- Verifier CLI usage (local and CI).
- Baseline 72 + margin 5 thresholds.
- PR guidance: add allowlist rules when introducing intentional ERROR-path tests.

Implementation references:

- `tests/expected_log_allowlist.yaml`
- `scripts/verify_test_log_guardrails.py`
- `.github/workflows/test.yml` — `pytest.log` capture + verifier step
