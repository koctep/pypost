# PYPOST-997: Add CI job for check-lock-otel with pinned uv

## Programming Language

GitHub Actions YAML for CI workflows, Python for contract tests, English Markdown for documentation.

## Goals

Follow-up from PYPOST-984. Production (`requirements.txt`) and dev (`requirements-dev.txt`) locks are gated in CI via dedicated `check-lock` and `check-lock-dev` jobs with pinned `uv` versions. OpenTelemetry dependencies (`requirements-otel.txt`) need the same CI gate.

**Business goal:** Add a `check-lock-otel` job in `.github/workflows/test.yml` mirroring `check-lock-dev` with pinned `uv` (`version: "0.11.31"`), protected by contract tests in `tests/test_ci_check_lock_job.py`.

## Definition of Done

- [ ] `.github/workflows/test.yml` contains a `check-lock-otel` job running `make check-lock-otel`.
- [ ] `check-lock-otel` uses `astral-sh/setup-uv` with pinned `version: "0.11.31"`.
- [ ] `tests/test_ci_check_lock_job.py` validates the job structure and pinned version.
- [ ] All tests pass cleanly.
