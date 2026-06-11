# PYPOST-311: CI dependency caching

## Goals

PyPost CI installs application and test dependencies on every push and pull request. Repeated
PyPI downloads add minutes to feedback loops and increase flakiness from network timeouts.
Maintainers need faster CI without sacrificing reproducibility when dependency declarations
change.

## User Stories

- As a **maintainer**, I want CI to reuse cached pip wheels when `requirements.txt` is
  unchanged so the test matrix stays fast on warm runners.
- As a **contributor**, I want dependency changes to invalidate the cache automatically so I
  never run tests against stale packages after editing `requirements.txt`.
- As a **reviewer**, I want the caching approach documented so I can reason about CI behavior
  when reviewing dependency PRs.

## Definition of Done

- GitHub Actions workflow caches pip dependencies for both the main pytest matrix and the slow
  Makefile install smoke job.
- Cache invalidation is tied to the content hash of `requirements.txt`.
- Developer documentation describes the caching strategy, scope, and limitations.
- No change to local `make install` / `make venv-test` behavior beyond documentation cross-links.

## Task Description

**Source:** Follow-up debt from PYPOST-33, PYPOST-307, PYPOST-310, and PYPOST-559.

**Scope:** `.github/workflows/test.yml`, `doc/dev/testing.md`. No application code changes.

**Constraints:**

- Deterministic installs: cache key must reflect `requirements.txt` content.
- Preserve existing CI job split (fast matrix vs slow install smoke).
- Do not pin or rewrite dependency versions beyond what the task requires.

## Q&A

- **Why not cache the entire `.venv`?** CI uses system Python with direct `pip install`; local
  developers use Makefile-managed `.venv`. Pip wheel cache via `setup-python` matches CI layout
  and avoids venv path coupling.
- **Why hash only `requirements.txt`?** Application dependencies dominate install time; test
  tooling (pytest, flake8) is small and installed outside the lock file by design.
