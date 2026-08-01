# PYPOST-927: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- `check-lock` is not added to `make check` — contributors without `uv` can still run the
  default quality gate locally; CI enforces production lock freshness.
- `check-lock-otel` remains local-only (unchanged inherited debt from PYPOST-787).

## Code Quality Issues

None blocking. Job structure mirrors `check-lock-dev` and reuses Makefile verification.

## Missing Tests

- No pytest invokes `make check-lock` (requires `uv` and network). The new CI job is the
  integration test for production lock drift.
- Static contract test covers job presence and `make check-lock` invocation only.

## Performance Concerns

None. `uv pip compile` runs once per workflow in an isolated job (~seconds).

## Follow-up Tasks

### NON-BLOCKER — inherited debt

#### CI check-lock-otel job

- **Priority:** Low
- **Description:** Optional CI step to fail PRs when `requirements-otel.txt` is stale vs
  `requirements-otel.in`.
- **Remediation:** Add sibling job mirroring `check-lock` when OTel lock CI is prioritized.
- **Source:** PYPOST-787 follow-up

#### pip-audit in dev lock

- **Priority:** Low
- **Description:** `pip-audit` scanning policy unchanged.
- **Remediation:** See existing dependency audit docs.

## Resolved debt

- PYPOST-923 TD-4 / PYPOST-779 production `check-lock` CI gap — closed by this task.
