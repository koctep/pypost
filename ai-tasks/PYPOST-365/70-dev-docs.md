# PYPOST-365 — Developer Documentation

> Date: 2026-06-11

## 1. What Changed and Why

Documented PyPost Qt GUI testing conventions and added ResponseView search tests to satisfy
PYPOST-37 follow-up PYPOST-365. The project uses offscreen Qt (`QT_QPA_PLATFORM=offscreen`) and
module-scoped `QApplication` fixtures — not the `pytest-qt` package.

## 2. New and Updated Modules

- `tests/conftest.py` — shared module-scoped `qapp` fixture
- `tests/test_response_view_search.py` — search bar behavior
- `doc/dev/gui_testing.md` — GUI test patterns (new)
- `doc/dev/testing.md` — GUI testing section and link

## 3. Testing

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_response_view_search.py -v
make test
```

## 4. Operator Notes

No operator-facing changes.
