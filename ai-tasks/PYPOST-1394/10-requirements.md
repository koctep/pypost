# PYPOST-1394: Unified JSON selector path evaluation engine for response masking

## Goals

PyPost supports masking sensitive response fields (such as access tokens, passwords, and API keys) to protect confidential information during API development. This masking functionality operates across two distinct operational boundaries:
1. **MCP Egress Redaction (`SensitiveTextSanitizer`)**: Irreversibly redacts sensitive JSON fields in response payloads before they are returned to AI coding agents via MCP tools.
2. **Interactive GUI Presentation (`ResponseMaskController`)**: Reversibly masks sensitive JSON values (`"***"`) in the desktop response viewer (`ResponseView`) while tracking character token spans to allow interactive click-to-reveal inspection.

Currently, both systems independently implement JSON hierarchy traversal and pattern matching logic for user-configured selector paths (e.g., simple keys like `token`, dot-notation paths like `user.credentials.apiKey`, and wildcard array expressions like `items[*].secret`). While they share a helper for path variant generation (`format_path_variants`), each consumer evaluates selectors independently during recursive node traversal.

The business goals of this task are:
- **Security Parity & Leak Prevention**: Guarantee 100% behavioral consistency between MCP redaction and GUI display. Any field that matches a selector rule in the GUI must match identically in MCP tool output and vice versa, eliminating data leakage risks resulting from divergent selector path evaluations.
- **Maintainability & Extensibility**: Consolidate selector parsing, normalization, wildcard handling, and path matching into a single, canonical engine. Future selector syntax enhancements or optimizations will be implemented once and immediately benefit all consumers.
- **Traversal Performance & Efficiency**: Eliminate redundant string allocations and repetitive path formatting during deep AST traversals, improving responsiveness when processing large response payloads up to the formatting threshold.

## Programming Language

Python 3.10+ (core logic decoupled from UI dependencies; test suites executed via `pytest` and `make`). Documentation and workflow artifacts are written in English Markdown.

## User Stories

- As a **security engineer**, I want MCP output redaction and GUI response masking to evaluate selector rules using identical matching semantics, so that sensitive data hidden in the UI is never accidentally exposed to external AI agents via MCP tools.
- As a **core developer / maintainer**, I want a single unified selector evaluation engine rather than duplicated traversal and pattern-matching implementations across `SensitiveTextSanitizer` and `ResponseMaskController`, so that the codebase is easier to test, maintain, and extend.
- As an **API developer using PyPost**, I want response field masking to evaluate selector paths (`token`, `auth.token`, `items[*].secret`, `data.*.key`) reliably and quickly across nested JSON objects and arrays, without UI lag or memory bloat.
- As a **quality engineer**, I want full regression protection ensuring that all existing selector patterns and consumer behaviors remain 100% backward-compatible across existing unit and integration test suites.

## Definition of Done

- A unified JSON selector path evaluation engine is established in the core layer (`pypost/core/`) with zero UI or graphical library dependencies.
- The engine supports all currently defined selector syntax patterns:
  - Exact key names matching at any nesting depth (e.g., `token`, `password`).
  - Dotted object hierarchy paths (e.g., `user.profile.token`).
  - Array wildcard patterns using bracket or dot notation (e.g., `items[*].secret`, `items.*.secret`, `[*].id`).
  - Graceful ignoring of header-specific selectors (e.g., `header:Authorization`) in JSON body evaluation.
- `SensitiveTextSanitizer` delegates its JSON response field redaction matching to the unified engine while preserving all existing public functions and signatures.
- `ResponseMaskController` (`JsonMaskFormatter`) delegates its selector matching during formatted output generation to the unified engine while preserving token span tracking and click-to-reveal interactions.
- All existing unit tests in `tests/test_sensitive_text_sanitizer.py`, `tests/test_response_mask_controller.py`, and `tests/test_hidden_response_fields_integration_edge_cases.py` pass without regression.
- Dedicated unit tests are added for the unified selector engine covering simple keys, nested paths, array wildcards, empty/invalid payloads, non-container values, deep nesting, and selector normalization.
- Full repository quality gate `make check` (`lint`, `test`, `verify-ai-tasks`) passes cleanly.

## Task Description

### Problem Statement

In the current implementation of response field masking (established in parent epic PYPOST-1312 and child stories PYPOST-1377 through PYPOST-1380):
- `pypost/core/sensitive_text_sanitizer.py` implements `_redact_node()`, recursively walking dictionaries and lists while constructing candidate path strings (`format_path_variants`) to match against configured selectors.
- `pypost/ui/widgets/response_mask_controller.py` implements `JsonMaskFormatter` (`_format_value()`, `_format_dict()`, `_format_list()`), which also traverses dictionaries and lists and calls `format_path_variants()` to determine if a node should be masked with `"***"` and recorded as a `MaskedTokenSpan`.

