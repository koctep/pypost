# Hidden Response Fields Architecture and Decomposition (PYPOST-1312 / PYPOST-1376)

## Overview

Modern API workflows frequently handle sensitive information such as authentication credentials,
API tokens, passwords, session identifiers, and Personally Identifiable Information (PII). When
executing requests in PyPost, these fields pose dual security risks:

1. **Desktop GUI Exposure**: Displaying secrets in plain text within `ResponseView` creates risk during
   screen sharing, presentations, or shoulder-surfing. Users require sensitive response fields to be
   masked by default with an intuitive, in-place click-to-reveal mechanism.
2. **MCP Tool Agent Leakage**: When requests are exposed as Model Context Protocol (MCP) tools for AI
   coding agents, returning raw credentials can leak secrets into LLM contexts or remote logs. MCP outputs
   require permanent, irreversible masking with zero reveal capabilities exposed to agents.
3. **Data Integrity**: Masking is strictly a presentation and serialization transformation. Raw
   in-memory responses (`ResponseData`) and history records remain pristine for scripting and auditing.

Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) addresses these requirements. Planning
task [PYPOST-1376](https://pypost.atlassian.net/browse/PYPOST-1376) established the architecture, selector
specifications, security boundaries, and decomposition into four focused child stories scheduled for Sprint 2032.

---

## Child Tasks Breakdown & Implementation Roadmap

To avoid monolithic implementation risks and adhere to repository sizing standards (all child stories
≤ 5 Story Points using the Fibonacci scale), Epic PYPOST-1312 is decomposed into four distinct stories
under active **Sprint 2032** ("Hide Selected Response Fields"):

| Child Key | Provisional ID | Summary | SP | Dependencies | Primary Layer / Area |
| :--- | :---: | :--- | :---: | :---: | :--- |
| [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) | **MASK-1** | Request model, persistence, and RequestEditor UI for hidden response fields | 3 | None | Data models, tab isolation, serialization, editor UI |
| [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) | **MASK-2** | Permanent MCP output masking for hidden response fields | 3 | PYPOST-1377 | McpResponseSanitizer, tool serialization, security boundary |
| [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) | **MASK-3** | Interactive click-to-reveal response masking in GUI ResponseView | 5 | PYPOST-1377 | GUI widget rendering, click detection, highlighter coexistence |
| [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) | **MASK-4** | Integration test suite, edge-case coverage, and developer documentation | 3 | PYPOST-1377, 1378, 1379 | End-to-end contracts, edge cases, fixtures, documentation |

**Total Estimated Effort**: 14 SP across 4 stories.

### Execution Sequence

```
      [MASK-1: Model, Persistence & RequestEditor UI] (3 SP)
                      /                \
                     /                  \
                    v                    v
  [MASK-2: MCP Permanent Mask] (3 SP)   [MASK-3: GUI Click-to-Reveal] (5 SP)
                    \                    /
                      \                /
                        v            v
      [MASK-4: Integration Tests & Dev Docs] (3 SP)
```

1. **Phase 1 (Foundation)**: Execute **MASK-1** ([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377)) to establish the `hidden_response_fields` model attribute, persistence round-tripping, tab isolation copying, and editor configuration UI.
2. **Phase 2 (Parallel Implementation)**:
   - Execute **MASK-2** ([PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378)) for server-side irreversible MCP output sanitization.
   - Execute **MASK-3** ([PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379)) for desktop GUI click-to-reveal presentation in `ResponseView`.
3. **Phase 3 (Verification & Documentation)**: Execute **MASK-4** ([PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)) to build end-to-end integration contracts across GUI and MCP boundaries, edge-case test matrices, and reference collections.

---

## Architectural Specifications

### 1. RequestData Schema Extension and Tab Copy Isolation (MASK-1)

The configuration of which response fields to hide lives as part of the request definition:

- **Model Extension (`pypost/models/models.py`)**:
  ```python
  class RequestData(BaseModel):
      ...
      hidden_response_fields: list[str] = Field(default_factory=list)
  ```
  Using `Field(default_factory=list)` guarantees backward compatibility: existing saved collections, test fixtures, or exports lacking this field load cleanly without schema migration errors.
- **Tab Copy Isolation (`pypost/core/request_persisted_fields.py`)**:
  Per the [Request Data Copy Policy](request_data_copy_policy.md), tab isolation deep-copies `RequestData` via `copy_request_for_isolated_tab(data)`. Adding `"hidden_response_fields"` to `_PERSISTED_FIELD_NAMES` ensures:
  1. Configured hidden fields are preserved across tab duplication and workspace state restoration.
  2. Dirty checking (`persisted_fields_equal` and `request_draft_fields_equal`) accurately detects unsaved modifications.
- **Request Editor Configuration UI (`pypost/ui/widgets/request_editor.py`)**:
  `RequestWidget` provides a configuration UI table/list allowing users to add, edit, and remove field selectors for the active request draft.

### 2. Fail-Closed MCP Permanent Masking Boundary (MASK-2)

When requests are invoked via MCP tools, security isolation from external AI agents is paramount:

```
Agent Tool Invocation
  → MCPServerImpl._call_tool_impl
    → RequestService._execute_request_sync
      → ExecutionResult(response)
        → format_structured_tool_result(..., hidden_response_fields=request.hidden_response_fields)
          → McpResponseSanitizer.sanitize_body
            → sensitive_text_sanitizer.redact_json_response_fields
              → Irreversible Output with "***"
```

- **Fail-Closed Irreversible Boundary**:
  - Values matching `hidden_response_fields` are permanently replaced with the placeholder `***`.
  - No MCP tool parameter (e.g. `reveal_secrets: bool`) or auxiliary tool is provided to AI agents.
  - Non-JSON payloads or malformed JSON content fallback safely without leaking raw values.
- **Preservation of Internal State**:
  - Masking occurs strictly during tool output serialization in `format_structured_tool_result`.
  - In-memory `ExecutionResult.response` and PyPost history storage remain unmodified.

### 3. GUI Click-to-Reveal Token Span Model in ResponseView (MASK-3)

In desktop GUI mode, users need confidentiality during screen sharing while retaining full interactive access to response data:

```
display_response(response, hidden_fields)
  → ResponseMaskController.format_masked_json(raw_json, hidden_fields)
    → FoldableCodeView.setPlainText(masked_json)
      → JsonHighlighter highlights "***" as valid string token
        → User left-clicks on masked token
          → ResponseMaskController.handle_click(char_pos)
            → In-place text toggle via QTextCursor ("***" <-> raw_value)
```

- **Token Span Management (`ResponseMaskController`)**:
  - Maintains `MaskedTokenSpan` records tracking character ranges `[start_pos, end_pos]`, raw secret values, placeholder values (`"***"`), and toggle state (`is_revealed`).
  - Detects click events in `FoldableCodeView` (`QPlainTextEdit`) via `cursorForPosition(event.pos())` and maps coordinates to token ranges.
- **Subsystem Coexistence**:
  - **Syntax Highlighting (`JsonHighlighter`)**: Masked tokens formatted as `"***"` comply with standard JSON string literal regex rules. Toggling values via `QTextCursor.insertText()` automatically triggers Qt's incremental block re-highlighting without modifying `JsonHighlighter`.
  - **Search & Match Counting**: Search navigation (`self.body_view.find(...)`) and match count calculation (`_count_matches`) operate consistently. Revealed tokens become searchable immediately upon unmasking.
  - **Code Folding Integrity**: In-place replacement of scalar tokens alters single-line character lengths without altering line counts or indentation structures, preserving `FoldController` block folding boundaries.
  - **Context Menu Actions**: Selecting text and using context menu actions ("Set Variable", "Copy") operates seamlessly; selecting an unmasked token and choosing "Set Variable" emits `variable_set_requested` with the true secret value.
  - **Large Document Bypass**: Payloads exceeding `LARGE_DOC_CHAR_THRESHOLD` (100 KB) bypass complex token tracking to maintain UI thread responsiveness.

### 4. Selector Syntax & Matching Rules

The selector engine supports four syntax formats:

| Selector Format | Pattern | Example | Semantics |
| :--- | :--- | :--- | :--- |
| **Simple Key** | `<key>` | `token`, `password`, `secret` | Matches JSON keys with this exact name at any nesting depth. |
| **Dot-Notation Path** | `<parent>.<child>` | `auth.token`, `data.user.secret` | Matches exact hierarchical object paths. |
| **Array Wildcard Path** | `<array>[*].<field>` | `users[*].email`, `items[*].secret` | Matches specific fields across array elements. |
| **Header Selector** | `header:<Name>` | `header:Authorization` | Targets HTTP response headers for MCP sanitization. |

---

## Comparison: GUI vs MCP Masking

| Dimension | GUI ResponseView | MCP Server Output |
| :--- | :--- | :--- |
| **Consumer** | Human developer via desktop GUI | External AI coding agent via MCP protocol |
| **Threat Model** | Visual observation, screen sharing, shoulder-surfing | Agent context ingestion, prompt injection, log leakage |
| **Reversibility** | **Reversible**: click-to-reveal toggle on demand | **Irreversible**: permanent redaction with `***` |
| **Reveal Capability** | Left-click on token span in `FoldableCodeView` | **None**: zero reveal parameters or tools |
| **Rendering** | Interactive `QPlainTextEdit` with syntax highlights | Formatted JSON string in MCP `TextContent` |
| **Underlying Data** | In-memory `ResponseData` remains unmutated | In-memory `ExecutionResult.response` remains unmutated |

---

## References

- Epic Decomposition Notes: [`ai-tasks/PYPOST-1312/decomposition-notes.md`](../../ai-tasks/PYPOST-1312/decomposition-notes.md)
- Step 2 Architecture Design: [`ai-tasks/PYPOST-1376/20-architecture.md`](../../ai-tasks/PYPOST-1376/20-architecture.md)
- Sensitive Data Masking Policy: [`doc/dev/sensitive_data_masking_policy.md`](sensitive_data_masking_policy.md)
- RequestData Copy Policy: [`doc/dev/request_data_copy_policy.md`](request_data_copy_policy.md)
- MCP Integration Guide: [`doc/dev/mcp_integration.md`](mcp_integration.md)
