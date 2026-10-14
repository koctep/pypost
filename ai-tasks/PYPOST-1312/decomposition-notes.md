# PYPOST-1312 Decomposition Notes: Hide Selected Response Fields

## Epic Overview

**Epic Key**: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)  
**Summary**: Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output  
**Sprint**: 2032 (Hide Selected Response Fields)  

### Problem Statement

Users often work with APIs that return sensitive information (e.g., authentication tokens, API keys, passwords, session identifiers, PII). When executing requests:
1. **Desktop GUI Exposure**: Sensitive fields are displayed in plain text in the response viewer (`ResponseView`), creating risk during demos, screen-shares, or casual observation. Users need sensitive response fields masked by default, with a fast, intuitive click-to-reveal interaction.
2. **MCP Tool Agent Leakage**: When requests are exposed as MCP tools to AI coding agents, returning sensitive response fields in full can compromise security. Sensitive fields must be permanently masked in MCP tool outputs, with zero possibility for an agent to reveal them through parameters or dedicated tools.
3. **Data Integrity**: Masking must be strictly a presentation-layer and output-formatting operation. Raw response data stored in memory or history must remain intact and unmodified.

### Scope and Constraints

- **Scope & Selector Syntax**: The configuration specifies which response fields to hide (key names / JSONPath / header selectors, with JSON body keys as primary scope).
- **GUI Masking**: Masked values in `ResponseView` are clickable to toggle/reveal the real value. Must seamlessly coexist with JSON syntax highlighting, search/find, "Set Variable" from selection, code folding, streaming body appending, and large-document fallback. GUI currently does not display response headers; masking applies to body content.
- **MCP Output Masking**: Hook into `McpResponseSanitizer` and `format_structured_tool_result`. Values are permanently masked (e.g., `***`); no reveal mechanism exists.
- **Granularity & Sizing**: Sized strictly into small, deliverable child tasks (each ≤ 5 Story Points).
- **Sprint Alignment**: All child tasks created from this epic belong to **Sprint 2032** ("Hide Selected Response Fields").

---

## Scope Breakdown and Slicing Strategy

To deliver epic PYPOST-1312 iteratively with rigorous testing at each layer and zero monolithic risk, the epic is decomposed into four focused child stories:

| Child ID | Provisional Key | Summary | SP | Dependencies | Focus Area | Sprint |
| --- | --- | --- | --- | --- | --- | --- |
| [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) | **MASK-1** | Request model, persistence, and RequestEditor UI for hidden response fields | 3 SP | None | Data models, serialization, tab isolation, and editor UI | Sprint 2032 |
| [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) | **MASK-2** | Permanent MCP output masking for hidden response fields | 3 SP | PYPOST-1377 | McpResponseSanitizer, tool result formatting, security boundary | Sprint 2032 |
| [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) | **MASK-3** | Interactive click-to-reveal response masking in GUI ResponseView | 5 SP | PYPOST-1377 | GUI widget rendering, click-to-reveal, highlighter/search coexistence | Sprint 2032 |
| [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) | **MASK-4** | Integration test suite, edge-case coverage, and developer documentation | 3 SP | PYPOST-1377, PYPOST-1378, PYPOST-1379 | End-to-end contracts, edge cases, fixtures, and developer docs | Sprint 2032 |

**Total Estimated Effort**: 14 SP across 4 child stories (all ≤ 5 SP, using standard Fibonacci estimates 3, 3, 5, 3).

---

## Detailed Child Task Descriptions

### MASK-1 -> PYPOST-1377: Request model, persistence, and RequestEditor UI for hidden response fields

- **Issue Key**: [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377)
- **Parent Epic**: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)
- **Sprint**: Sprint 2032 (Hide Selected Response Fields)
- **Estimated Effort**: 3 SP
- **Summary**: Request model, persistence, and RequestEditor UI for hidden response fields

---

### MASK-2 -> PYPOST-1378: Permanent MCP output masking for hidden response fields

- **Issue Key**: [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378)
- **Parent Epic**: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)
- **Sprint**: Sprint 2032 (Hide Selected Response Fields)
- **Estimated Effort**: 3 SP
- **Dependencies**: PYPOST-1377

---

### MASK-3 -> PYPOST-1379: Interactive click-to-reveal response masking in GUI ResponseView

- **Issue Key**: [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379)
- **Parent Epic**: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)
- **Sprint**: Sprint 2032 (Hide Selected Response Fields)
- **Estimated Effort**: 5 SP
- **Dependencies**: PYPOST-1377

---

### MASK-4 -> PYPOST-1380: Integration test suite, edge-case coverage, and developer documentation

