# PYPOST-804: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- Production `check-lock` remains local-only (PYPOST-779 follow-up debt); only dev lock is gated
  in CI because test tooling installs from `requirements-dev.txt` on every workflow run.
- `check-lock-dev` is not added to `make check` — contributors without `uv` can still run the
  default quality gate locally; CI enforces dev lock freshness.

## Code Quality Issues

None blocking. Job structure mirrors `security-audit` and reuses Makefile verification.

## Missing Tests

- No pytest invokes `make check-lock-dev` (requires `uv` and network). The new CI job is the
  integration test for dev lock drift.

## Performance Concerns

None. `uv pip compile` runs once per workflow in an isolated job (~seconds).

## Follow-up Tasks

### NON-BLOCKER — inherited debt

#### CI check-lock job (production)

- **Priority:** P3
- **Description:** Optional CI step to fail PRs when `requirements.txt` is stale vs
  `requirements.in`.
- **Remediation:** Add sibling job mirroring `check-lock-dev` when production lock CI is
  prioritized.
- **Source:** PYPOST-779 follow-up

#### pip-audit in dev lock

- **Priority:** P3
- **Description:** `pip-audit` is still installed inline for `make security-audit`.
- **Remediation:** [PYPOST-805](https://pypost.atlassian.net/browse/PYPOST-805)
