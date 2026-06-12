# PYPOST-251: Observability

## Assessment

This ticket verifies existing pytest infrastructure. No new production logging or metrics are
required.

## Test-time visibility

- Default `make test` runs the fast suite with `log_cli_level=WARNING` per `pytest.ini`.
- CI surfaces pytest failures via `.github/workflows/test.yml` matrix jobs.
- Manager and integration tests emit expected WARNING logs on not-found paths; no new contracts.

## Local visibility

Developers use `make test`, `make test-cov`, and focused commands in `doc/dev/testing.md`.