This duplication presents several concerns:
1. **Divergence Risk**: Because traversal and matching logic are separated across two files, future modifications or bug fixes applied to one component may not be mirrored in the other, leading to privacy discrepancies between the GUI and MCP.
2. **Computational Redundancy**: On every key in every dictionary traversed, `format_path_variants()` constructs multiple string variations (`key`, `full_dot`, `shorthand_dot`, `wildcard_dot`) and performs set lookups. For large JSON trees, this creates unnecessary allocations and CPU overhead.
3. **Architectural Coupling**: GUI formatting components directly import and rely on internal utility functions from the MCP text sanitizer rather than delegating to a dedicated core path-evaluation service.

### Scope

#### In Scope
- Designing and implementing a unified JSON selector path evaluation engine in `pypost/core/`.
- Normalizing and parsing selector expressions (simple keys, dotted paths, array wildcards).
- Evaluating whether a given node in a JSON AST/hierarchy matches any configured selector.
- Providing traversal/visitor support suitable for both:
  - Irreversible value replacement (MCP redaction).
  - Formatted text generation with span tracking (GUI click-to-reveal).
- Integrating the engine into `SensitiveTextSanitizer` (`pypost/core/sensitive_text_sanitizer.py`).
- Integrating the engine into `ResponseMaskController` (`pypost/ui/widgets/response_mask_controller.py`).
- Maintaining backward compatibility for existing helper functions (`format_path_variants`).
- Adding comprehensive unit tests for selector evaluation edge cases.

#### Out of Scope
- Modifying the UI interaction model (hover cursors, ExtraSelections, mouse click event filters) in `ResponseMaskController`.
- Modifying request persistence models or `RequestEditor` UI for configuring `hidden_response_fields` (completed in PYPOST-1377).
- Introducing full complex JSONPath expressions (e.g., filter expressions `[?(@.price < 10)]`, slice expressions `[0:5]`, recursive descend `..`).
- Altering header redaction behavior or non-JSON payload handling (plain text, XML, HTML).

## Functional Requirements

- **FR-1: Selector Normalization & Pre-compilation**: The engine must accept an iterable of selector strings, trim whitespace, ignore empty strings, filter out non-body selectors (e.g., `header:*`), and compile the remaining selectors into a structured query representation for efficient matching.
- **FR-2: Key-Level Matching**: When given a simple field name without path separators (e.g., `token`), the engine must match that field name regardless of its depth or location in the JSON hierarchy.
- **FR-3: Exact Hierarchical Path Matching**: When given a dot-separated selector (e.g., `user.profile.apiKey`), the engine must match only when the exact sequence of ancestor object keys aligns from the root to the target key.
- **FR-4: Array Wildcard Path Matching**: The engine must support matching elements inside arrays using wildcard notation:
  - Bracket wildcard: e.g., `items[*].secret` or `[*].id`.
  - Dot wildcard: e.g., `items.*.secret`.
  - Nested array wildcards: e.g., `matrix[*][*].value` or `groups[*].members[*].token`.
- **FR-5: Visitor / Traversal Extensibility**: The engine must provide a clean traversal or matching mechanism that can be leveraged by both:
  - An in-place or copied data transformer (replacing matched node values with placeholder values for MCP output).
  - A formatted text generator (emitting formatted JSON tokens and recording character offsets for GUI span tracking).
- **FR-6: Backward-Compatible Signatures**: Existing functions (`redact_json_response_fields`, `format_path_variants`) in `sensitive_text_sanitizer.py` must retain their existing signatures and behaviors so external callers remain unaffected.
- **FR-7: GUI Masking Parity**: `JsonMaskFormatter` in `response_mask_controller.py` must produce identical formatted text and `MaskedTokenSpan` coordinates as prior to the refactor.

## Non-Functional Requirements

- **NFR-1 — Performance & Optimization**: Selector path matching must eliminate redundant string formatting allocations on non-matching nodes. Traversal of typical payloads (1 KB – 50 KB) must complete within a few milliseconds, well below interactive UI thresholds.
- **NFR-2 — Resilience & Fault Tolerance**: The engine must safely handle non-container JSON root values (numbers, booleans, strings, null), empty containers (`{}`, `[]`), malformed JSON text, and deeply nested hierarchies without throwing unhandled exceptions.
- **NFR-3 — Zero UI Dependencies**: The core selector engine must reside entirely in `pypost/core/` and have zero imports from `PySide6` or `pypost/ui/`, allowing use in headless services, daemon processes, and MCP servers.
- **NFR-4 — Testability & Coverage**: 100% of selector evaluation code paths and edge cases must be covered by automated tests. Every test must include explicit timeout markers per project testing guidelines.

## Acceptance Criteria

- **AC-1:** The unified selector path engine is located under `pypost/core/` with clear domain separation and no UI dependencies.
- **AC-2:** `SensitiveTextSanitizer.redact_json_response_fields` uses the unified engine to redact matched JSON fields.
- **AC-3:** `ResponseMaskController` (`JsonMaskFormatter`) uses the unified engine to identify masked fields during formatted text generation.
- **AC-4:** All supported selector patterns (simple key, dotted path, array wildcard notation) match identically across both consumers.
- **AC-5:** No existing tests fail; existing test assertions for MCP redaction and GUI masking remain green.
- **AC-6:** Dedicated unit tests validate the unified selector engine across positive matches, negative matches, array wildcards, root containers, empty selectors, and malformed inputs.
- **AC-7:** The complete quality check `make check` passes with zero lint, test, or artifact verification errors.

