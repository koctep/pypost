# PYPOST-787: Code Cleanup

## Lint

- `make lint` — no new flake8 issues in modified Python files.

## Lock verification

- `make check-lock` — production lock matches `requirements.in` (OTel removed).
- `make check-lock-otel` — OTel overlay lock matches `requirements-otel.in`.

## Test results

- `make check` — lint + fast test suite including OTel and Makefile dependency-chain tests.
