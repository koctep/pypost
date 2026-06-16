# PYPOST-736: Run make lint in CI

## Goals

Prevent flake8 violations from merging silently — CI should fail when lint fails,
not just when tests fail.

## Definition of Done

- GitHub Actions test workflow runs flake8 against `pypost/` on every push/PR.
- A lint failure fails the CI job (matches local `make lint` semantics: non-zero exit).

## Task Description

The audit found flake8 was never executed in GitHub Actions, even though `make lint`
exists locally and `flake8` was already installed as a test tool in CI (unused).
PYPOST-729 (same sprint) already fixed the 4 existing violations, so turning this on
now won't break the pipeline.