## Constraints and Assumptions

- **Immutable Raw Data**: Neither MCP redaction nor GUI mask formatting may mutate the raw response payload or `ResponseData` stored in memory.
- **Maximum Payload Sizing**: In the GUI, interactive masking is bypassed for payloads exceeding 100 KB (`LARGE_DOC_CHAR_THRESHOLD`); the selector engine should nonetheless maintain linear $O(N)$ traversal efficiency regardless of payload size.
- **Header Selectors**: Header selectors (`header:<name>`) are exclusively evaluated against HTTP response headers during MCP sanitization and are excluded from JSON body selector evaluation.

## Main Entities and Interactions

| Entity | Role in System | Key Responsibilities |
| --- | --- | --- |
| **Selector Expression** | User Configuration | Represents a field or path pattern configured in `hidden_response_fields` (e.g. `apiKey`, `user.token`, `items[*].id`). |
| **Selector Path Engine** | Core Domain Engine | Parses and compiles selector expressions; evaluates whether an AST path matches configured selectors during JSON traversal. |
| **MCP Redaction Transformer** | Security Consumer | Traverses JSON data and uses the engine to replace matching field values with `"***"` before sending output to MCP tools. |
| **GUI Mask Formatter** | UI Presentation Consumer | Traverses JSON data and uses the engine to emit pretty-printed JSON while capturing character offsets (`MaskedTokenSpan`) for click-to-reveal interactions. |
| **MaskedTokenSpan** | UI State Container | Stores start/end character offsets, raw value, masked value, and reveal state for interactive toggling in `FoldableCodeView`. |

## Evidence and Traceability

| Source | Reference / Context | Requirement Trace |
| --- | --- | --- |
| Parent Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) | Response field masking for GUI and MCP | Goals, DoD |
| [PYPOST-1380 Technical Debt](file:///home/src/ai-tasks/PYPOST-1380/60-tech-debt.md#L24-L36) | Code quality finding recommending unified selector engine extraction | Goals, FR-1, FR-5, NFR-1 |
| [`sensitive_text_sanitizer.py`](file:///home/src/pypost/core/sensitive_text_sanitizer.py#L79-L164) | Existing `redact_json_response_fields` and `_redact_node` implementation | FR-2, FR-3, FR-4, FR-6 |
| [`response_mask_controller.py`](file:///home/src/pypost/ui/widgets/response_mask_controller.py#L40-L133) | Existing `JsonMaskFormatter` implementation | FR-2, FR-3, FR-4, FR-7 |
| [`tests/test_hidden_response_fields_integration_edge_cases.py`](file:///home/src/pypost/tests/test_hidden_response_fields_integration_edge_cases.py) | End-to-end regression tests verifying masking parity | AC-4, AC-5 |

## Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| --- | --- | --- |
| Subtle discrepancy in wildcard matching between MCP and GUI | Potential security leak or UI formatting mismatch | Establish a unified test suite verifying both consumers against a comprehensive matrix of nested and array structures. |
| Performance regression during deep AST traversal | GUI responsiveness degradation on medium/large responses | Compile selectors into structured token hierarchies or sets upfront; avoid repetitive string formatting per node. |
| Breaking changes to legacy helper functions | Broken external scripts or dependent tests | Preserve `format_path_variants()` in `sensitive_text_sanitizer.py` as a backward-compatible wrapper. |

## Q&A

- **Q: Why is an AST-based selector engine needed instead of using a standard third-party JSONPath library?**  
  **A:** PyPost maintains strict dependency hygiene and requires zero external runtime dependencies for response masking. Furthermore, PyPost selector syntax has distinct semantics: simple keys match at any depth (convenient for API tokens), dot notation matches explicit ancestor chains, and array wildcards (`[*]`) span collections. A lightweight, zero-dependency native engine avoids bloat, security audit risks, and aligns with existing project patterns.

- **Q: Does this task alter how `hidden_response_fields` are configured or persisted?**  
  **A:** No. Configuration models (`RequestData.hidden_response_fields`), persistence serialization, and UI editor tabs were completed in PYPOST-1377 and remain unchanged.

- **Q: How does this engine handle `header:` selectors?**  
  **A:** Header selectors (e.g. `header:Authorization`) are filtered out during selector normalization because they apply to HTTP response headers rather than JSON body content.

- **Q: Will existing test cases need to be rewritten?**  
  **A:** No. All existing tests in `test_sensitive_text_sanitizer.py`, `test_response_mask_controller.py`, and `test_hidden_response_fields_integration_edge_cases.py` must pass unmodified to confirm complete backward compatibility.
