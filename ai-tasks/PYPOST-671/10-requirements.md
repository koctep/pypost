# PYPOST-671: Disable `log_cli` in CI

## Goals

Quiet CI stdout on green test runs while preserving post-run guardrails from PYPOST-572 and
PYPOST-573.

## User Stories

- As a **maintainer**, I want CI logs to show pytest progress without 200+ live application
  WARNING/ERROR lines on every green run.
- As a **reviewer**, I want CI to still fail on unexpected ERROR log lines and duration budget
  violations after disabling live CLI logging.

## Definition of Done

- [x] `.github/workflows/test.yml` adds `-o log_cli=false` to the main pytest command.
- [x] Application logs still captured for the allowlist verifier via `--log-file`.
- [x] Duration audit reads pytest stdout from `pytest-output.txt` (not the log file).
- [x] `pytest.ini` unchanged — local `make test` keeps `log_cli = true`.
- [x] `ai-tasks/PYPOST-671/` documents the change.

## Task Description

**Origin:** [PYPOST-570](../PYPOST-570/60-tech-debt.md) recommended CI-only `-o log_cli=false`.
PYPOST-572 added the ERROR allowlist verifier; this ticket implements the quiet-CI half of the
hybrid design.

**Scope:** `.github/workflows/test.yml` only. No application code or `pytest.ini` changes.

## Out of Scope

- Changing local `log_cli` defaults (PYPOST-570 keeps `true` / `WARNING`).
- Allowlist rules or verifier logic (PYPOST-572).
- `caplog` contract (PYPOST-574).
