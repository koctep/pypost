# PYPOST-399: Code Cleanup

## Static analysis

- `read_lints` on `tests/test_json_highlighter.py` — no issues.

## Formatting

- Line length ≤ 100 characters maintained.
- Module `pytestmark = pytest.mark.timeout(60)` retained.

## Cleanup actions

| Item | Action |
| ---- | ------ |
| Unused imports | None added |
| Dead code | None |
| Debug output | None |
| Duplicate helpers | Reused `_hex_color_at` / `_edit_with_highlighted` |

## Test run

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

All tests pass.
