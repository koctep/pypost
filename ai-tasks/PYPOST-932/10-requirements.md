# PYPOST-932: Contract test typecheck depends on venv-test

## Goals

[PYPOST-906](https://pypost.atlassian.net/browse/PYPOST-906) made `make lint`
depend on `venv-test` (mirroring `typecheck`) and added a Makefile contract
test for lint. The same peer pattern for `typecheck` was already in the
Makefile but never had a dedicated contract assertion — architecture for 906
overstated that lock. Without it, a future edit could drop `venv-test` from
`typecheck` without failing CI.

This Debt closes that gap: **`test_typecheck_depends_on_marker_and_venv_test`**
locks the existing `typecheck: $(VENV_MARKER) venv-test` edge so it cannot
regress silently.

**Business need:** Makefile contract tests must cover all quality targets that
ensure `[dev]` via `venv-test`, so contributor and agent loops stay consistent.

**Source:** [PYPOST-906](https://pypost.atlassian.net/browse/PYPOST-906)
`60-tech-debt.md` follow-up #1.

## Programming Language

Python pytest (`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`).
Developer docs in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want a contract test for `typecheck` → `venv-test`,
  so the peer pattern cannot drift after PYPOST-906.
- As a **contributor**, I want `make typecheck` to keep auto-ensuring `[dev]`,
  so I do not need a separate install step before mypy.

## Definition of Done

- `tests/test_makefile.py` includes `test_typecheck_depends_on_marker_and_venv_test`
  with the same shape as `test_lint_depends_on_marker_and_venv_test` (marker
  present, `venv-test` present, `install` absent).
- Targeted and full makefile contract suite passes.
- Developer docs mention the new contract lock where Makefile automation tests
  are listed.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

`typecheck` already depends on `$(VENV_MARKER) venv-test` in the root Makefile,
but `tests/test_makefile.py` only asserted that edge for lint (906), pytest
targets (872), and related stamps — not for `typecheck` by name.

### Business need

Encode the existing ensure-tooling promise in automated checks so refactors
cannot remove `venv-test` from `typecheck` without a failing test.

### In Scope

- Add `test_typecheck_depends_on_marker_and_venv_test` in `TestDependencyChain`.
- Update `doc/dev/testing.md` Makefile automation table / dependency-chain row.
- Task artifacts under `ai-tasks/PYPOST-932/`.

### Out of Scope

- Makefile production changes (edge already correct).
- Changing `run`, `lint`, stamp mechanics, or mypy behavior.
- Creating Jira Debt tickets in this run (list follow-ups in
  `60-tech-debt.md` only).

## Functional Requirements

- FR1: Contract test asserts `typecheck` prerequisites include `MARKER_REL`
  and `venv-test`, and exclude `install`.
- FR2: Test mirrors lint peer lock naming and docstring style (PYPOST-906).
- FR3: Existing makefile tests remain green.

## Non-Functional Requirements

- NFR1: Module timeout via existing `pytestmark = pytest.mark.timeout(120)`.
- NFR2: No new fixtures; reuse `_prerequisites` / `make_workspace`.
- NFR3: Docs line length ≤ 100 where practical.

## Constraints and Assumptions

- Root `Makefile` `typecheck` line is already `$(VENV_MARKER) venv-test`.
- No red Step 3 repro — this is a regression lock, not a behavior fix.
- Parent debt item is PYPOST-906 follow-up #1.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Typecheck entry (`typecheck`) | Optional mypy gate; ensures `[dev]` via `venv-test` |
| Dev extra ensure (`venv-test`) | Ensures pytest / flake8 / mypy peers in `.venv` |
| Contract tests | Encode Make prerequisite promises |
| Maintainer | Prevents silent regression of ensure edges |

## Q&A

| Q | A |
| --- | --- |
| Why not change the Makefile? | Edge already matches lint; only the test was missing. |
| Why N/A for Step 3? | No behavioral change; test is green on current code. |
| Relation to PYPOST-906? | Completes optional follow-up #1 from 906 debt analysis. |
