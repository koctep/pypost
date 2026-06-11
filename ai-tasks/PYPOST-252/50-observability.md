# PYPOST-252: Observability

## Assessment

Unit tests for `RequestManager` and `StateManager` exercise business logic with mocked storage
or isolated config directories. No new production logging or metrics are required.

## Test-time logging

- `RequestManager` delete/rename not-found and validation paths emit `WARNING` logs during
  tests. These are expected-path messages, not ERROR-level; no `caplog` contract required per
  PYPOST-574 (ERROR-only rule).
- `StateManager` uses `logger.debug` for save scheduling; not visible at default `log_cli_level=WARNING`.

## CI visibility

- Manager tests run as part of default `make test` / CI pytest matrix.
- Failures surface as standard pytest assertion errors with `--tb=short`.

## Local visibility

Focused commands in `doc/dev/testing.md` allow running manager tests in isolation during
refactors.
