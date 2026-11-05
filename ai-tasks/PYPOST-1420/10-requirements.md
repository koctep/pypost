# PYPOST-1420: Native In-Process Workspace Materialization

## Goals

Makefile integration tests prepare isolated workspaces by materializing a per-workspace
pre-warmed virtual environment from a published shared skeleton (or shared base fallback).
After [PYPOST-1419](https://pypost.atlassian.net/browse/PYPOST-1419), that materialization is
owned by `SharedVenvManager`, but the population step still incurs residual process spawn
overhead for every workspace. That cost was identified during
[PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413) Step 7 technical debt analysis and
remains visible under parallel worker load.

The business goal of this task is to make workspace environment materialization complete
**in-process**—without spawning an external OS process for the filesystem population step—so
parallel Makefile suites pay less preparation overhead while keeping the same isolation,
readiness, and failure-diagnostic outcomes consumers already rely on.

Success means: each workspace still receives a ready, isolated pre-warmed `.venv`; materialization
no longer depends on fork/exec of an external copy utility; existing shared-readiness and
materialization timing/behavior validated by the PYPOST-1413 suite are preserved or improved;
and ownership remains under `SharedVenvManager` without expanding sibling debt tickets.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **quality / CI engineer**, I want workspace materialization free of per-workspace
  external process spawn overhead, so that parallel Makefile suites spend less wall time in
  preparation and are less sensitive to process-creation contention under load.
- As a **Makefile test author**, I want each workspace fixture to keep receiving an isolated,
  ready pre-warmed `.venv` with the same provisioning guarantees, so that my suites do not
  regress while materialization becomes in-process.
- As a **test infrastructure maintainer**, I want materialization outcomes (success, failure
  cleanup, diagnostics) owned by `SharedVenvManager` without changing fixture contracts, so that
  consumers and follow-up debt tickets keep a stable seam.
- As a **platform engineer**, I want materialization behavior verifiable against readiness,
  isolation, and failure paths already covered by shared-readiness suites, so that removing
  external-process overhead does not silently weaken guarantees.
- As a **tech-debt owner**, I want this ticket to close the residual materialization overhead
  called out in PYPOST-1413 / PYPOST-1419 without absorbing deeper readiness validation or
  extreme-concurrency stress work tracked elsewhere.

## Definition of Done

This task is considered complete when:

1. Workspace environment materialization owned by `SharedVenvManager` completes the filesystem
   population step **in-process**, without spawning an external OS process for that step.
2. Materialized workspace `.venv` environments remain isolated: mutations in one workspace must
   not corrupt sibling workspaces or the shared base / skeleton source.
3. Readiness semantics for a materialized workspace environment remain equivalent to the
   baseline established by PYPOST-1413 / PYPOST-1419 (a ready target is reused; incomplete or
   failed targets are cleaned up rather than left half-ready).
4. Materialization failures continue to raise contextual errors that identify the failing
   operation and retain diagnostic detail sufficient for CI triage, and leave no usable
   half-ready workspace `.venv`.
5. Existing Makefile shared-readiness and materialization suites—especially
   `tests/test_makefile_shared_readiness.py`, including
   `test_parallel_workspace_materialization_under_load_budget`—continue to pass with no
   intentional regression of isolation or shared-venv preparation timing/behavior (timing may
   improve).
6. Public fixture / facade contracts used by Makefile suites
   (`make_workspace`, `make_workspace_full_deps`, and helpers that materialize pre-warmed
   workspaces) remain stable; no suite-wide consumer rewrites are required.
7. Repository quality gates (`make check`, `make lint`, `make typecheck`,
   `make verify-ai-tasks`) pass.

## Task Description

### Problem Statement

Shared virtual environment preparation is already fast enough for parallel Makefile suites after
PYPOST-1413, and lifecycle ownership is cohesive after PYPOST-1419. Residual debt remains in the
materialization step: populating each workspace `.venv` still depends on spawning an external
OS process. Under parallel workers that cost accumulates as fork/exec overhead and process-
creation contention, even though the on-disk result (an isolated ready environment derived from
the published skeleton or shared base) is already correct.

This ticket removes that residual overhead by requiring in-process materialization outcomes,
without changing what Makefile tests expect from workspace fixtures and without locking a
specific filesystem technique into the requirements.

### Scope

- **In-process materialization outcome**:
  - Ensure `SharedVenvManager` workspace materialization populates the target environment
    without spawning an external OS process for the filesystem population step.
- **Preserve provisioning guarantees**:
  - Keep isolation between workspaces, readiness reuse/cleanup semantics, failure diagnostics,
    and shared-readiness timing/behavior validated by the PYPOST-1413 suite (timing may improve).
- **Consumer continuity**:
  - Keep existing Makefile workspace fixtures and facades provisioning pre-warmed environments
    through the same outward contracts.
- **Documentation alignment**:
  - Update developer-facing notes only as needed so descriptions of materialization match the
    in-process outcome (no new product features).

### Out of Scope

- Changing production application code under `pypost/`.
- Re-encapsulating or redesigning `SharedVenvManager` ownership (already done in PYPOST-1419).
- Deepening readiness validation of skeleton linkage contents
  ([PYPOST-1421](https://pypost.atlassian.net/browse/PYPOST-1421)).
- Adding extreme-concurrency / nightly stress suites beyond current coverage
  ([PYPOST-1422](https://pypost.atlassian.net/browse/PYPOST-1422)).
- Changing host OS, CI runner layout, or repository Makefile dependency policy.
- Expanding Windows / non-POSIX virtual environment layout support.
- Changing how shared base bootstrap, preparation locking, or skeleton publication work,
  except as needed to keep materialization consumers working.

### Functional Requirements

- **FR1 (In-Process Materialization)**:
  - Workspace `.venv` materialization owned by `SharedVenvManager` must complete the filesystem
    population step in-process. Spawning an external OS process solely to populate the target
    environment is not allowed.
- **FR2 (Preserve Isolation)**:
  - A materialized workspace environment must remain isolated from sibling workspaces and from
    the shared base / skeleton source. Mutations under one workspace must not corrupt others.
- **FR3 (Preserve Readiness Semantics)**:
  - If the workspace target is already ready, materialization must reuse it without unnecessary
    rework.
  - If the target exists but is not ready, materialization must replace it rather than leave a
    half-ready environment.
  - On materialization failure, any partial target must be cleaned up so consumers do not observe
    a usable half-ready `.venv`.
- **FR4 (Preserve Source Selection Outcome)**:
  - Materialization must continue to prefer the published skeleton when it is ready, and fall
    back to the shared base when the skeleton is not ready, matching current provisioning
    outcomes.
- **FR5 (Preserve Failure Diagnostics)**:
  - Materialization failures must continue to raise contextual errors that identify the failing
    operation and retain diagnostic detail sufficient for CI triage.
- **FR6 (Consumer Compatibility)**:
  - Existing Makefile test modules that import workspace fixtures or shared-preparation helpers
    must keep working without suite-wide rewrites. Outward contracts for Makefile/test helpers
    must remain stable.
- **FR7 (Preserve Parallel Preparation Guarantees)**:
  - Concurrent workers requesting workspace preparation must continue to receive ready isolated
    environments without regressing shared-venv preparation timing/behavior validated by the
    PYPOST-1413 test suite (notably
    `tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`).

### Non-Functional Requirements

- **NFR1 (Overhead Reduction)**:
  - Materialization must eliminate residual per-workspace external process spawn overhead for
    the filesystem population step. Shared-venv preparation timing/behavior validated by the
    PYPOST-1413 suite must not regress; wall-clock materialization cost may improve.
- **NFR2 (No Intentional Behavior Regression)**:
  - Success criteria for readiness, isolation, source selection (skeleton vs base), and failure
    cleanup must remain equivalent to the PYPOST-1413 / PYPOST-1419 baseline aside from the
    in-process population mechanism.
- **NFR3 (Maintainability)**:
  - Materialization remains owned by `SharedVenvManager`; maintainers must not need a separate
    external-process path to understand ordinary workspace provisioning.
- **NFR4 (Testability)**:
  - Materialization success, failure cleanup, isolation, and readiness reuse must remain
    verifiable through automated tests (existing shared-readiness suites and/or focused manager
    tests).
- **NFR5 (Quality Gate Compliance)**:
  - Changes must satisfy repository Python standards (lint, types, AI-task artifact checks) via
    `make` targets.

### Constraints and Assumptions

- Work remains confined to test harness code under `tests/` (primarily
  `SharedVenvManager` materialization and related tests/docs), plus developer docs that describe
  materialization.
- Shared preparation continues to assume a POSIX-oriented virtual environment layout, matching
  current CI and developer Linux environments.
- Sibling debt tickets PYPOST-1421 and PYPOST-1422 remain separate; this task must not absorb
  their scope.
- Discovered during PYPOST-1413 Step 7; ownership moved to `SharedVenvManager` in PYPOST-1419.
  Behavior introduced there is the baseline to preserve, except for removing external-process
  population overhead.
- Requirements specify **outcomes** (in-process population, isolation, readiness, diagnostics).
  They do not prescribe a particular filesystem technique, library, or layout strategy; those
  choices belong to architecture and development.

### Main Business Entities

- **Shared Base Environment**: Once-per-host pre-warmed environment used as the source of truth
  for test tooling packages. Attributes: location, readiness, publication status.
- **Skeleton Template**: Lightweight published template used to populate workspace environments
  quickly. Attributes: template location, readiness, linkage to shared base packages.
- **Workspace Environment**: Per-test isolated `.venv` materialized for Makefile suite
  execution. Attributes: workspace path, readiness, isolation boundary from siblings.
- **Shared Venv Manager**: Cohesive owner of bootstrap, locking, skeleton publication,
  readiness state, and materialization. Attributes: owned readiness state, materialize
  operation.
- **Materialization Outcome**: Result of populating a workspace environment from skeleton or
  base. Attributes: success/failure, cleanup of partial targets, diagnostic context, absence of
  external process spawn for population.
- **Makefile Workspace Fixture**: Test entry point that prepares an isolated project tree and
  pre-warmed environment. Attributes: fixture name, consumer suites, provisioning outcome.

### User Scenarios

#### Scenario 1: Parallel Workspace Materialization Under Load
Multiple parallel workers request workspace fixtures at once. Each worker receives a ready
isolated `.venv` without paying per-workspace external process spawn overhead for filesystem
population. Shared-readiness timing/behavior validated by the PYPOST-1413 suite continues to
hold (and may improve).

#### Scenario 2: Ready Workspace Is Reused
A fixture requests materialization for a workspace whose `.venv` is already ready. The manager
reuses it without unnecessary rework, matching existing readiness semantics.

#### Scenario 3: Failed Materialization Leaves No Half-Ready Environment
Materialization fails partway through. The harness raises a contextual error suitable for CI
triage and removes any partial target so subsequent attempts or sibling workers do not observe a
usable half-ready `.venv`.

#### Scenario 4: Skeleton Preferenced Over Base
When the published skeleton is ready, workspaces are populated from it. When the skeleton is not
ready, materialization falls back to the shared base. Consumer-visible provisioning outcomes
remain unchanged aside from in-process population.

#### Scenario 5: Existing Suites Keep Passing
After the change, existing Makefile shared-readiness and materialization suites run unchanged in
intent: workspaces remain isolated, preparation timing/behavior does not regress, fixture
contracts stay stable, and failure messages remain actionable.

## Q&A

**Q: Why change materialization if PYPOST-1413 already made it fast enough?**  
A: PYPOST-1413 fixed the catastrophic timeout problem with the skeleton pattern. Residual
per-workspace external process spawn overhead remains under parallel load and was explicitly
ticketed as follow-up debt. This ticket removes that residual cost.

**Q: Why is “in-process” a business requirement rather than an implementation detail?**  
A: The business need is to eliminate fork/exec overhead and process-creation contention during
workspace population. “In-process” names that outcome constraint. How the filesystem is
populated (specific APIs or layout tactics) is intentionally left to architecture.

**Q: Does this change production runtime behavior?**  
A: No. Scope is test harness materialization under `tests/` (and related developer docs).
Application code in `pypost/` is out of scope.

**Q: How does this relate to PYPOST-1419?**  
A: PYPOST-1419 moved materialization ownership to `SharedVenvManager` but retained
external-process population. This ticket changes only the materialization population outcome
on that owner.

**Q: How does this relate to PYPOST-1421 / PYPOST-1422?**  
A: PYPOST-1421 deepens readiness validation of skeleton linkage; PYPOST-1422 adds extreme
concurrency stress. Neither is required to close the in-process materialization debt.

**Q: Must fixture import paths or facade names change?**  
A: No. Outward contracts for Makefile/test helpers must remain stable.

**Q: What does “preparation timing/behavior” mean for this ticket?**  
A: Existing shared-venv preparation timing/behavior validated by the PYPOST-1413 test suite—
especially
`tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`
—must not regress. Removing external-process overhead may improve wall-clock cost; no new
stricter timing semantics are introduced here beyond that non-regression bar.

**Q: Are specific filesystem techniques required?**  
A: No. Requirements forbid external-process population and require equivalent isolation,
readiness, and diagnostics. Concrete techniques are architecture/development decisions.
