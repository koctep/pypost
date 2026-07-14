# PYPOST-812: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | OTel section: editable `[otel]` extra is the primary install path; `requirements-otel.txt` is lock-only |

## Key maintainer workflow

1. Edit direct OTel pins in `requirements-otel.in` and mirror in `pyproject.toml` `[otel]`.
2. Regenerate lock with `make lock-otel` when pins change.
3. Install OTel locally: `make venv-otel` or `pip install -e ".[otel]"`.
4. Full dev env: `make install` (`pip install -e ".[dev,otel]"`).

## Cross-links

- Editable install (all extras): PYPOST-806 (`doc/dev/setup.md` § Project metadata)
- OTel overlay introduction: PYPOST-787 (`doc/dev/setup.md` § OpenTelemetry optional overlay)
- Lazy-import when OTel absent: PYPOST-811

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-812 end-to-end, tokens_used: 42000
