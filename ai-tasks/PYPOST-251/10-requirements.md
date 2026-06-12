# PYPOST-251: Close pytest-setup debt from PYPOST-29

## Goals

Verify that the debt recorded in PYPOST-29 — "no automated tests because pytest setup is
missing" — is no longer applicable, document the satisfied state, and close the Jira ticket
without redundant infrastructure work.

## User Stories

- As a **developer**, I want `make test` to run pytest so refactors are regression-safe without
  manual verification.
- As a **maintainer**, I want the PYPOST-29 debt trail updated so obsolete follow-ups are not
  re-opened.

## Definition of Done

- [x] Pytest infrastructure confirmed: `pytest.ini`, `Makefile` (`test`, `test-cov`, `venv-test`),
      `tests/conftest.py` timeout enforcement.
- [x] `tests/` directory is non-empty with runnable automated coverage (127 test modules).
- [x] Manager unit-test debt tracked separately in
      [PYPOST-252](https://pypost.atlassian.net/browse/PYPOST-252) — already Done.
- [x] `doc/dev/testing.md` references PYPOST-251 closure.
- [x] Top-down artifacts stored under `ai-tasks/PYPOST-251/`.

## Task Description

**Source:** `ai-tasks/PYPOST-29/40-tech-debt.md` — debt item
[PYPOST-251](https://pypost.atlassian.net/browse/PYPOST-251).

**Discovery (2026-06-12):** The precondition this ticket waited on is satisfied:

| Area | Status at PYPOST-29 close | Status now |
| --- | --- | --- |
| Pytest config | Missing | `pytest.ini` with markers, coverage gate, log_cli |
| Test runner | Missing | `make test`, `make test-cov`, `make test-slow` |
| Test harness | Empty `tests/` | 127 `tests/test_*.py` modules + `conftest.py` |
| Manager tests | Manual only | Covered in PYPOST-252 |

**Remaining work:** Document verification, update dev docs, close Jira. No new pytest plugins,
CI changes, or duplicate test authoring.

**Out of scope:** Re-implementing infrastructure; manager edge-case tests (PYPOST-252).

## Q&A

| Question | Answer |
| --- | --- |
| Why not add more tests here? | PYPOST-252 closed the scoped manager follow-up; suite is already broad. |
| Is this ticket duplicate of PYPOST-252? | PYPOST-251 is the parent debt (missing setup); PYPOST-252 is the scoped test gap. |
| Close as Won't Do or Done? | Done — precondition met; verification documented. |
