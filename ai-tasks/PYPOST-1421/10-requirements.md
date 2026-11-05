# PYPOST-1421: Deep Template Validation in Shared Venv Readiness

## Goals

Makefile integration tests rely on a published lightweight skeleton template so each workspace
can materialize a pre-warmed `.venv` quickly. After
[PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413), that template injects shared
dependencies through a `_prewarmed_base.pth` redirect. After
[PYPOST-1419](https://pypost.atlassian.net/browse/PYPOST-1419), readiness lives on
`SharedVenvManager.is_ready` (with `_venv_ready` as a thin facade).

Today readiness only checks an initialization marker and `bin/python`. A skeleton that still
has those two artifacts but whose `_prewarmed_base.pth` is missing, unreadable, or points at a
non-directory / unreachable path is still treated as ready. Callers then copy that damaged
template into workspaces, and the harness silently loses the fast skeleton path—falling back
to slow full-base materialization or leaving workspaces that look ready while imports fail.

The business goal of this task is to make readiness refuse damaged skeleton templates so the
shared-venv lifecycle rebuilds or selects a healthy source instead of silently accepting a
broken `.pth` and paying the slow materialization / broken-workspace cost discovered during
PYPOST-1413.

Success means: a template is ready only when marker, interpreter, and a valid readable
`_prewarmed_base.pth` target (when the template is expected to carry that file) all check out;
full shared bases that do not use the redirect remain ready; existing shared-readiness and
manager suites stay green; ownership stays on `SharedVenvManager.is_ready` without expanding
sibling debt tickets.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **quality / CI engineer**, I want damaged skeleton templates rejected by readiness, so
  that parallel Makefile suites do not silently fall back to slow full-base materialization or
  run against workspaces that look ready but cannot import shared deps.
- As a **Makefile test author**, I want workspace fixtures to keep receiving a ready, usable
  pre-warmed `.venv` when the shared template is healthy, so that suites do not regress while
  readiness becomes stricter.
- As a **test infrastructure maintainer**, I want deep `.pth` validation owned by
  `SharedVenvManager.is_ready` (and therefore by `_venv_ready`), so that every consumer of the
  readiness seam sees the same guarantee without duplicating checks.
- As a **platform engineer**, I want missing, corrupt, or unreachable `_prewarmed_base.pth`
  targets to fail readiness and trigger the existing rebuild / source-selection paths, so that
  recovery stays automatic and observable through current failure diagnostics.
- As a **tech-debt owner**, I want this ticket to close the deep template validation called out
  in PYPOST-1413 / PYPOST-1419 / PYPOST-1420 without absorbing extreme-concurrency stress or
  facade retirement work tracked elsewhere.

## Definition of Done

This task is considered complete when:

1. Readiness owned by `SharedVenvManager.is_ready` (facade `_venv_ready`) treats a skeleton
   template as not ready when `_prewarmed_base.pth` is missing.
2. Readiness treats a template as not ready when `_prewarmed_base.pth` exists but is unreadable,
   empty/invalid, or points at a path that is not a readable directory.
3. A healthy skeleton with marker, interpreter, and a `_prewarmed_base.pth` that points at a
   valid readable directory remains ready.
4. A full shared base `.venv` that is complete (marker + interpreter) and does not rely on
   `_prewarmed_base.pth` remains ready so bootstrap and base fallback keep working.
5. When a published skeleton fails deep validation, `ensure_ready` rebuilds it (existing
   `not is_ready(skeleton)` path) rather than leaving a damaged template in place.
6. Materialization source selection continues to prefer a ready skeleton and falls back to the
   shared base only when the skeleton is not ready—including deep `.pth` failure.
7. Existing Makefile shared-readiness and manager suites—especially
   `tests/test_shared_venv_manager.py` and `tests/test_makefile_shared_readiness.py`—continue
   to pass with no intentional regression of isolation or preparation timing/behavior.
8. Repository quality gates applicable to this change (`make test` for touched suites,
   `make lint` / cleanup step, `make verify-ai-tasks` as required by the workflow) pass for
   the task’s scope.

## Task Description

### Problem Statement

Shared virtual environment preparation is fast when the published `.skeleton` carries a valid
`_prewarmed_base.pth` into each workspace. Readiness still only verifies marker + interpreter.
A damaged template therefore looks ready, gets copied, and the suite either hits slow full-base
materialization after the fact or proceeds with a workspace that cannot resolve shared packages.
That gap was filed as follow-up debt from PYPOST-1413 and left open through the
`SharedVenvManager` ownership move (PYPOST-1419) and in-process materialization (PYPOST-1420).

### Scope

**In scope**

- Deepen readiness validation for `_prewarmed_base.pth` on the owned readiness API
  (`SharedVenvManager.is_ready` / `_venv_ready`).
- Cover missing, unreadable, invalid, and unreachable `.pth` target cases with automated tests.
- Keep facade contracts stable; no suite-wide consumer rewrites beyond fixture seeding needed
  for the stricter check.
- Update developer docs that describe readiness so they match the deeper guarantee.

**Out of scope**

- Changing in-process vs subprocess population mechanics (PYPOST-1420).
- Extreme concurrency / NFS stress beyond existing load-budget coverage (PYPOST-1422).
- Retiring underscore facades / late-bind shims (tracked elsewhere, e.g. PYPOST-1440).
- Redesigning materialization source-selection policy beyond reacting to deeper readiness.
- Emitting a distinct “template damaged” user-facing product error (fail-closed readiness +
  existing rebuild/fallback is sufficient for this ticket).

### Constraints and Assumptions

- Implementation language is Python; tests use pytest with explicit timeouts.
- Skeleton templates published by `build_skeleton` always write `_prewarmed_base.pth`; full
  shared bases typically do not.
- `_venv_ready` remains a thin delegate to `SharedVenvManager.is_ready`.
- Silent healthy-path logging stays quiet; failure continues to surface through existing
  stage-aware `RuntimeError` paths where applicable.

## Main Entities (Business Perspective)

- **Shared base environment**: Fully populated shared `.venv` used as the package source and
  fallback materialization source.
- **Skeleton template**: Lightweight published `.skeleton` that must carry a valid
  `_prewarmed_base.pth` redirect into the shared base site-packages.
- **Readiness check**: Gate that decides whether a venv/template may be reused, rebuilt, or
  selected as a materialization source.
- **Workspace environment**: Per-test `.venv` materialized from skeleton (preferred) or base
  (fallback).
- **Facade consumers**: Makefile fixtures and helpers that call `_venv_ready` /
  `_get_shared_base_venv` / materialize without owning validation logic.

## Q&A

**Q: Why is this a business problem rather than a pure refactor?**  
A: Damaged templates cause silent loss of the fast preparation path and flaky or slow Makefile
suites—the same class of CI/developer-velocity pain that motivated PYPOST-1413.

**Q: Why deepen `is_ready` instead of only changing materialize?**  
A: After PYPOST-1419 every consumer (ensure_ready rebuild, materialize source selection,
workspace reuse, `_venv_ready`) shares one readiness owner; fixing only materialize would leave
ensure_ready accepting damaged skeletons.

**Q: Must a full shared base carry `_prewarmed_base.pth`?**  
A: No. Bases install packages directly. The existence requirement applies to skeleton templates
that are expected to publish the redirect file; whenever the file is present it must point at a
valid readable directory.

**Q: Is a distinct “template damaged” error required?**  
A: No for this ticket. Fail-closed readiness should drive rebuild (`ensure_ready`) or base
fallback (`materialize`) using existing diagnostics. A louder dedicated signal can be follow-up
debt if needed.
