# PYPOST-752: Architecture

Enable the `flake8-print` plugin (error code **T201**) through repo-level `.flake8` config.
Lint scope stays `pypost/` only (`make lint` and CI lint step unchanged).

Dependency wiring:

- `Makefile` target `venv-test` — local dev installs `flake8-print` alongside `flake8`
- `.github/workflows/test.yml` — CI installs the same plugin before `flake8` runs

No application code changes; enforcement is config-only.
