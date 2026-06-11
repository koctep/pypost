# PYPOST-363 — Developer Documentation

> Date: 2026-06-11

## 1. What Changed and Why

Added 250 ms debounced search scheduling for large response bodies (>100KB) in `ResponseView`.
Small documents keep immediate search-on-keystroke behaviour. Clears and new responses cancel
pending debounce.

## 2. New and Updated Modules

- `pypost/ui/widgets/response_view.py` — `_schedule_search_text_changed`, `_search_timer`
- `tests/test_response_view_search.py` — debounce tests
- `doc/dev/response_search.md` — `_schedule_search_text_changed`, configuration section

## 3. Testing

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_response_view_search.py -v
```

## 4. Operator Notes

No operator-facing changes. Large-response search may show match counter ~250 ms after typing
stops; small responses behave as before.
