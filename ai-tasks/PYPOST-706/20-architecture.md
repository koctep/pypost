# PYPOST-706: Architecture

Extract `sensitive_text_sanitizer.py`; `SensitiveDataMaskingPolicy` applies heuristics after
rendering. `McpResponseSanitizer` delegates to the same module.
