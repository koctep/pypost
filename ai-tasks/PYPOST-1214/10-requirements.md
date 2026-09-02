# PYPOST-1214: Mitigate large-batch GUI segfault and document CI ownership

## Goals

Prevent the native Qt style-engine crash observed when GUI tests accumulate in one
long-lived process, while keeping CI results reproducible and making the policy visible
to maintainers.

## User Stories

- As a CI maintainer, I want GUI tests to run in bounded isolated processes so a native
  crash in one batch cannot corrupt later batches.
- As a developer, I want a documented command and threshold for validating the mitigation.
- As a project owner, I want explicit ownership and tradeoffs for the test-infrastructure
  policy.

## Definition of Done

- A mitigation path is evaluated and enforced through the repository workflow.
- The bounded topology is proven against REPRO-1 without an unguarded xfail.
- CI ownership, threshold, tradeoffs, and residual risk are documented.
- PYPOST-1115 remains explicitly out of scope.

## Task Description

The REPRO-1 workload can crash while many GUI modules execute in one process. The safe
scope is test infrastructure: bound GUI workloads by process lifetime and preserve the
existing per-file isolation used by the normal test runner. No production `apply_theme`
change is required.

## Q&A

- **Why is process isolation required?** REPRO-1 and DIAG-1 show that short-lived
  processes complete cleanly while cumulative in-process Qt state can crash.
- **What is out of scope?** The distinct SettingsDialog/QWidgetItem teardown issue in
  PYPOST-1115 and upstream PySide changes.
