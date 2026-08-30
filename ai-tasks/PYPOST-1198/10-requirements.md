# PYPOST-1198: Log worker_timeout on parallel_test_run_started

## Goals

Operators currently only learn the configured per-worker timeout bound after a worker actually
times out, via a separate WARNING-level log emitted when the timeout is exceeded. There is no
way to confirm what timeout bound is in effect for a given run
until something goes wrong. Surfacing the configured `worker_timeout` in the run-start INFO log
(`parallel_test_run_started`) lets operators verify and audit the configured bound proactively —
e.g. when investigating CI behavior, comparing environments, or confirming an override took
effect — without needing to wait for or provoke a timeout. This closes a small observability gap
left over as a follow-up from PYPOST-1192 (recorded in
`ai-tasks/PYPOST-1192/60-tech-debt.md`, follow-up item 2).

## User Stories

- As an operator running the parallel test runner, I want the effective per-worker timeout bound
  logged at run start, so that I can confirm the configured value without waiting for a worker to
  time out.
- As an operator troubleshooting CI test runs, I want the run-start log line to be
  self-sufficient for auditing the run's configuration, so that I don't have to cross-reference
  docs, Makefile env vars, or wait for a WARNING to discover the effective timeout bound.

## Definition of Done

- The `parallel_test_run_started` INFO log line includes the effective `worker_timeout` value
  (the same bound the runner will use to enforce per-worker timeouts for this run), alongside the
  run's existing configuration summary fields it already logs.
- The value logged is the actual bound in effect for the run (reflecting any configured
  override), not just the hardcoded default.
- No change to when or how the existing WARNING-level timeout log fires; that log is out of
  scope for this task.
- Existing behavior of the parallel test runner (test discovery, execution, reporting) is
  unchanged — this is an additive logging-field change only.

## Task Description

The parallel test runner emits a single structured INFO log line, `parallel_test_run_started`,
at the start of a run, summarizing the run's configuration for operators. The run's
configuration already includes a resolved per-worker timeout bound, but this bound is not
currently included in that startup log summary — it only becomes visible via a WARNING log after
a worker exceeds it.

This task adds the effective `worker_timeout` value as a field on the existing
`parallel_test_run_started` INFO log line. This is a small, low-risk, additive observability
change: one field is added to one existing log statement.

**Constraints and assumptions:**

- Scope is limited to the `parallel_test_run_started` INFO log line only. The WARNING-level
  timeout log elsewhere in the file is not touched.
- No new configuration, CLI flags, or behavior changes — the per-worker timeout bound is already
  computed and available as part of the run's configuration before this log line executes.
- Out of scope (owned by sibling Jira issues PYPOST-1197 and PYPOST-1199, not this task):
  process-group teardown/orphan cleanup, and unit tests for timeout precedence rules.
- Existing automated checks on the startup log message's content must continue to pass; they may
  need to reflect the new field.

## Main Entities

- **Run configuration**: the business-level notion of "how this test run is configured" —
  includes worker count, coverage flag, report path, test targets, pytest args, and the
  per-worker timeout bound. This task makes one more attribute of that configuration (the
  timeout bound) visible to operators at run start.
- **Run-start log event (`parallel_test_run_started`)**: the operator-facing announcement of a
  run's configuration, emitted once per run before execution begins.

## Q&A

- **Q: Why does this matter if operators can already find the timeout via docs or Make env
  vars?**
  A: Docs and env vars describe intent, not the resolved value actually in effect for a specific
  run (which may come from a CLI override, env var, or default with a defined precedence).
  Logging the resolved value removes ambiguity and lets operators audit runs after the fact from
  logs alone.
- **Q: Should this task change the WARNING-level timeout log?**
  A: No. That log's trigger condition and content are unrelated to this task's scope, which is
  purely about adding visibility at run start.
