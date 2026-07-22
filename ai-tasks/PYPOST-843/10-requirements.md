# PYPOST-843: Run full make check for lifecycle changes

## Goals

Confirm the agent lifecycle change set does not break the project quality gate.

## Programming Language

Python

## Definition of Done

- `make check` is green on a branch that includes PYPOST-833 lifecycle work.

## Task Description

Deferred full gate after PYPOST-833 scoped smoke; run analyze + full fast suite
and fix regressions needed for a green gate.

## Q&A

| Question | Answer |
| --- | --- |
| Fix unrelated failures? | Yes when required for green `make check` acceptance. |
