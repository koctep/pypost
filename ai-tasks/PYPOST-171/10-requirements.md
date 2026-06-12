# PYPOST-171: Review MetricsManager locks during server start/stop

## Goals

PYPOST-23 flagged that metrics server lifecycle uses locks for thread safety during
start/stop. Maintainers need a documented review confirming whether that locking remains
appropriate after the metrics stack split (PYPOST-49/75) and whether any concurrency risk
warrants follow-up work.

## User Stories

- As a **maintainer**, I want the PYPOST-23 locking debt item reviewed with evidence so I can
  close it or schedule a fix.
- As a **reviewer**, I want call sites and lock scope documented so future lifecycle changes
  do not introduce races or deadlocks.
- As a **developer**, I want dev docs to state who may call start/stop/restart and from which
  thread, so I do not add unsafe concurrent callers.

## Definition of Done

- [x] Lock usage in metrics server lifecycle is reviewed and documented.
- [x] Production call sites for `start_server`, `stop_server`, and `restart_server` are
  identified.
- [x] Risk classification recorded (low / medium / high) with rationale.
- [x] PYPOST-23 locking tech-debt item closed or follow-up Jira created if needed.
- [x] `make test` passes.
- [x] Developer docs note threading and lock expectations for the metrics server.

## Task Description

**Source:** [PYPOST-23](https://pypost.atlassian.net/browse/PYPOST-23) tech-debt — locking in
`MetricsManager` during server start/stop (low risk, infrequent operations).

After PYPOST-49/75, lifecycle and `server_lock` live in `MetricsServer`; `MetricsManager` is
a thin facade. This task reviews that implementation.

**In scope:** Code review, risk assessment, documentation, close debt item.

**Out of scope:** Replacing `threading.Lock` with `RLock`, redesigning metrics threading, or
new integration tests unless a blocker is found.

## Q&A

| Question | Answer |
| --- | --- |
| Is code change required? | No — locking is adequate for current single-threaded callers. |
| New tests needed? | No — existing startup tests cover lifecycle; review-only task. |
