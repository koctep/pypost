# PYPOST-516: Code Cleanup

- New test file follows existing `test_request_editor_*.py` conventions (`_get_app`, tearDown).
- Reuses `CodeEditor` public API and `_line_number_area` as in `test_code_editor.py`.
- No lint issues introduced; line length within 100 characters.
