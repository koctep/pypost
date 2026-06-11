# PYPOST-354 — Developer Documentation

> Date: 2026-06-11

## 1. What Changed and Why

Extracted `_search_text_or_clear` and `_track_search_result` in `ResponseView` so Next/Previous
navigation share one empty-query guard and one metrics/logging path. Behaviour is unchanged.

## 2. New and Updated Modules

- `pypost/ui/widgets/response_view.py` — navigation helpers
- `doc/dev/response_search.md` — `_track_search_result` and `_search_text_or_clear` sections

## 3. Testing

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_response_view_search.py \
  tests/test_response_search_flow_integration.py -v
```

## 4. Operator Notes

No operator-facing changes.