- **Issue Key**: [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)
- **Parent Epic**: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)
- **Sprint**: Sprint 2032 (Hide Selected Response Fields)
- **Estimated Effort**: 3 SP
- **Dependencies**: PYPOST-1377, PYPOST-1378, PYPOST-1379
- **Summary**: Integration test suite, edge-case coverage, and developer documentation
- **Scope**:
  - **End-to-End Contract Testing**: Automated test verifying the full lifecycle: request created with hidden fields -> HTTP request executed -> GUI response view displays masked value with click-to-reveal -> MCP tool execution returns permanently masked value.
  - **Edge-Case Matrix**:
    - Array of objects containing masked fields.
    - Deeply nested keys and duplicate key names at different hierarchy levels.
    - Non-string values (numbers, booleans, nulls, arrays).
    - Non-JSON responses (HTML, plain text, XML) with hidden fields configured.
    - Empty body responses (204 No Content, empty string).
    - Concurrent tabs with different hidden field configurations.
  - **Developer Documentation**: Add documentation in `doc/dev/` describing the response field masking architecture, selector semantics, MCP security boundaries, and copy policy considerations.
  - **Example Collections**: Add or update reference collection fixtures with examples of response field masking.
- **Acceptance Criteria**:
  1. End-to-end integration tests verify both GUI click-to-reveal and MCP permanent masking on the same request configuration.
  2. Edge cases (malformed JSON, non-JSON bodies, empty responses, nested keys) pass with 100% test reliability.
  3. Developer documentation is published under `doc/dev/`.
  4. All tests pass under `make test` with required timeout markers.
- **Primary Deliverables**: `tests/test_response_field_masking_e2e.py`, `doc/dev/response_field_masking.md`, example collection fixtures.

---

## Dependency Graph and Execution Sequence

```
      [MASK-1: Model, Persistence & RequestEditor UI] (3 SP)
                      /                \
                     /                  \
                    v                    v
  [MASK-2: MCP Permanent Mask] (3 SP)   [MASK-3: GUI Click-to-Reveal] (5 SP)
                    \                    /
                     \                  /
                      v                v
      [MASK-4: Integration Tests & Dev Docs] (3 SP)
```

1. **Phase 1**: Execute **MASK-1** (foundation: model schema, persistence, tab copy, editor UI).
2. **Phase 2 (Parallelizable)**:
   - Execute **MASK-2** (MCP output sanitization & permanent masking).
   - Execute **MASK-3** (GUI response view masked presentation & click-to-reveal).
3. **Phase 3**: Execute **MASK-4** (end-to-end integration contracts, edge-case verification, developer docs).

---

## Sprint 2032 Allocation Summary

All child tasks are strictly assigned to **Sprint 2032** ("Hide Selected Response Fields") and linked to parent epic **PYPOST-1312**:

| Task | Story Points | Assignee Sprint | Hierarchy |
| --- | --- | --- | --- |
| MASK-1 | 3 SP | Sprint 2032 | Child of PYPOST-1312 |
| MASK-2 | 3 SP | Sprint 2032 | Child of PYPOST-1312 |
| MASK-3 | 5 SP | Sprint 2032 | Child of PYPOST-1312 |
| MASK-4 | 3 SP | Sprint 2032 | Child of PYPOST-1312 |
| **Total** | **14 SP** | **Sprint 2032** | **4 child stories** |

---

## Architectural Refinements (from Step 2 Architecture)

1. **Selector Syntax Scope & Semantics:**
   - **Simple Key Names:** `token`, `password`, `secret` — recursively matches JSON object keys at any nesting depth. Default matching is exact match.
   - **Dot-Notation & Wildcards:** `auth.token`, `items[*].secret` — precision matching for deep paths or collections of records.
   - **Header Selectors:** `header:Authorization` — targets HTTP response headers in MCP tool output. GUI currently does not render headers in `ResponseView`, so GUI header masking is deferred.

2. **Security Boundary Distinction:**
   - **MCP Tool Output (Irreversible):** Sanitized in `format_structured_tool_result` via `McpResponseSanitizer.sanitize_body`. Values matching hidden selectors are permanently replaced with `***`. Zero reveal tools, parameters, or endpoints are exposed to the calling agent.
   - **GUI ResponseView (Reversible):** Formatted with `ResponseMaskController` tracking token character spans in `FoldableCodeView`. Left-clicking a masked token toggles between masked placeholder (`"***"`) and raw value.
   - **Underlying Response Immutability:** Neither GUI masking nor MCP output formatting mutates the raw in-memory `ResponseData` stored in `ExecutionResult.response` or request history.

3. **GUI Interaction & Subsystem Coexistence:**
   - **JsonHighlighter Coexistence:** Masked string literals (`"***"`) match standard JSON string regex rules. When a value is unmasked via `QTextCursor.insertText`, Qt's syntax highlighter automatically re-highlights the modified text block.
   - **Search & Match Counting:** Search via `self.body_view.find(...)` and match counting (`_count_matches`) continue to work seamlessly. Unmasked values become searchable immediately upon reveal.
   - **Code Folding Integrity:** In-place scalar token toggling alters character count on a single line but does not alter indentation or line count, preserving fold region structure. `ensure_scanned()` is invoked after document mutations.
   - **Context Menu Actions:** "Set Variable" and "Copy" on selected text operate normally. Selecting a revealed token and choosing "Set Variable" emits `variable_set_requested` with the true secret value.
   - **Large Document Threshold:** For documents exceeding `LARGE_DOC_CHAR_THRESHOLD` (100 KB), heavy token tracking is bypassed to guarantee GUI thread responsiveness.

