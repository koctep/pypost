# PYPOST-1509: Fix pre-existing registry test line-length lint failure

## Goals

Maintainers rely on `make lint` as a trustworthy quality gate for the repository,
including the test-source lint baseline. A single overlong comment in the MCP
server registry test module caused a reproducible E501 failure that blocked the
gate for unrelated work. Clearing that failure restores confidence that new lint
regressions are real defects rather than known noise.

This debt was discovered during PYPOST-1463 as a NON-BLOCKER pre-existing lint
finding and ticketed so the gate can be repaired without expanding that task's
scope.

## User Stories

- As a maintainer running `make lint` / `make check`, I want the registry test
  module to satisfy the 100-character line-length rule so the quality gate
  reports only genuine new findings.
- As a developer working on MCP registry behavior, I want existing test comments
  and assertions left behaviorally unchanged so formatting cleanup does not alter
  what the suite proves.

## Definition of Done

- The overlong comment at
  `tests/test_mcp_server_registry.py` (historically line 308, 111 characters)
  is wrapped to ≤ 100 characters per line.
- `make lint` no longer reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long
  (111 > 100 characters)` for that comment.
- Test runtime behavior, assertions, and fixtures are unchanged.
- Top-Down artifacts for PYPOST-1509 exist under `ai-tasks/PYPOST-1509/`.

## Task Description

**Problem.** At base commit `33d5cb1a`, `make lint` fails in `lint-tests` because
flake8 reports E501 on a single comment line in
`tests/test_mcp_server_registry.py` (111 > 100 characters). The failure is
formatting-only; no pytest node id applies.

**Goal.** Split/wrap that comment so the line-length rule is satisfied without
changing what the surrounding test asserts.

**Constraints.**

- Implementation language: Python.
- Make-only verification (`make lint`); do not invoke raw flake8/pytest CLIs.
- No production-code changes; no test-behavior changes; comment formatting only.
- Scope is this single E501; unrelated lint debt stays out of scope.

## Q&A

- **Why is this a Debt issue rather than a feature?**
  It repairs a pre-existing quality-gate failure that already existed at the
  recorded base commit and was filed from another task's tech-debt analysis.
- **Why not add a new pytest?**
  The acceptance signal is the lint gate itself. A behavioral test would not
  fail for an overlong comment and would not prove the fix.
- **What programming language is used?**
  Python.
