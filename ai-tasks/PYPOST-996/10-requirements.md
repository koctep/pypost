# PYPOST-996: Port check-lock retry/diagnostics to check-lock-dev and check-lock-otel

## Programming Language

Makefile syntax for build automation targets, Python for automated test fixtures, and English Markdown for documentation.

## Goals

Follow-up from PYPOST-984. In `Makefile`, `check-lock` featured a resilient 3-attempt retry loop with exponential backoff, clear and distinct error messages distinguishing tool/network compile failure from genuine lock drift, and cleanup of temporary scratch files. However, `check-lock-dev` and `check-lock-otel` used simple one-shot execution with raw `diff -q` and did not clean up scratch files on failure.

**Business goal:** Port the retry loop, distinct error messaging, and scratch file cleanup across `check-lock-dev` and `check-lock-otel` in `Makefile`, and lock the contract with automated tests in `tests/test_makefile_check_lock_retry.py`.

## Definition of Done

- [ ] `check-lock-dev` and `check-lock-otel` in `Makefile` implement the 3-attempt retry loop with exponential backoff.
- [ ] Both targets output distinct messages for compile failure vs stale lock.
- [ ] Scratch files are cleaned up in all code paths.
- [ ] `tests/test_makefile_check_lock_retry.py` verifies all three targets.
