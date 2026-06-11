# PYPOST-279: Policy for pytest exit code 5 (no tests collected)

## Goals

Technical debt from [PYPOST-27](https://pypost.atlassian.net/browse/PYPOST-27),
[PYPOST-30](https://pypost.atlassian.net/browse/PYPOST-30), and
[PYPOST-33](https://pypost.atlassian.net/browse/PYPOST-33) flagged ambiguity when `pytest`
reports exit code `5` (`collected 0 items`). PyPost now has a substantial automated test
suite; zero collection indicates misconfiguration (wrong path, broken markers, accidental
deletion) rather than an acceptable empty state. This task records the policy and adds
regression coverage so CI and local workflows cannot silently treat “no tests” as success.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want a documented policy that exit code `5` is a failure so that
  misconfigured test runs cannot pass CI or `make test`.
- As a **developer**, I want `make test` to fail when no tests are collected so that I
  discover broken test paths before merging.
- As a **reviewer**, I want automated regression tests that lock the policy so future Makefile
  or workflow changes cannot downgrade exit code `5` to success or warning.

## Policy Decision

| Exit code | Meaning | Treatment in CI and `make test` |
| --- | --- | --- |
| `5` | No tests collected | **FAILURE** — must never be treated as success or warning |

Rationale: the repository expects hundreds of collected tests. Zero collection is always
actionable and must block merges and local quality gates.

## Definition of Done

- [x] Policy documented in `10-requirements.md` and `20-architecture.md`.
- [x] Regression tests assert pytest exit code `5` for an empty tests directory.
- [x] Regression test asserts `make test` returns non-zero in an isolated workspace with no
      collectable tests and that make reports pytest exit `5`.
- [x] All new tests declare explicit `pytest.mark.timeout(30)` per project testing rules.

## Task Description

### Problem

Historically, an empty or misconfigured `tests/` tree produced `collected 0 items` and pytest
exit code `5`. Some workflows treated this as benign during early bootstrap. With a mature
suite, the same outcome hides regressions in collection paths, marker filters, or CI wiring.

### Functional requirements

1. **Policy** — Exit code `5` MUST be treated as failure in CI and `make test`.
2. **No downgrade** — No wrapper may map exit code `5` to success (`0`) or warning-only
   behavior.
3. **Regression tests** — Automated tests lock the policy for direct `pytest` invocation and
   `make test` in an isolated fixture workspace.

### Non-functional requirements

- Tests must use bounded subprocess timeouts and explicit per-test `pytest.mark.timeout`
  markers.
- Tests must not modify the repository `.venv` or the main `tests/` tree.

### Out of scope

- Changing pytest.ini `addopts` or coverage thresholds.
- CI workflow edits (enforcement relies on native exit-code propagation; workflow already
  fails on non-zero pytest exit).
- Developer documentation updates (`doc/dev/testing.md`) — deferred to Step 7.

## Q&A

- **Why failure, not warning?** Zero collection with a mature suite is always misconfiguration;
  warnings are easy to miss in CI logs.
- **Does this affect legitimate empty repos?** PyPost is past bootstrap; empty collection is not
  a valid steady state for this project.
