# PYPOST-807: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | `pythonpath` reference points to `[tool.pytest.ini_options]` |
| `doc/dev/testing.md` | Markers, coverage gate, CI defaults, empty_tests_policy, log_cli sections |
| `doc/dev/observability_audit.md` | Local config column renamed to `pyproject.toml` |
| `doc/dev/test_audit.md` | Coverage gate source updated |
| `doc/dev/tech-debt/PYPOST-434.md` | Historical `pythonpath` note updated |

## Key maintainer workflow

1. Edit pytest defaults in `pyproject.toml` under `[tool.pytest.ini_options]`.
2. When changing `--cov-fail-under`, update `THRESHOLD` in `.github/workflows/test.yml` together.
3. Local runs: `make test` (config auto-loaded from `pyproject.toml`).

## Cross-links

- PEP 621 metadata: PYPOST-785
- Editable install: PYPOST-806 (`doc/dev/setup.md` § Unit tests)
- Original `pythonpath` fix: PYPOST-434

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-807 end-to-end, tokens_used: 45000
