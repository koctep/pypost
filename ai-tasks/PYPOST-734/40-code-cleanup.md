# PYPOST-734: Code Cleanup

## Changes

| File | Change |
| --- | --- |
| `requirements-dev.in` | Added `mypy`, `types-PyYAML` |
| `requirements-dev.txt` | Regenerated lock |
| `pyproject.toml` | Dev extras + `[tool.mypy]` |
| `Makefile` | `typecheck` target |
| `scripts/check_mypy_baseline.py` | Baseline gate script |
| `mypy-baseline.json` | 54 frozen error signatures |
| `tests/test_mypy_baseline.py` | Baseline file structure tests |

## Verification

- [x] `make typecheck` — pass (baseline match)
- [x] `make lint` — pass
- [x] `make test` — pass (via `make check`)
- [x] No application code changes (tooling-only task)

## Checklist

- [x] Line length ≤ 100
- [x] UTF-8, LF endings
- [x] English comments and docs
- [x] Makefile target has `##` help comment
