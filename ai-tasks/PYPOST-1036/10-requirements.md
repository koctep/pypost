# PYPOST-1036: Expand safe-path grammar edge locks for dotted template identifiers

## Goals

Template expressions in PyPost allow dotted identifiers to reference nested variables (such as `mcp.request.<param>`) in both standalone expressions and function arguments. To protect the application runtime and enforce strict input validation, the grammar must maintain precise boundary locks.

This task expands the behavioral requirements and acceptance criteria for dotted template path validation:
1. Enforce strict syntax boundaries: reject malformed dotted paths with leading dots, trailing dots, empty segments (consecutive dots), and invalid segment characters.
2. Enforce sandbox security: reject any dotted path where any child/attribute segment begins with an underscore (e.g., `_private`, `__dict__`, `__globals__`, `__class__`), preventing unauthorized access to object internals and private attributes.
3. Validate safe deep navigation: ensure legitimate nested variable paths of arbitrary depth (3 or more segments) validate reliably and consistently.
4. Establish comprehensive test locking to document grammar rules and prevent regressions in future template engine modifications.

**Programming language:** Python

## User Stories

- As a **security-conscious operator**, I want the template resolver to strictly reject any dotted path that attempts to access private or dunder attributes on objects (e.g. `mcp.request._private`, `data._secret`, `config.__dict__`), so that object introspection and potential sandbox escapes remain blocked.
- As a **collection author**, I want clear and consistent syntax validation that rejects malformed expressions (such as leading dots, trailing dots, or double dots) with syntax errors so I can quickly identify and fix template typos.
- As an **integrator**, I want deeply nested safe paths (e.g. `payload.user.contact.address.city`) to validate successfully in both standalone template expressions and catalog function arguments.
- As a **maintainer**, I want an automated test suite explicitly locking all valid and invalid grammar edge cases, ensuring that future grammar or tokenizer changes cannot accidentally weaken security or break deep path resolution.

## Definition of Done

- [ ] Standalone template expressions with leading dots (e.g. `{{ .mcp.request }}`) are rejected as invalid syntax.
- [ ] Standalone template expressions with trailing dots (e.g. `{{ mcp.request. }}`) are rejected as invalid syntax.
- [ ] Standalone template expressions with empty segments / consecutive dots (e.g. `{{ mcp..request }}`) are rejected as invalid syntax.
- [ ] Standalone template expressions containing underscore-prefixed child/attribute segments (e.g. `{{ mcp.request._private }}`, `{{ data._hidden.val }}`, `{{ root.__dict__ }}`) are rejected as invalid syntax.
- [ ] Function arguments with leading dots, trailing dots, empty segments, or underscore-prefixed attribute segments are rejected as invalid argument errors naming the enclosing function.
- [ ] Deep-but-safe dotted paths with multiple valid segments (e.g. `a.b.c.d.e`) validate successfully in standalone expressions and function arguments.
- [ ] Root-level identifier rules continue to permit valid leading-underscore variable names (e.g. `_var`, `_context.field`) while still rejecting child attribute underscores (e.g. `_context._private`).
- [ ] Automated unit test suites under `tests/` cover all specified edge cases with explicit pytest timeout markers.

## Task Description

**Problem:** Following the introduction of dotted variable path support in PYPOST-1033, technical debt item TD-3 identified that while `__class__` and basic dotted paths were tested, other grammar edge cases and private attribute access patterns were not comprehensively locked with unit tests. Specifically, leading/trailing dots, empty segments, and general underscore-leading attribute segments (e.g., `_private`, `__dict__`, `__globals__`) across varying path depths require explicit edge locks.

**Business outcome:** Ensure reliable, secure, and well-documented template expression validation that prevents template injection/escape vectors and provides predictable syntax error behavior for template authors.

### In Scope

- Specification and locking of grammar edge cases for dotted identifiers in template expressions.
- Verification of invalid syntax rejections for leading dots, trailing dots, consecutive dots, and invalid characters.
- Verification of safety rejections for any non-root segment with a leading underscore (`._*`).
- Verification of successful validation for deep-but-safe multi-segment paths.
- Test coverage for both standalone expressions (`{{ path }}`) and function arguments (`{{ func(path) }}`).

### Out of Scope

- Modifying Jinja runtime rendering behavior or template evaluation engines outside the expression resolver contract.
- Adding new catalog functions or expanding the standard function registry.
- Changing MCP tool definitions or adding new Jira MCP tools.
- Modifying UI hover / variable preview behavior.

## Functional Requirements

- **Leading / Trailing Dot Rejection:**
  - Any expression containing a leading dot (e.g., `.path`, `.a.b`) must fail validation.
  - Any expression containing a trailing dot (e.g., `path.`, `a.b.`) must fail validation.
- **Empty Segment / Double Dot Rejection:**
  - Any expression containing consecutive dots (e.g., `a..b`, `mcp..request.field`) must fail validation.
- **Underscore Attribute Segment Rejection:**
  - Non-root segments starting with `_` (e.g., `obj._private`, `a.b._c`, `mcp.request.__globals__`) must fail validation.
  - Root segments starting with `_` (e.g., `_local_var`, `_root.subfield`) are permitted as valid root variables, provided subsequent child segments do not start with `_`.
- **Deep Safe Path Acceptance:**
  - Valid multi-segment paths (e.g., `a.b.c`, `a.b.c.d`, `org.dept.team.service.metric`) conforming to safe segment rules must validate successfully.
- **Function Argument Context:**
  - All above edge cases and deep path rules must apply equally when paths are used as arguments inside catalog functions (e.g., `urlencode(a.b.c)` is valid; `urlencode(a._private)` is invalid argument).

## Non-functional Requirements

- **Security:** Strict fail-closed policy preventing access to internal/private object attributes through template expressions.
- **Performance:** Validation must remain linear time and negligible overhead without backtracking vulnerabilities.
- **Maintainability:** Clear, readable test cases documenting the grammar boundaries and expected error codes.
- **Test Integrity:** All newly added test methods or test modules must include explicit pytest timeout markers per testing standards.

## Constraints and Assumptions

- Task type: Debt / Follow-up (Follow-up from PYPOST-1033 TD-3).
- Priority: Low.
- Jira browse: https://pypost.atlassian.net/browse/PYPOST-1036.
- Implementation language: Python.
- Testing standard: Make-only execution (`make test`, `make check`), standard timeouts.

## Main Entities

| Entity | Description |
| --- | --- |
| Template Expression | An expression enclosed in `{{ ... }}` evaluated within collection requests |
| Dotted Identifier Path | A variable reference composed of dot-separated segments (e.g., `mcp.request.id`) |
| Root Segment | The first segment of a dotted path, representing the top-level variable name |
| Attribute Segment | Any subsequent segment following a dot, representing nested property access |
| Unsafe Attribute | An attribute segment beginning with `_` that must be blocked for safety |
| Validation Result | The status (`valid` or `error` with code and function name) returned by the expression resolver |

## Q&A

| Question | Answer |
| --- | --- |
| Why allow leading underscores on the root segment but not on attribute segments? | Root variables like `_ctx` or `_item` are common local variable names in template contexts, but child attribute access like `obj._private` or `obj.__class__` targets object internals and poses security risks. |
| Does this require changing the runtime evaluation engine? | No, this task focuses on locking and validating the grammar rules in the expression resolver to enforce these contracts before template evaluation. |
| How deep can safe paths be? | Safe paths have no arbitrary depth limitation as long as all segments satisfy the safe identifier grammar rules. |
