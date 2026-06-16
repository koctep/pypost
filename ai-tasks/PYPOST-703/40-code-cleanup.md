# PYPOST-703: Code Cleanup

No lint issues introduced. Sanitizer is a pure module with no UI or Qt dependencies.
Existing `format_structured_tool_result` callers in tests pass without env/hidden args
(backward compatible defaults).
