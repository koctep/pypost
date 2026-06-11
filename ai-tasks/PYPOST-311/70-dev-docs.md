# PYPOST-311: Dev Docs

## Updates

| File | Change |
| ---- | ------ |
| `doc/dev/testing.md` | Added § CI dependency caching (PYPOST-311): cache key, jobs, invalidation, local vs CI |

## Summary

Documented pip wheel caching via `actions/setup-python@v5`, explicit
`cache-dependency-path: requirements.txt`, per-Python cache scope, and the relationship between
CI caching and local Makefile `.venv` installs.
