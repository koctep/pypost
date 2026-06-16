# PYPOST-723: Document local vs CI test parity

## Goals

Help developers debugging "works locally, fails in CI" (or vice versa) reports
quickly distinguish real bugs from macOS/Python-version environment drift against
the Ubuntu CI matrix.

## Definition of Done

- A troubleshooting section exists in `doc/dev/testing.md` mapping symptom → cause → fix
  for known local/CI differences.
- `doc/dev/test_audit.md`'s existing brief "Local vs CI" note links to it.

## Task Description

The audit found macOS/Python version differences vs Ubuntu CI causing confusion
(R-P2-005). PYPOST-718 already fixed one concrete instance (Makefile PYTHON
coupling in tests). This task documents that fix plus other known parity gaps
(Qt/EGL runtime libraries, Python version matrix, OS-gated code branches) so
future contributors don't have to rediscover them.
