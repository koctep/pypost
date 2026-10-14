# PYPOST-1376: Developer Documentation

## Updates

- **`doc/dev/hidden_response_fields.md`**:
  - Authored comprehensive developer documentation summarizing the architecture, security boundaries, and decomposition for Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) ("Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output").
  - Detailed the child task execution sequence and sprint roadmap:
    - `PYPOST-1377` (MASK-1, 3 SP): Request model, persistence, and RequestEditor UI for hidden response fields
    - `PYPOST-1378` (MASK-2, 3 SP): Permanent MCP output masking for hidden response fields
    - `PYPOST-1379` (MASK-3, 5 SP): Interactive click-to-reveal response masking in GUI ResponseView
    - `PYPOST-1380` (MASK-4, 3 SP): Integration test suite, edge-case coverage, and developer documentation
  - Documented core architectural specifications:
    - **`RequestData` Schema & Tab Copy Isolation**: Adding `hidden_response_fields: list[str]` with backward-compatible default, `copy_request_for_isolated_tab` deep copy, and `persisted_fields_equal` dirty tracking.
    - **Fail-Closed MCP Permanent Masking Boundary**: Recursive JSON sanitization in `McpResponseSanitizer` replacing values with `***`, irreversible redaction with zero reveal mechanism for AI agents, and preserving unmodified raw `ResponseData` in memory and history.
    - **GUI Click-to-Reveal Token Span Model**: `ResponseMaskController` tracking `MaskedTokenSpan` offsets in `FoldableCodeView` (`QPlainTextEdit`), in-place cursor toggling, coexistence with `JsonHighlighter` and search/match counting, code folding preservation, and large-document (>100 KB) bypass.
    - **Selector Syntax**: Simple key names, dot-notation paths, array wildcard notation, and response header selectors.
- **`doc/dev/README.md`**:
  - Registered `[Hidden Response Fields Architecture and Decomposition (PYPOST-1312 / PYPOST-1376)](hidden_response_fields.md)` under the `### Request and response UI` section in the Table of Contents.

## Overview for Maintainers & Downstream Implementers

### Downstream Child Task Ownership

1. **MASK-1 ([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377))**: Extends `RequestData` in `pypost/models/models.py`, adds `hidden_response_fields` to `_PERSISTED_FIELD_NAMES` in `pypost/core/request_persisted_fields.py`, and creates the selector configuration table in `RequestWidget`.
2. **MASK-2 ([PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378))**: Hooks into `format_structured_tool_result` in `pypost/core/mcp_server_impl.py` and `McpResponseSanitizer.sanitize_body`, ensuring permanent masking (`***`) with zero reveal endpoints.
3. **MASK-3 ([PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379))**: Coordinates GUI presentation in `pypost/ui/widgets/response_view.py` and `FoldableCodeView`, using mouse click detection to toggle masked token spans in-place.
4. **MASK-4 ([PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380))**: Builds end-to-end integration contracts across GUI and MCP boundaries in `tests/test_response_field_masking_e2e.py` and verifies edge cases.

## Traceability & References

- Epic Decomposition Notes: [`ai-tasks/PYPOST-1312/decomposition-notes.md`](../PYPOST-1312/decomposition-notes.md)
- Planning Task Requirements: [`ai-tasks/PYPOST-1376/10-requirements.md`](10-requirements.md)
- Planning Task Architecture: [`ai-tasks/PYPOST-1376/20-architecture.md`](20-architecture.md)
- Planning Task Roadmap: [`ai-tasks/PYPOST-1376/00-roadmap.md`](00-roadmap.md)
- Sensitive Data Masking Policy: [`doc/dev/sensitive_data_masking_policy.md`](../../doc/dev/sensitive_data_masking_policy.md)
- RequestData Copy Policy: [`doc/dev/request_data_copy_policy.md`](../../doc/dev/request_data_copy_policy.md)

## Verification

Run static analysis and task artifact verification:

```bash
make lint
make verify-ai-tasks
```
