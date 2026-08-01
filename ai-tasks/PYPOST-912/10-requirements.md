# PYPOST-912: Caplog proof for dump hook failed event

## Goals

Maintainers need unit-level confidence that when the optional
`AgentAppSession.__exit__` failure-dump hook raises, lifecycle logs
`agent_session_failure_dump_hook_failed` and still shuts down without masking
the original test failure. PYPOST-875 added the WARNING; this debt ticket locks
it under caplog.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want a caplog unit test that asserts
  `agent_session_failure_dump_hook_failed` when the dump hook raises, so hook
  wrapper regressions are caught without subprocess probes.
- As a **contributor**, I want the test to follow existing lifecycle caplog and
  timeout patterns, so it stays consistent with the suite.
- As a **desktop user** (indirect), I want no product UX change — only test
  coverage for existing observability.

## Definition of Done

- An in-process `@pytest.mark.agent_e2e` test installs a raising dump hook,
  fails a direct `AgentAppSession` context, and asserts the WARNING under
  caplog at `pypost.agent.lifecycle`.
- The check confirms the original `AssertionError` still propagates.
- Explicit pytest timeout marker on the module (existing `pytestmark`).
- Steps 1–8 task artifacts exist for PYPOST-912.
- No intentional product change unless the test exposes a logging bug.

## Task Description

**Problem:** PYPOST-875 noted missing caplog coverage for
`agent_session_failure_dump_hook_failed`. Source:
[PYPOST-912](https://pypost.atlassian.net/browse/PYPOST-912), from
[PYPOST-875](https://pypost.atlassian.net/browse/PYPOST-875)
`ai-tasks/PYPOST-875/60-tech-debt.md`.

**Business need:** Close lowest-priority testing debt so dump-hook failure
logging stays verified without relying on manual log inspection.

### In Scope

- Focused caplog unit test in `tests/test_agent_e2e_failure_artifacts.py`.
- Hook save/restore via `set_agent_session_failure_dump_hook`.
- Completing Steps 1–8 workflow artifacts.
- Developer doc cross-links (failure artifacts + logging catalog).

### Out of Scope

- Changing dump helper best-effort catalogue (PYPOST-876).
- CI artifact upload (PYPOST-874).
- Renaming `session_fixture` provenance field (PYPOST-913).
- New product features or UI changes.

## Functional Requirements

- FR1: When the installed dump hook raises, caplog captures
  `agent_session_failure_dump_hook_failed error=<ExcType>`.
- FR2: The original exception from the session context still propagates.
- FR3: Session shutdown completes (no hang / leaked session after the test).
- FR4: Test uses `caplog.at_level(logging.WARNING, logger="pypost.agent.lifecycle")`.

## Non-Functional Requirements

- NFR1: Module-level `pytest.mark.timeout(60)` (GUI tier).
- NFR2: Marked `agent_e2e` for harness consistency with sibling failure tests.
- NFR3: Thin smoke — raising hook + caplog assert + minimal session-ready sanity.

## Q&A

| Question | Answer |
| --- | --- |
| Source of the debt item? | [PYPOST-875 tech debt](../PYPOST-875/60-tech-debt.md) → PYPOST-912. |
| Product code change expected? | No — WARNING already in `lifecycle.py`; gap is test coverage. |
| Subprocess vs in-process? | In-process caplog (fast, targeted). Subprocess proofs remain for dump files. |
