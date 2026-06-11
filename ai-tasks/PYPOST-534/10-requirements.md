# PYPOST-534: Benchmark env save with 100+ hidden keys

## Goals

PYPOST-485 introduced selective re-encrypt so unchanged hidden environment values skip Fernet
calls on save. Large environments (100+ secrets) are the scenario where that optimization matters.
This task adds automated guards and a profiling harness so regressions that force full
re-encryption on every save are caught before they reach users.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want CI tests that exercise 100+ hidden keys so selective re-encrypt
  cannot silently regress.
- As a developer profiling save latency, I want a repeatable local harness that reports
  encrypt vs reuse timing and stats.
- As an operator with large secret sets, I want confidence that editing one variable does not
  trigger re-encryption of every other secret.

## Definition of Done

- Automated tests cover environments with at least 100 hidden keys for reuse stats, metrics, and
  relative timing vs full re-encrypt.
- Local profiling script documents how to run the benchmark on developer hardware.
- Developer documentation describes the harness and how to interpret results.
- Existing encryption and storage tests continue to pass.

## Out of Scope

- Changing selective re-encrypt logic (PYPOST-485).
- New Prometheus counters for reuse (remains log-only per PYPOST-485).
- Async storage or UI-thread changes (PYPOST-486).

## Task Description

Follow-up from PYPOST-485 tech debt: add benchmark or profiling harness for environments with
100+ hidden keys to guard regressions in selective re-encrypt.

## Q&A

- Q: Why 100+ keys?
  A: PYPOST-485 tech debt called out large single-environment dictionaries; 100+ is a realistic
  stress size for secret-heavy workspaces.
- Q: Source?
  A: [PYPOST-485 tech debt](https://pypost.atlassian.net/browse/PYPOST-485).
