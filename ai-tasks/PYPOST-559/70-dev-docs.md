# PYPOST-559: Dev Docs

## Updates

| File | Change |
| ---- | ------ |
| `doc/dev/testing.md` | Added PYPOST-559 slow install smoke scope, commands, and CI job note |

## Summary

Documented the three-way Makefile test scope split (PYPOST-307 / 310 / 559), `@pytest.mark.slow`
behavior, `make test-slow`, focused pytest commands, and the separate `make-install-smoke` CI
job with pip caching.
