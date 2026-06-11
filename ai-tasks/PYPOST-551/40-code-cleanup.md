# PYPOST-551: Code Cleanup (Step 4)

## Changes

- Extracted shared Streamable HTTP wiring to `pypost/core/mcp_streamable_http.py`.
- Moved legacy SSE setup in `MCPServerImpl` to `_create_sse_app()` to keep `create_app()` focused.
- Removed redundant comments; aligned docstrings with Streamable HTTP URLs.

## Verification

- [x] `flake8` on changed modules (via targeted lint)
- [x] Line length within 100 characters
- [x] No unused imports in changed files

## Worklog

role: execution, step: 4, step_name: Code Cleanup, tokens_used: (subagent aggregate)
