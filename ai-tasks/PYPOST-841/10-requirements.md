# PYPOST-841: Harden AgentAppSession mid-start cleanup

## Goals

When an agent session fails during start (before ready), temporary directories and
ephemeral metrics must not leak. Operators and CI need failed starts to leave the
process as clean as a successful shutdown.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As a **CI / agent harness**, I want failed starts to release temp dirs and
  metrics binds so the next session (or later tests) is not blocked by orphans.
- As a **maintainer**, I want start failure cleanup to match the ready-timeout
  path, not only that one exception type.

## Definition of Done

- Any failure from `AgentAppSession.start` after resources are allocated triggers
  the same cleanup path as shutdown (temp dirs + metrics + partial composed app).
- Automated tests cover at least one mid-start failure path and assert no orphan
  temp dirs / metrics listener for that path.
- Docs note transactional start cleanup.

## Task Description

**Problem:** Ready timeout calls `shutdown()`; other mid-start failures do not,
so temp dirs and metrics can leak when `compose_app` or the ready wait fails for
non-timeout reasons.

**Business need:** Predictable cleanup on every failed start.

### In Scope

- Transactional cleanup on `start()` failure.
- Tests for mid-start failure paths.
- Brief lifecycle doc update.

### Out of Scope

- Changing successful-start semantics.
- Hard socket assert for post-shutdown port free (PYPOST-842).
- Full `make check` campaign (PYPOST-843).

## Q&A

| Question | Answer |
| --- | --- |
| Why not only rely on `__exit__`? | `start()` called without a context manager, or failures inside `__enter__` before return, must still clean up. |
| Sprint mode? | Autonomous sprint-task-runner. |
