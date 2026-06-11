# PYPOST-572: CI log allowlist and post-run verifier

## Goals

Implement Phase 1 of the PYPOST-571 CI guardrails proposal: an ERROR allowlist derived from
the PYPOST-567 inventory and a post-run script that fails CI when pytest emits unlisted ERROR
lines or exceeds the baseline ERROR count + margin.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want CI to fail on unlisted ERROR log lines so that new regressions
  cannot hide among known error-path test noise.
- As a **maintainer**, I want a global ERROR count ceiling (baseline 72 + margin 5) so that
  silent ERROR storms are caught even when patterns repeat.
- As a **reviewer**, I want allowlist changes in git (YAML) so that permitted ERROR patterns
  are reviewable in PRs.

## Definition of Done

- [x] `tests/expected_log_allowlist.yaml` with baseline_error_count 72, error_margin 5, and
      rules covering PYPOST-567 expected ERROR groups.
- [x] `scripts/verify_test_log_guardrails.py` reuses `parse_log` from
      `scripts/parse_test_log_inventory.py`.
- [x] Verifier fails on unknown ERROR lines and on count > baseline + margin.
- [x] `tests/test_verify_test_log_guardrails.py` with `@pytest.mark.timeout(30)` per test.
- [x] `.github/workflows/test.yml` captures pytest log and runs verifier after pytest.
- [x] `doc/dev/testing.md` CI guardrails section updated with implementation details.

## Out of Scope

- Duration budget audit (PYPOST-573).
- `caplog` contract in `do-testing.md` (PYPOST-574).
- Reclassifying suspicious inventory groups.
