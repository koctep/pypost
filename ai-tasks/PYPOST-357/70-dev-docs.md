# PYPOST-357: Developer Documentation

## Purpose

Document RequestTab-level integration test coverage for response search flow.

## Modified Files

| File | Change |
| ---- | ------ |
| `doc/dev/response_search.md` | Testing section adds integration tests and run command |
| `doc/dev/testing.md` | Cross-link to integration test module |
| `doc/dev/gui_testing.md` | Representative modules table updated |

## Key Takeaways for Developers

- Use `tests/test_response_search_flow_integration.py` when changing `RequestTab` layout or
  `ResponseView` signal wiring after `display_response`.
- Entry points under test: typed search (`textChanged`), Next button, Enter key.
- For ResponseView-only behavior (debounce, case sensitivity, metrics), see
  `tests/test_response_view_search.py`.
