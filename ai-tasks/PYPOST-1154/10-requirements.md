# PYPOST-1154: Set default WORKERS for parallel test runner

## Goals

Developers running `make test` without tuning should get the fastest reliable parallel test
execution on typical dev machines. PYPOST-1149 added optional `WORKERS`, but leaving it empty
falls back to `cpu_count()`, which benchmarks show is slower than a lightly oversubscribed
default on a 6-core ARM64 container.

## User Stories

- As a developer, I want `make test` to pick a sensible worker count automatically so I do not
  need to benchmark `WORKERS` on every machine.
- As a CI operator, I want the Makefile default and orchestrator script fallback to use the same
  policy so behavior is consistent whether tests are started via Make or the script directly.
- As a maintainer, I want the default policy documented so operators can override `WORKERS` when
  memory pressure or oversubscription becomes a problem.

## Definition of Done

- Bare `make test` and `make test-cov` pass a non-empty default worker count to the parallel
  orchestrator (not conditional on user setting `WORKERS`).
- `scripts/run_parallel_tests.py` uses the same default when no CLI or env override is set.
- On a host with six logical CPUs, the default is eight workers (benchmark-optimal on the dev
  container).
- `doc/dev/parallel_test_runner.md` and `doc/dev/testing.md` describe the default policy.
- Automated tests lock the default policy and Makefile wiring.
- `make check` passes.

## Task Description

Benchmarks on 6-core ARM64 (container `01e1f0f08b7c`) showed `WORKERS=8` at ~2m1s wall clock
versus `cpu_count()`=6 at ~2m5s, while `WORKERS=24` regressed to ~2m24s. The task defines a
documented oversubscription policy (not a hardcoded constant) and aligns Makefile, script, docs,
and tests.

## Q&A

- **Q:** Why oversubscribe beyond CPU count?
  **A:** Subprocess pytest runs are I/O- and startup-bound; modest oversubscription improved wall
  clock on the reference host without the regression seen at very high worker counts.
