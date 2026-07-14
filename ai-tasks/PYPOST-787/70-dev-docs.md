# PYPOST-787: Dev Docs

## Updated files

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | OTel overlay section, Makefile behavior, install/test notes |
| `doc/dev/dependencies_audit.md` | Production table without OTel; optional OTel row; R-P3-003 Done |

## Key documentation points

- Production install: `requirements.txt` (13 direct deps, no OTel).
- OTel overlay: `requirements-otel.in` / `requirements-otel.txt`, `make lock-otel`,
  `make venv-otel`.
- CI test jobs install OTel overlay for `tests/test_metrics_otel.py`.
- Optional PEP 621 extra: `pip install -e ".[otel]"`.
