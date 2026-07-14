# PYPOST-780: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- Dev lock compiled for Python 3.11 only; 3.13 CI relies on forward compatibility (same pattern
  as production lock, PYPOST-779).
- `check-lock-dev` is not wired into CI (requires `uv` on runner); documented for local use.
- `pip-audit` remains an ad-hoc install in `make security-audit` / CI security job (out of
  scope for dev test tooling lock).

## Code Quality Issues

None blocking. Makefile and CI changes mirror PYPOST-779 conventions.

## Missing Tests

- No integration test runs `make lock-dev` or `make check-lock-dev` (requires `uv` and network).
  Static tests cover file presence, Makefile graph, and `venv-test` install smoke.

## Performance Concerns

None. Dev lock compilation is maintainer-only.

## Follow-up Tasks

### NON-BLOCKER — existing PYPOST-691 debt

#### CI check-lock-dev job

- **Priority:** P3
- **Description:** Optional CI step to fail PRs when `requirements-dev.txt` is stale vs
  `requirements-dev.in`.
- **Remediation:** Add lightweight job with `uv` setup when CI uv adoption is standardized.
- **Jira:** [PYPOST-804](https://pypost.atlassian.net/browse/PYPOST-804)

#### pip-audit in dev lock

- **Priority:** P3
- **Description:** `pip-audit` is still installed inline for `make security-audit`.
- **Remediation:** Add to `requirements-dev.in` if security tooling should share the dev lock.
- **Jira:** [PYPOST-805](https://pypost.atlassian.net/browse/PYPOST-805)

#### pyproject.toml optional dev extra

- **Priority:** P3
- **Description:** PEP 621 metadata and `[project.optional-dependencies]` still absent.
- **Remediation:** [PYPOST-434](https://pypost.atlassian.net/browse/PYPOST-434)
