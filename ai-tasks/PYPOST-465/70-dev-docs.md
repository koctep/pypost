# PYPOST-465: Dev Docs

## Updates

| File | Change |
| ---- | ------ |
| `doc/dev/testing.md` | Added § Reproducible test environment (PYPOST-465): install checklist, regression commands, CI/local parity |
| `doc/dev/setup.md` | Aligned Python prerequisite to 3.11+; expanded unit-test section with `make install` + regression targets |

## Summary

Documented the standard path to a reproducible test-ready environment: `make install` provisions
both `requirements.txt` and Makefile `venv-test` tooling (`pytest`, `pytest-cov`,
`pytest-timeout`, `flake8`); `make test`, `make test-slow`, and `make test-cov` cover full
local regression; CI main job now lists `pytest-timeout` alongside the same test tools for
parity with local installs. Python version guidance notes README 3.11+ and CI matrix 3.11/3.13.
