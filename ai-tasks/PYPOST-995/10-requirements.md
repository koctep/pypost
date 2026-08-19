# PYPOST-995: Pin uv version on check-lock-dev CI job

## Programming Language

YAML is used for GitHub Actions CI workflow definitions, Python for test verification, and English Markdown for task artifacts.

## Goals

Follow-up from PYPOST-984. In `.github/workflows/test.yml`, the production lock check (`check-lock`) pinned `astral-sh/setup-uv` to version `0.11.31` to prevent dependency resolver drift caused by automatic uv updates in CI. However, the dev lock check (`check-lock-dev`) remained unpinned.

**Business goal:** Pin `astral-sh/setup-uv` on the `check-lock-dev` CI job to `0.11.31` matching `check-lock`, and add regression test coverage in `tests/test_ci_check_lock_job.py`.

## Definition of Done

- [ ] `check-lock-dev` in `.github/workflows/test.yml` has `with: version: "0.11.31"`.
- [ ] `tests/test_ci_check_lock_job.py` contains `test_workflow_check_lock_dev_setup_uv_step_pins_version` asserting that `check-lock-dev` pins a non-empty `version:`.
- [ ] All tests pass cleanly.
