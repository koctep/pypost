# PYPOST-1422: Extreme Concurrency Stress for Shared Venv Materialization

## Goals

Makefile integration suites materialize many workspace `.venv` trees from a shared skeleton
template in parallel. After [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413),
high worker counts under slow disk (NFS-like latency) caused preparation timeouts and flaky
CI. Later work moved ownership to `SharedVenvManager` (PYPOST-1419), switched population to
in-process copy (PYPOST-1420), and deepened template readiness (PYPOST-1421). The suite still
only proves a **4-worker** load budget; it does not prove that the harness stays reliable at
**16+ concurrent** materializations when disk latency is present.

The business goal of this task is to add an automated extreme-concurrency stress check that
gives CI and maintainers confidence that shared-venv materialization remains correct and
within contention limits when many workspaces prepare at once under simulated slow I/O—closing
the residual risk called out from PYPOST-1413 / PYPOST-1421 without changing the ordinary
4-worker readiness contract.

Success means: an integration stress test runs 16 or more concurrent workspace materializations
with simulated disk latency; every worker finishes successfully with a ready, isolated
workspace `.venv`; the existing shared-readiness / load-budget suite stays green.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **quality / CI engineer**, I want 16+ concurrent materializations proven under
  simulated disk latency, so that high-parallel Makefile runs do not rediscover the
  PYPOST-1413 timeout class without a regression signal.
- As a **Makefile test author**, I want the existing 4-worker load-budget behavior unchanged,
  so that ordinary readiness regressions remain fast and stable while extreme stress is
  covered separately.
- As a **test infrastructure maintainer**, I want the stress check to exercise the same
  shared-venv materialization path used by fixtures (`SharedVenvManager` / facade), so that
  the result reflects real harness contention rather than a toy mock.
- As a **platform engineer**, I want simulated latency (not live NFS) so the stress case is
  deterministic, offline, and runnable in CI without external storage dependencies.
- As a **tech-debt owner**, I want this ticket to close the extreme-concurrency follow-up
  already referenced from PYPOST-1421 without absorbing unrelated facade-retirement or
  readiness-deepening work.

## Definition of Done

This task is considered complete when:

1. An automated integration stress test runs **at least 16** concurrent workspace
   materializations against the shared-venv materialization path.
2. The stress scenario injects **simulated disk latency** on the population path (no live NFS
   required).
3. Every concurrent worker completes without materialization error and leaves a **ready**
   workspace `.venv`.
4. Workspace isolation still holds under stress (a mutation in one workspace does not appear
   in sibling workspaces or the shared template/base).
5. Contended completion stays within an explicit, documented wall-clock budget appropriate for
   the simulated latency and worker count.
6. The existing 4-worker load-budget test and the broader shared-readiness suite continue to
   pass (no intentional regression).
7. Repository quality gates applicable to this change (`make test` for touched suites,
   `make lint` / cleanup step, `make verify-ai-tasks` as required by the workflow) pass for
   the task’s scope.

## Task Description

### Problem Statement

Shared virtual environment materialization is fast for a few parallel workspaces, and a
4-worker load-budget test already guards the ordinary NFR. Extreme concurrency (16+ workers)
under slow disk was the original PYPOST-1413 failure mode and remains only partially covered.
Without a dedicated stress check, CI can still ship regressions that only appear when many
workspaces materialize together under latency.

### Scope

**In scope**

- Add an automated extreme-concurrency integration stress test (16+ workers) with simulated
  disk latency on the materialization population path.
- Assert success, readiness, isolation, and a documented completion budget.
- Keep the existing 4-worker load-budget and shared-readiness cases green.
- Update developer docs that describe shared-venv materialization / related tests so the
  stress case is discoverable.

**Out of scope**

- Redesigning skeleton vs base source selection or deep `.pth` readiness (PYPOST-1421).
- Retiring underscore facades / late-bind shims (e.g. PYPOST-1440).
- Requiring live NFS or production filesystem changes.
- Changing default `pytest` worker counts or Make `WORKER_TIMEOUT` globally.
- Broader product features unrelated to Makefile shared-venv harness stress.

### Constraints and Assumptions

- Implementation language is Python; tests use pytest with explicit timeouts.
- Simulated latency is injected via the existing population seam (`tree_copier` / equivalent),
  not by requiring slow external storage.
- The 4-worker load-budget test remains the ordinary NFR guard; extreme stress may use a
  longer per-test timeout and its own budget constants.
- Silent healthy-path logging stays quiet; stress validation is assertion-based.

## Main Entities (Business Perspective)

- **Shared base / skeleton template**: Source tree copied into each workspace `.venv`.
- **Workspace environment**: Per-worker `.venv` materialized for isolated Makefile tests.
- **Materialization**: Operation that populates a workspace from skeleton (preferred) or base.
- **Concurrent workers**: Parallel materialization requests (16+) that contend on shared
  source / process resources under latency.
- **Simulated disk latency**: Deterministic delay on the population path representing slow I/O.
- **Load-budget guard**: Existing 4-worker check that must remain green.

## Q&A

**Q: Why is this a business problem rather than “just another unit test”?**  
A: Extreme concurrency under latency was a real CI failure class (PYPOST-1413). Without a
regression signal at 16+ workers, the harness can silently reintroduce flaky, slow preparation
that blocks developer and pipeline velocity.

**Q: Why simulate latency instead of using NFS?**  
A: Offline, deterministic CI needs a controllable latency seam. Live NFS is environment-
specific and non-portable across developer machines and runners.

**Q: Does this replace the 4-worker load-budget test?**  
A: No. The 4-worker case stays the fast ordinary NFR guard. Extreme stress is additional
coverage for high contention limits.

**Q: Is a production API change required?**  
A: Only if the stress scenario exposes a real contention defect. The primary deliverable is
the stress verification; production changes are in scope only as needed to make that check
honestly green without weakening isolation or readiness guarantees.
