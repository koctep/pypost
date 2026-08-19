# Requirements: PYPOST-1090

## Summary

Clarify `mcp_arg_count` DEBUG-log semantic shift in `_build_execution_variables` after PYPOST-1054 default-injection.

## Background & Motivation

In `pypost/core/mcp_server_impl.py::_build_execution_variables`, the pre-existing `mcp_execution_variables_merged` DEBUG log line emitted `mcp_arg_count`. Following PYPOST-1054's parameter defaulting, `mcp_arg_count` counts post-merge/post-default arguments (`len(merged_args)`), while `defaults_applied_count` records how many defaults were injected.

The raw caller-supplied arg count is equal to `mcp_arg_count - defaults_applied_count`.

## Requirements

1. Add explicit comment in `pypost/core/mcp_server_impl.py::_build_execution_variables` explaining the post-default count semantics and how the raw count is derived.
2. Update developer documentation in `doc/dev/mcp_integration.md` to resolve the follow-up note.
3. Ensure unit tests and lint pass cleanly.
