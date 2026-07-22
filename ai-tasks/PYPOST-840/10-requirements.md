# PYPOST-840: Deduplicate agent wait_until helper

## Goals

Agent and harness code must share one bounded Qt event-poll wait helper so
maintainers do not keep a production copy and a test-only copy in sync, and so
`pypost.agent` never depends on `tests/`.

This debt closes the PYPOST-833 follow-up: remove intentional duplication of
`_wait_until` by consolidating on a single production-safe implementation.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As a **maintainer**, I want one processEvents + deadline wait implementation so
  timeout and polling behavior cannot drift between agent lifecycle and tests.
- As an **agent package owner**, I want agent code free of `tests/` imports so
  production packaging stays clean.
- As a **test author**, I want existing `tests.helpers.qt_wait.wait_until` call
  sites to keep working without maintaining a second poll loop.

## Definition of Done

- No `tests/` import from `pypost.agent`.
- Single implementation of processEvents + deadline wait used by agent lifecycle
  (and by tests via re-export or direct production import).
- Regression coverage locks the single-implementation invariant.
- Dev docs state where the canonical helper lives and how tests consume it.

## Task Description

**Problem:** PYPOST-833 introduced a local `_wait_until` in agent lifecycle that
mirrored `tests.helpers.qt_wait.wait_until` to avoid importing tests into
production. That duplication is tech debt.

**Business need:** One shared, production-owned wait helper; tests may re-export
it but must not own a divergent poll loop.

### In Scope

- Confirm or complete consolidation under `pypost/`.
- Ensure lifecycle / agent surface uses that helper.
- Keep or add test re-export compatibility.
- Lock tests and brief doc notes.

### Out of Scope

- New settle conditions (widget/text/snapshot waits) — owned by PYPOST-837+.
- Changing default timeout semantics for callers.
- Broader Qt test harness redesign.

## Q&A

| Question | Answer |
| --- | --- |
| Why not import tests from agent? | Production packages must not depend on the test tree. |
| Is new wait behavior required? | No — unify ownership; sibling PYPOST-837 already delivered the helper. |
| Sprint mode? | sprint-task-runner autonomous; user step approval overridden. |
