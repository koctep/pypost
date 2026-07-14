# PYPOST-779: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- Lock compiled for Python 3.11 only; 3.13 CI relies on forward compatibility (verified by
  diff — only stdlib backport packages differ).
- `check-lock` is not wired into CI (requires `uv` on runner); documented for local/optional use.

## Code Quality Issues

None blocking. Makefile lock targets follow existing conventions.

## Missing Tests

- No integration test runs `make lock` or `make check-lock` (would require `uv` and network in
  CI). Static tests cover file presence and Makefile graph.

## Performance Concerns

None. Lock compilation is a maintainer-only operation.

## Follow-up Tasks

### NON-BLOCKER — existing PYPOST-691 debt

#### R-P2-002 — Consolidate dev dependencies

- **Priority:** P2
- **Description:** pytest/flake8 still installed from duplicate unpinned lines in Makefile and CI.
- **Remediation:** `requirements-dev.txt` with pins; `make install-dev`.
- **Jira:** [PYPOST-780](https://pypost.atlassian.net/browse/PYPOST-780)

#### R-P2-005 — Reconcile starlette and uvicorn direct declarations

- **Priority:** P2
- **Description:** Now resolved transitively via `mcp`; direct lines removed from `requirements.in`.
- **Remediation:** Covered by this lock; no separate issue needed.

#### CI check-lock job

- **Priority:** P3
- **Description:** Optional CI step to fail PRs when `requirements.txt` is stale vs `requirements.in`.
- **Remediation:** Add lightweight job with `uv` setup when CI uv adoption is standardized.
