# PYPOST-800: Add pytest smoke for make help non-empty output

## Goals

PYPOST-794 added a self-documenting `help` target to the root Makefile. Without an automated
check, accidental removal of `##` annotations or breakage of the help recipe could go unnoticed
until a developer runs `make help` manually. This task adds a fast pytest smoke test so CI and
`make check` catch regressions in Makefile help output.

## User Stories

- As a maintainer, I want CI to fail when `make help` produces empty output, so that
  self-documenting targets stay intact.
- As a developer, I want the help smoke test to run in the default fast suite, so that local
  `make check` mirrors CI without extra steps.

## Definition of Done

- A pytest in `tests/test_makefile.py` shells out to `make help` in an isolated workspace and
  asserts non-empty stdout.
- The test exits zero and runs in the default fast suite (no `@pytest.mark.slow`).
- `make check` passes.
- Developer docs mention the help smoke coverage.

## Task Description

Follow-up from [PYPOST-794](https://pypost.atlassian.net/browse/PYPOST-794) tech debt (line 26
of `ai-tasks/PYPOST-794/60-tech-debt.md`). Scope is a single integration test reusing the
existing `_run_make` helper and `make_workspace` fixture — no Makefile or CI workflow changes.

Implementation: Python (pytest).

## Q&A

- **Q**: Should the test assert specific target names?
- **A**: No — non-empty output is sufficient to catch removal of `##` annotations; target lists
  are covered by manual review and PYPOST-794 acceptance criteria.
