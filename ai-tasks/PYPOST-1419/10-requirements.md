# PYPOST-1419: Encapsulate Shared Virtual Environment Lifecycle

## Goals

PyPost's Makefile integration tests rely on a shared, pre-warmed virtual environment lifecycle
inside `tests/makefile_test_helpers.py`. That lifecycle covers base environment bootstrapping,
concurrency-safe locking, lightweight skeleton template generation, and per-workspace
materialization so suites can run quickly under parallel workers without recreating full
environments from scratch (see [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)).

Today those responsibilities are spread across free helper functions and a module-level mutable
cache for the resolved base environment path. That structure creates ongoing friction for the
test platform:

1. **Opaque ownership and state**: Lifecycle stages (bootstrap, lock, skeleton, materialize)
   are not owned by a single cohesive unit, so maintainers must mentally reconstruct the full
   flow when changing or debugging preparation failures.
2. **Hard-to-isolate verification**: Module-level mutable state and tightly coupled free
   functions make it difficult to exercise individual lifecycle stages in isolation, increasing
   the cost and risk of regressions when hardening preparation.
3. **Follow-up debt friction**: Later improvements identified in PYPOST-1413 (native
   materialization, deeper readiness checks, extreme concurrency stress) must touch the same
   scattered helpers; without clear boundaries, each follow-up risks reintroducing coupling or
   accidental behavior drift.

The business goal of this task is to encapsulate the shared virtual environment lifecycle into a
cohesive owner (`SharedVenvManager`) so that Makefile test workspace preparation remains
reliable, understandable, and safely evolvable. Success means: isolated verification of
lifecycle stages; clear ownership of shared-venv readiness state; and no module-level mutable
shared-base path cache as the source of truth—without changing the external contracts relied on
by existing fixtures and suites.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **test infrastructure maintainer**, I want the shared virtual environment lifecycle owned
  by one cohesive manager, so that bootstrap, locking, skeleton publication, and workspace
  materialization have a single clear place to read, change, and review.
- As a **Makefile test author**, I want existing workspace fixtures to keep provisioning
  pre-warmed environments with the same isolation and timing guarantees, so that my suites do
  not regress while the harness is reorganized.
- As a **quality / CI engineer**, I want preparation state free of module-level mutable path
  caches that can go stale across worker boundaries or reloads, so that parallel Makefile test
  runs remain deterministic and free of flaky preparation failures.
- As a **platform engineer**, I want lifecycle stages verifiable in isolation, so that
  readiness, locking, and materialization behaviors can be checked before larger follow-up
  changes land.
- As a **tech-debt owner**, I want this encapsulation to leave clear seams for later tickets
  (native materialization, deeper readiness validation, extreme concurrency stress) without
  forcing those changes into this task.

## Definition of Done

This task is considered complete when:

1. Shared base environment bootstrapping, concurrency locking, skeleton template generation, and
   workspace materialization are owned by a cohesive `SharedVenvManager` (or equivalently named
   manager) rather than a scatter of free functions plus a module-level mutable path cache.
2. Shared-venv readiness state (including the resolved shared base environment path) has clear
   ownership under that manager; a module-level mutable shared-base path cache must not be the
   source of truth.
3. Lifecycle stages can be verified in isolation without rewriting consumer fixtures.
4. Existing public fixture contracts used by Makefile suites (`make_workspace`,
   `make_workspace_full_deps`, and other helpers that materialize pre-warmed workspaces) continue
   to provision isolated workspaces with pre-warmed environments and must not regress existing
   shared-venv preparation timing/behavior validated by the PYPOST-1413 test suite
   (notably `tests/test_makefile_shared_readiness.py`, including
   `test_parallel_workspace_materialization_under_load_budget`).
5. Existing Makefile shared-readiness and materialization suites continue to pass with no
   intentional behavioral regressions in provisioning outcomes.
6. Repository quality gates (`make check`, `make lint`, `make typecheck`,
   `make verify-ai-tasks`) pass.

## Task Description

### Problem Statement

After PYPOST-1413, shared virtual environment preparation is functionally fast enough for
parallel Makefile suites, but the implementation remains procedural and stateful at module
scope. Responsibilities that form one lifecycle—discovering or creating the shared base,
serializing bootstrap with file locking, publishing the lightweight skeleton, and copying that
skeleton into each workspace—live as separate helpers around `_SHARED_BASE_VENV`.

That organization raises maintenance cost and defect risk: stale cached paths, unclear
publication boundaries, and limited ability to verify lifecycle stages in isolation.
Encapsulating the lifecycle into `SharedVenvManager` addresses that debt without changing what
Makefile tests expect from workspace fixtures.

