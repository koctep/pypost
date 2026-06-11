# PYPOST-465: Provision full test dependencies and run complete regression for PYPOST-446

## Goals

PYPOST-446 (history masking for hidden environment variables) was implemented and partially
validated, but a full project regression could not be completed because the execution environment
lacked required test dependencies. That gap leaves merge quality uncertain: unrelated areas of the
product may have regressed without detection.

This task closes that validation debt. The business objective is **confidence in merge quality**
for PYPOST-446 and a **reproducible test environment** so maintainers, contributors, and CI can
run the complete automated test suite without ad-hoc dependency fixes.

## Programming Language

Python 3.10+ (project test toolchain: Makefile, dependency declarations, CI workflow).

## User Stories

- As a **maintainer**, I want the standard local test workflow to include all dependencies
  needed for the full suite so I can validate changes before merge without manual setup.
- As a **contributor**, I want the documented install and test path to work on a clean checkout
  so I get the same regression signal as CI.
- As a **reviewer**, I want evidence that the complete project test suite passed after PYPOST-446
  so I can approve merge with confidence that masking work did not break other behavior.
- As a **release steward**, I want CI to run the full regression reliably so every push and pull
  request receives consistent quality feedback.

## Definition of Done

1. The complete automated project test suite can be executed using the project's standard local
   workflow without missing-dependency failures.
2. CI runs the full regression using the same dependency set, producing a clear pass or fail
   outcome on push and pull request.
3. A full regression run has been executed and recorded as successful, closing the outstanding
   validation gap from [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md).
4. Contributors can discover how to obtain a reproducible test environment through existing
   developer documentation or project conventions (no one-off setup steps required).
5. **No product behavior change** — deliverable is environment provisioning and regression
   validation only; history masking rules remain as implemented in PYPOST-446.

## Task Description

### Problem Statement

During PYPOST-446 implementation, runtime dependency provisioning for tests was incomplete in the
working environment. Unit and targeted tests were added, but end-to-end validation of the **entire**
project test suite did not occur. That leaves an open quality risk for merge: failures in unrelated
modules, integration paths, or UI tests may go undetected.

### Business Objective

Restore trust in the quality gate before PYPOST-446 merge by ensuring every required test
dependency is available and the full regression suite passes in both local and CI contexts.

### In Scope

- Provisioning all dependencies required to execute the complete automated test suite locally and
  in CI.
- Running and confirming success of full project regression tied to PYPOST-446 readiness.
- Aligning local and CI environments so they produce equivalent regression coverage.

### Out of Scope

- New product features or changes to history masking behavior (PYPOST-446 scope).
- History persistence/reload or History panel integration tests ([PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462)).
- Refactoring `RequestService` history-recording logic ([PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463)).
- Adding masking metric scrape tests ([PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464) — done).

## Functional Requirements

- The project must provide a reproducible path to install everything needed to run the full
  automated test suite on a clean checkout.
- Local and CI environments must both support executing the complete regression without
  dependency-related errors.
- A successful full regression run must be demonstrable before this task is closed.
- Existing test selection semantics (fast vs slow jobs, coverage thresholds) must remain
  aligned with project policy unless a documented gap is intentionally closed.

## Non-Functional Requirements

- **Reproducibility:** A new contributor following project documentation should reach the same
  test-ready state without undocumented manual steps.
- **Reliability:** CI regression results must be deterministic enough for reviewers to trust pass
  signals on pull requests.
- **Maintainability:** Dependency provisioning must stay aligned with how the project already
  declares and installs packages.
- **Traceability:** The work must be linkable to the PYPOST-446 debt item and Jira
  [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465).

## Constraints and Assumptions

- This is a follow-up **debt** task from PYPOST-446; priority is merge-confidence validation, not
  new functionality.
- The debt analysis identified missing test-runtime dependencies as the blocker; resolving that
  gap is the prerequisite for regression execution.
- Standard project conventions (`make install`, `make test`, documented CI workflow) are the
  expected entry points for validation.
- Python 3.10+ matrix behavior defined by the project applies; this task does not redefine
  supported Python versions.

## Main Entities and Interactions (Business View)

- **Contributor** — clones the repo, installs dependencies, runs tests locally.
- **Maintainer** — ensures quality gates pass before merging PYPOST-446-related work.
- **Reviewer** — relies on CI and documented local workflows to assess regression risk.
- **CI pipeline** — executes automated regression on every change.
- **Test suite** — the project's collective automated checks guarding product quality.
- **PYPOST-446 work** — history masking feature whose merge readiness depends on full regression.

Interactions:

1. PYPOST-446 implementation introduced changes that require whole-project validation.
2. Missing dependencies blocked full-suite execution during initial delivery.
3. This task restores the ability to run the full suite locally and in CI.
4. A passing full regression provides evidence that PYPOST-446 is safe to merge.

## Q&A

- **Why is this task needed if PYPOST-446 already has unit tests?**
  Targeted tests validate masking behavior but do not prove the wider product still passes all
  automated checks. Full regression closes that assurance gap.
- **What is the business objective?**
  Confidence in merge quality and a reproducible test environment for the whole project, not
  changes to masking rules.
- **Is this a feature task?**
  No. It is infrastructure and validation debt from PYPOST-446.
- **What defines success beyond "tests pass once"?**
  Both local standard workflow and CI must support repeatable full regression without
  dependency gaps.
- **Source of this task?**
  Follow-up from [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md) and
  Jira [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465).
