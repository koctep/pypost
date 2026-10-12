# PYPOST-1359: Development dependency lock fails Make verification with CI-pinned uv at base commit

## Goals

Ensure development environments and CI quality gates have consistent, reproducible, and verifiable dependency resolution. A contributor or CI runner verifying development dependency locks must experience deterministic results matching repository specifications, preventing spurious quality-gate failures and ensuring that committed dependency locks faithfully reflect their declared direct requirements.

## User Stories

- As a contributor or developer, I want `make check-lock-dev` to reliably verify that development dependencies match direct requirements, so I can trust that my local development and test environment matches project specifications.
- As a release engineer / CI maintainer, I want CI quality gates verifying dependency locks to execute deterministically without spurious drift or false-positive failures, so that dependency integrity is guaranteed across builds.
- As a project maintainer, I want lockfile verification and generation to maintain strict reproducible constraints without speculative or unreviewed transitive dependency upgrades, so project stability is preserved.

## Definition of Done

1. A clear reproduction under the repository's Make workflows verifies the red state of `make check-lock-dev` using the project-pinned `uv` toolchain.
2. It is determined whether the committed development lock file, the lock generation inputs, or the verification mechanism is stale or inconsistent.
3. A narrow, reviewed correction is applied that resolves the drift without introducing speculative dependency upgrades.
4. Resolver requirements, tool pinning expectations, and development dependency constraints are clearly documented.
5. All relevant repository quality gates pass cleanly via Make (`make check-lock-dev`, `make check`, or appropriate quality targets) using the pinned toolchain.

## Task Description

During packaging implementation in PYPOST-1348, a pre-existing quality gate failure was discovered where `make check-lock-dev` fails against the committed `requirements-dev.txt` using the CI-pinned `uv` compiler version (`0.11.31` as pinned in `.github/workflows/test.yml`).

The task requires diagnosing the compiler, source, and lockfile drift, establishing a clean Make-driven reproduction, and implementing a minimal, reviewed fix that restores quality gate verification without speculative dependency upgrades.

### Implementation Language

Python (alongside Make workflows and dependency definition files).

### Scope

- Diagnose compiler, input specification, and lockfile differences causing `make check-lock-dev` failure.
- Ensure `make check-lock-dev` reproduces the failure state cleanly under pinned tooling before fixing.
- Apply a narrow, reviewed correction to lock artifacts or verification rules.
- Document resolver behavior and tool expectations in development documentation.
- Verify resolution through repository Make targets.

### Constraints and Assumptions

- Make-Only Tooling: All commands and quality gates must run through `make` targets; no direct CLI tool invocations (`uv`, `pytest`, `pip`) outside Make.
- Minimal / Narrow Correction: Strictly avoid speculative transitive or direct dependency upgrades beyond what is required to resolve lock consistency.
- Pin Consistency: Alignment with CI-pinned tooling (specifically `uv` version pinned in CI workflows) must be respected.
- Top-Down Workflow: Strict adherence to Top-Down sequential stages without premature technical or architectural lock-in at requirements stage.

### Main Entities

| Entity | Business attributes and relationship |
| --- | --- |
| Direct Development Requirements (`requirements-dev.in`) | Direct declared dependencies and version constraints for development and testing tools |
| Development Lock File (`requirements-dev.txt`) | Fully resolved, pinned transitive dependency graph matching direct requirements |
| Verification Quality Gate (`make check-lock-dev`) | Integrity check comparing freshly compiled locks against committed locks |
| Pinned Toolchain (`uv`) | Deterministic packaging tool version defined in CI workflows and repository guidelines |

### User Scenarios

1. A developer checks out the repository and executes the quality gate `make check-lock-dev` with the required toolchain; the check passes cleanly with no unexplained file drift.
2. A developer modifies direct development dependencies in `requirements-dev.in` and runs `make lock-dev`; the regenerated lock reflects exactly the required changes, and subsequent `make check-lock-dev` succeeds.
3. CI runs pull request checks against dependency lockfiles; the verification accurately confirms parity between declared inputs and locked outputs without false-positive failures.

## Q&A

- **Why is this task needed from a business perspective?**
  Spurious failures in dependency lock verification block pull request workflows, disrupt developer productivity, and undermine confidence in reproducible builds and test environments.
- **Why can't we simply upgrade all development packages to their latest versions?**
  Speculative upgrades introduce untested transitive changes and potential regressions. The project mandates narrow, reviewed corrections that diagnose and resolve the specific drift.
- **Does this require changing runtime application dependencies?**
  No. This issue specifically targets development dependency lock verification (`requirements-dev.in` and `requirements-dev.txt`), leaving runtime dependency specifications untouched.
