# PYPOST-517: Architecture

Add `TestFoldRemappingAfterEdits` to `tests/test_code_editor_folding.py` with helper
`_replace_once` for surgical document edits. Call `fold_controller()._run_scan()` after each
edit (same pattern as existing folding tests).
