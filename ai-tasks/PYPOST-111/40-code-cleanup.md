# PYPOST-111: Code Cleanup

## Changes

- Extracted `PasteJsonFormatWorker` into `paste_json_worker.py` to keep `CodeEditor` focused on
  UI coordination.
- `_looks_like_json` and `_should_format_pasted_json` remain module-level helpers beside the
  threshold constant.
- `make test` and lint pass on touched files.

## Notes

No formatting or structural refactors outside the paste path.
