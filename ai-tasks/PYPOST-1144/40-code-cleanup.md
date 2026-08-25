# PYPOST-1144: Code Cleanup Report

## Linter Fixes

No flake8 issues introduced. `make lint` passes (flake8 on `pypost/`, doc lint on `doc/`).

## Code Formatting

Applied formatting changes:
- [x] PEP 8 line length within 100 characters for modified modules
- [x] Worker docstrings and signal comments match `CollectionImportParseWorker` style
- [x] Type annotations on `StreamExportSnapshot` and worker constructor

## Code Cleanup

Cleanup actions performed:
- Removed synchronous core export calls from `WebSocketStreamView.export_json()` / `export_text()`
- Extracted `_resolve_export_env()` to avoid duplicating presenter/detail-pane env resolution
- Removed unused `export_stream_to_*` imports from `stream_view.py` (worker owns core calls)
- Updated `test_websocket_presenter_env_properties.py` to inspect `_resolve_export_env` after refactor

## Validation Results

Validation results:
- [x] Targeted tests passed (`tests/test_websocket_stream_export_responsiveness.py`)
- [x] Stream view export integration test updated for sequential async completion
- [x] All new tests have explicit module `pytestmark` timeout
- [x] `make lint` passes
- [x] Full `make test`: 263 passed; 5 pre-existing failures unrelated to this task

## Notes

Export busy guard prevents overlapping JSON/text exports; integration tests must wait for each export to finish before starting the next.
