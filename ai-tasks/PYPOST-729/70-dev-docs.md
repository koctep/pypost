# PYPOST-729: Dev Docs

## Changes

No new documentation file needed. `doc/dev/setup.md` already documents `make lint`
and the flake8 integration.

The fixes in this task are internal code quality corrections. Developers should be
aware that `make lint` now exits 0 and can be safely run as part of pre-commit or CI
workflows (CI wiring tracked in PYPOST-736).

## No doc/dev update required

All lint-related developer guidance lives in `doc/dev/setup.md` (lines 82–105).
