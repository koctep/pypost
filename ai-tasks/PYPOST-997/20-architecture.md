# PYPOST-997: Architecture Design

## CI Lock Job Architecture

1. **`check-lock-otel` Job Specification**:
   - Runs on `ubuntu-latest`.
   - Steps:
     - `actions/checkout@v4` (pinned hash `11bd71901bbe5b1630ceea73d27597364c9af683`).
     - `astral-sh/setup-uv@v8.3.2` (pinned hash `11f9893b081a58869d3b5fccaea48c9e9e46f990`) with `version: "0.11.31"`.
     - `make check-lock-otel`.
     - Job summary write to `$GITHUB_STEP_SUMMARY`.

2. **Automated Verification Contract**:
   - `tests/test_ci_check_lock_job.py` parses `test.yml` using `workflow_job_block` helper and validates setup-uv version pin.
