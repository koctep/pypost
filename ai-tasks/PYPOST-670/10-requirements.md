# PYPOST-670: CI allowlist / fail on unexpected ERROR

## Goals

Close the PYPOST-570 high-priority follow-up: CI must fail when pytest emits unlisted ERROR log
lines. Confirm acceptance criteria are met by the PYPOST-572 implementation.

## User Stories

- As a **maintainer**, I want CI to fail on unexpected ERROR lines so new regressions cannot hide
  among known error-path test noise.
- As a **reviewer**, I want allowlist changes in git so permitted ERROR patterns are reviewable
  in PRs.

## Definition of Done

- [x] `tests/expected_log_allowlist.yaml` — baseline 72, margin 5, PYPOST-567 rule coverage.
- [x] `scripts/verify_test_log_guardrails.py` — parses capture, matches allowlist, exit 0/1.
- [x] `tests/test_verify_test_log_guardrails.py` — unit tests with per-test timeouts.
- [x] `.github/workflows/test.yml` — `tee pytest.log` after pytest; verifier step on success.
- [x] CI fails when an ERROR line is unlisted or count exceeds baseline + margin.
- [x] `ai-tasks/PYPOST-670/` documents verification-only closure (no new code).

## Task Description

**Origin:** [PYPOST-570](../PYPOST-570/60-tech-debt.md) follow-up — "CI allowlist / fail on
unexpected ERROR". Implementation landed in PYPOST-572 (Done). This ticket records closure and
links artifacts.

**Scope:** Verification and documentation only. No source or workflow edits.

## Out of Scope

- Disabling `log_cli` in CI (PYPOST-671).
- Duration budget audit (PYPOST-573).
- `caplog` contract (PYPOST-574).
