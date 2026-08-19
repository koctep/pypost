# PYPOST-998: Optionally include check-lock in make check or document separately

## Programming Language

Makefile for build target and English Markdown for developer documentation.

## Goals

Follow-up from PYPOST-984. Developers need clear clarity on why `make check` does not invoke `uv pip compile` against PyPI (to remain fast and runnable offline without `uv`), and how to run lock verification (`make check-lock`, `make check-lock-dev`, `make check-lock-otel`, `make check-lock-all`) when dependency definitions change.

**Business goal:** Provide `check-lock-all` convenience target in `Makefile` and comprehensively document the lock verification workflow in `doc/dev/setup.md`.

## Definition of Done

- [ ] `Makefile` provides `check-lock-all` running `check-lock`, `check-lock-dev`, `check-lock-otel`, and `check-license-inventory`.
- [ ] `doc/dev/setup.md` explains the design rationale behind `make check` vs `make check-lock*` and provides the 4-step dependency update procedure.
- [ ] All Makefile targets and lint checks pass cleanly.
