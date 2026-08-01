# PYPOST-929: Contract test — make install touches extra stamps

## Goals

[PYPOST-905](https://pypost.atlassian.net/browse/PYPOST-905) added stamp-gated
`venv-test` and `venv-otel` prerequisites and made `make install` touch both
stamp files after a combined `[dev,otel]` editable install. That touch keeps
split extras in sync so pytest and lint targets skip redundant pip work after
a one-shot `make install`.

The Makefile recipe is present, but there was no automated guard. Without a
contract test, a future edit could remove the `touch` lines while leaving
dependency-chain tests green — contributors would pay repeated pip installs
again without an obvious signal.

**Business need:** Lock the install→stamp contract so `make install` remains a
reliable one-shot setup path for developers, CI, and agent loops.

**Source:** Follow-up from `ai-tasks/PYPOST-905/60-tech-debt.md` item 1.
Jira parent context: [PYPOST-905](https://pypost.atlassian.net/browse/PYPOST-905).

## Programming Language

Python pytest contract tests in `tests/test_makefile.py`
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **developer** who runs `make install` once after clone, I want CI and
  local tests to fail if `install` stops updating the extra stamps, so later
  `make test` stays fast without silent regression.
- As a **maintainer** editing the root `Makefile`, I want a focused contract
  test that catches accidental removal of stamp touches from the `install`
  recipe.

## Definition of Done

- A pytest contract test runs `make install` in the isolated makefile
  workspace fixture and asserts both `.venv/.venv-test-<pyver>` and
  `.venv/.venv-otel-<pyver>` exist afterward.
- The test fails if `install` no longer creates/touches either stamp.
- Optional: assert subsequent `venv-test` / `venv-otel` skip pip when stamps
  were set by `install`.
- Test has an explicit timeout marker and passes in `make test`.
- Developer docs in `doc/dev/testing.md` mention the new contract.

## Task Description

Add the deferred contract test from PYPOST-905. No Makefile change is required
when the current recipe already touches both stamps; this task is test coverage
and documentation only.

## Constraints and Assumptions

- Reuse existing `make_workspace` fixture and helpers from
  `tests/test_makefile.py` (PYPOST-905 patterns).
- Tests spawn `make` with `PYTHON=sys.executable` (PYPOST-718).
- Fast suite only — no new `@pytest.mark.slow` tests.

## Q&A

- **Why not change the Makefile?** PYPOST-905 already added
  `touch "$(VENV_TEST_STAMP)" "$(VENV_OTEL_STAMP)"` to `install`.
- **Why does Step 3 not start red?** Production behavior is correct; the test
  is a regression guard that would fail if the touch lines are removed.