### Scope

- **Lifecycle encapsulation**:
  - Group base environment bootstrapping, lock coordination, skeleton generation, readiness
    checks used by that lifecycle, and workspace materialization under one manager.
  - Replace module-level mutable shared-base path caching as the source of truth with
    clearly owned readiness state.
- **Isolated verification**:
  - Enable verification of individual lifecycle stages (success, failure, timeout, and
    lock-contention paths) without relying solely on full filesystem bootstrap or rewriting
    consumer fixtures.
- **Consumer continuity**:
  - Keep existing Makefile workspace fixtures and suites provisioning pre-warmed environments
    through the same outward contracts and behavioral guarantees established by PYPOST-1413.
- **Documentation alignment**:
  - Update developer-facing notes only as needed so descriptions of shared venv preparation
    match the encapsulated ownership model (no new product features).

### Out of Scope

- Changing production application code under `pypost/`.
- Replacing subprocess-based workspace copying with native in-process materialization
  ([PYPOST-1420](https://pypost.atlassian.net/browse/PYPOST-1420)).
- Deepening readiness validation of skeleton linkage contents
  ([PYPOST-1421](https://pypost.atlassian.net/browse/PYPOST-1421)).
- Adding extreme-concurrency / nightly stress suites beyond current coverage
  ([PYPOST-1422](https://pypost.atlassian.net/browse/PYPOST-1422)).
- Changing host OS, CI runner layout, or repository Makefile dependency policy.
- Expanding Windows / non-POSIX virtual environment layout support.

### Functional Requirements

- **FR1 (Cohesive Lifecycle Ownership)**:
  - Bootstrap of the shared base environment, concurrency-safe lock coordination, skeleton
    template publication, readiness checks used by that flow, and materialization into a test
    workspace must be owned by one cohesive manager (`SharedVenvManager` or equivalent).
- **FR2 (Clean State Management)**:
  - Shared-venv readiness state (including the resolved shared base environment path) must have
    clear ownership under the manager. A module-level mutable shared-base path cache must not be
    the source of truth.
  - After ownership moves, stale or invalid readiness must remain detectable and recoverable with
    the same semantics already established by PYPOST-1413. This task adds no new recovery
    behavior beyond encapsulating that existing readiness/recovery contract.
- **FR3 (Isolated Lifecycle Verification)**:
  - Individual lifecycle stages must be verifiable in isolation so readiness, locking, timeout,
    failure, and materialization paths can be exercised without rewriting consumer fixtures or
    depending solely on full filesystem bootstrap.
- **FR4 (Preserve Workspace Provisioning Behavior)**:
  - Workspace fixtures that today materialize a pre-warmed `.venv` must continue to do so with
    equivalent isolation: mutations in one workspace must not corrupt sibling workspaces or the
    shared base.
  - Concurrent workers requesting preparation must still serialize bootstrap safely and share a
    validated published base. Encapsulation must not regress existing shared-venv preparation
    timing/behavior validated by the PYPOST-1413 test suite (notably
    `tests/test_makefile_shared_readiness.py`, including
    `test_parallel_workspace_materialization_under_load_budget`).
- **FR5 (Preserve Failure Diagnostics)**:
  - Preparation and materialization failures must continue to raise contextual errors that
    identify the failing stage or operation and retain diagnostic detail sufficient for CI
    triage.
- **FR6 (Consumer Compatibility)**:
  - Existing Makefile test modules that import workspace fixtures or shared-preparation helpers
    from `tests.makefile_test_helpers` must keep working without requiring suite-wide rewrites
    of scenario assertions unrelated to this encapsulation. Outward contracts for Makefile/test
    helpers must remain stable.

### Non-Functional Requirements

- **NFR1 (No Intentional Behavior Regression)**:
  - Encapsulation must not intentionally change materialization success criteria, isolation
    guarantees, or shared-venv preparation timing/behavior validated by the PYPOST-1413 test
    suite.
- **NFR2 (Maintainability)**:
  - Lifecycle ownership and readiness-state ownership must be obvious to a maintainer reading
    the helpers module without reconstructing the flow across many free functions or a
    module-level mutable shared-base path cache.
- **NFR3 (Testability)**:
  - Core lifecycle behaviors must be verifiable through automated tests, including isolated
    checks of individual lifecycle stages.
- **NFR4 (Quality Gate Compliance)**:
  - Changes must satisfy repository Python standards (lint, types, AI-task artifact checks) via
    `make` targets.

### Constraints and Assumptions

- Work remains confined to test harness code under `tests/` (primarily
  `tests/makefile_test_helpers.py` and related tests/docs).
- Shared preparation continues to assume a POSIX-oriented virtual environment layout, matching
  current CI and developer Linux environments.
- Sibling debt tickets PYPOST-1420, PYPOST-1421, and PYPOST-1422 remain separate; this task must
  not absorb their scope.
- Discovered during PYPOST-1413 Step 7 technical debt analysis; behavior introduced there is the
  baseline to preserve.

### Main Business Entities

- **Shared Base Environment**: Once-per-host pre-warmed environment used as the source of truth
  for test tooling packages. Attributes: location, readiness marker, installed tooling set,
  publication status.
- **Preparation Lock**: Coordination token preventing concurrent workers from bootstrapping the
  same base twice. Attributes: lock identity, acquisition state, wait within budget.
- **Skeleton Template**: Lightweight published template used to populate workspace environments
  quickly. Attributes: template location, readiness, linkage to shared base packages.
- **Workspace Environment**: Per-test isolated `.venv` materialized for Makefile suite
  execution. Attributes: workspace path, readiness, isolation boundary from siblings.
- **Shared Venv Manager**: Cohesive owner of bootstrap, locking, skeleton publication,
  readiness state, and materialization. Attributes: owned readiness state, lifecycle
  operations.
- **Makefile Workspace Fixture**: Test entry point that prepares an isolated project tree and
  pre-warmed environment. Attributes: fixture name, consumer suites, provisioning outcome.

### User Scenarios

#### Scenario 1: Parallel Makefile Suite Startup
Multiple parallel workers request workspace fixtures at once. Exactly one worker performs shared
base bootstrap under the preparation lock; others wait within the existing PYPOST-1413
preparation timing expectations and then materialize from the published skeleton. All workspaces
become ready without module-level stale path confusion.

#### Scenario 2: Maintainer Adjusts Lifecycle Behavior
A maintainer needs to change how skeleton publication or materialization is verified. They open
the shared venv manager, locate the relevant lifecycle responsibility, and adjust it without
hunting across unrelated free helpers or a module-level global cache.

#### Scenario 3: Isolated Lifecycle Verification
A platform engineer writes automated checks for lock contention, bootstrap failure diagnostics,
or materialization cleanup. They exercise individual lifecycle stages in isolation and keep full
Makefile suites focused on Make-target behavior.

#### Scenario 4: Existing Suites Keep Passing
After encapsulation, existing Makefile shared-readiness and materialization suites run unchanged
in intent: workspaces remain isolated, shared-venv preparation timing/behavior validated by the
PYPOST-1413 test suite is preserved, and failure messages remain actionable.

## Q&A

**Q: Why encapsulate if PYPOST-1413 already made materialization fast enough?**  
A: PYPOST-1413 fixed the performance and timeout problem. This ticket addresses the resulting
maintainability debt: scattered helpers and module-level mutable state that make the lifecycle
harder to reason about, harder to verify in isolation, and riskier to evolve.

**Q: Why is module-level mutable shared-base caching a business risk?**  
A: Cached paths can become stale across worker boundaries or reloads even when the on-disk
environment is invalid or incomplete. That produces intermittent preparation failures that look
like product regressions and erode trust in quality gates. The source of truth for readiness
must be clearly owned, not a module-level mutable shared-base path cache.

**Q: Why require isolated verification of lifecycle stages?**  
A: The business need is to verify readiness, locking, timeout, failure, and materialization
paths without rewriting every consumer fixture or depending solely on full filesystem
bootstrap. How that isolation is achieved is an architecture concern; the requirement is the
verification outcome.

**Q: Does this change production runtime behavior?**  
A: No. Scope is test harness encapsulation under `tests/`. Application code in `pypost/` is out
of scope.

**Q: How does this relate to PYPOST-1420 / 1421 / 1422?**  
A: Those tickets deepen materialization mechanics, readiness validation, and concurrency stress.
This ticket only consolidates ownership and state so those follow-ups have a clear seam.

**Q: Must fixture import paths used by Makefile suites change?**  
A: No. Outward contracts for Makefile/test helpers must remain stable; consumer suites should
keep working through existing helper/fixture entry points without suite-wide rewrites.

**Q: What does “preparation budget / timing” mean for this ticket?**  
A: This ticket must not regress existing shared-venv preparation timing/behavior validated by
the PYPOST-1413 test suite—especially
`tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`
and related readiness/recovery checks. No new timing semantics are introduced here.
