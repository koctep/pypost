# PYPOST-66: Code Cleanup

## Static analysis

- No new linter issues in `main_window.py` or `main_window_signals.py`.
- `TYPE_CHECKING` guard avoids runtime circular import for `MainWindow` type hint.

## Formatting

- 100-character line limit observed.
- Trailing whitespace removed; final newlines present.

## Tests

- `pytest tests/test_main_window.py tests/test_main_window_signals.py` — 8 passed.
- Related MainWindow e2e/shutdown/encrypted-startup tests — 12 passed combined run.
- Full `make test`: 11 pre-existing failures unrelated to this change (makefile marker version,
  http_client_sse_probe).

## Files touched

| File | Notes |
|------|-------|
| `pypost/ui/main_window_signals.py` | New module |
| `pypost/ui/main_window.py` | Removed `_wire_signals`, `_on_curl_copied` |
| `tests/test_main_window_signals.py` | New |
| `tests/test_*main_window*.py` | Patch target update |
