# PYPOST-840: Architecture

## Decision

**Verify + lock.** Acceptance is already satisfied by PYPOST-837:

| Concern | Current state |
| --- | --- |
| Canonical poll loop | `pypost.agent.ui_wait.wait_until` |
| Lifecycle | Imports `wait_until` from `ui_wait`; session method wraps it |
| Test helper | `tests.helpers.qt_wait` re-exports production `wait_until` |
| Agent → tests | No `tests` imports under `pypost.agent` |

No further production API change is required for DoD. This task adds **regression
locks** and closes the PYPOST-833 TD-1 documentation trail.

## Components

```text
pypost.agent.ui_wait.wait_until  ←── single processEvents + deadline loop
        ↑                    ↑
 AgentAppSession.wait_until  tests.helpers.qt_wait (re-export)
```

## Failing Repro Plan

**N/A — no behavioral change.** Current code already meets AC. Step 4 adds
positive lock tests (identity + source invariants) that fail if duplication
returns.

## Risks

- Future contributors may reintroduce a private `_wait_until` in lifecycle —
  mitigated by AST/source lock tests.
- Callers of `tests.helpers.qt_wait` must keep resolving to the same function
  object as production.
