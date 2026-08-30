# PYPOST-1120: Return structured failed-function provenance from expression resolution for strict rendering

## Goals

When template authors construct request templates for external APIs and MCP services, certain functions (such as integer coercion) enforce strict conversion rules to guarantee that corrupted or invalid values are never dispatched to external endpoints. When an expression containing a strict conversion fails (due to invalid data or malformed expression syntax), the system must reliably fail closed rather than falling back to sending raw unconverted literal text.

Currently, the rendering layer detects whether a strict conversion function failed by inspecting template text using narrow pattern-matching heuristics. This coupling poses business and operational risks:
1. Variations or advancements in expression syntax (whitespace variations, nested function calls, complex parameter formatting) risk evading textual regex heuristics, potentially allowing invalid payloads to reach upstream services.
2. Introducing additional strict validation or conversion functions in the future would require maintaining duplicate regex patterns in the rendering engine, creating maintenance overhead and risk of divergence.

By requiring the expression resolution domain to supply structured failure provenance, the system ensures that template execution reliably detects strict conversion failures across any valid expression syntax, protecting downstream systems while keeping the template architecture extensible and maintainable.

**Programming language:** Python

## User Stories

- As an **MCP client user**, I want requests with failed or malformed conversion expressions to be halted immediately and reliably, so that downstream systems are never invoked with invalid or partially converted data.
- As a **collection author**, I want consistent fail-closed protection regardless of how I format whitespace or nest allowed functions in my template expressions, without subtle regex-matching edge cases.
- As a **maintainer**, I want expression evaluation to communicate failed function details through structured diagnostic provenance, so that adding new conversion functions or expanding expression capabilities does not require brittle regex synchronizations in the rendering layer.

## Definition of Done

- [ ] The expression resolution process yields structured failure provenance identifying the specific function, expression, and failure cause when expression validation or evaluation encounters an error.
- [ ] The strict rendering pipeline determines whether to halt execution based on structured failure provenance rather than relying on textual regex heuristics (`_DIRECT_TO_INT_CALL_RE` and `_STARTED_TO_INT_CALL_RE`).
- [ ] Strict conversion failure behavior ("fail closed" with an execution error) is preserved for all direct, started, and nested strict conversion errors.
- [ ] Safe fallback to literal content remains preserved for non-strict template expressions and unrelated rendering errors where no strict conversion function failed.
- [ ] Whitespace variations, nesting, and formatting variations in expressions are handled predictably by the resolver without heuristic mismatch.
- [ ] Existing documented template expressions, ordinary variable replacements, and conversion semantics continue to behave identically.
- [ ] Automated regression tests verify structured failure detection, strict failure propagation, and compatibility with existing template behaviors.

## Task Description

**Problem:** In PYPOST-1037, strict conversion was introduced to halt HTTP request preparation when integer coercion fails. To avoid widening fallback for unrelated placeholders while catching started or broken `to_int` expressions, the rendering engine introduced ad-hoc regular expressions (`_DIRECT_TO_INT_CALL_RE` and `_STARTED_TO_INT_CALL_RE`). While effective for initial narrow cases, this couples the rendering layer directly to specific function names and lexical patterns, making expression grammar evolution brittle and creating technical debt.

**Business outcome:** Strict rendering decisions are powered by authoritative, structured failure provenance from the expression resolver. The template engine becomes robust against expression syntax variations, eliminating narrow regex coupling and providing a clean, extensible foundation for future data conversion functions.

### In Scope

- Structured failure provenance model indicating which expression or function failed and the category of failure during expression resolution.
- Updating strict rendering evaluation to consume structured failure provenance instead of regex matching on function names.
- Deprecating and removing renderer-level regex heuristics for identifying strict function calls.
- Automated test coverage validating structured failure reporting, edge cases (unclosed tags, nested calls, multiple placeholders), and strict failure enforcement.

### Out of Scope

- Introducing new conversion functions (e.g. float, boolean) beyond existing catalog functions; those remain separate future enhancements.
- Modifying the public syntax or semantics of existing template expressions visible to collection authors.
- Changing external MCP tool contracts or schema definitions.

## Functional Requirements

- **Structured Failure Provenance:**
  - Expression validation and evaluation must capture and report structured details for failed expressions, including the identity of the function involved (if identified), the failed expression text, and the failure classification (such as syntax error, unknown function, invalid argument, or conversion evaluation error).
  - When content contains multiple expressions, failure provenance must accurately reflect failures occurring across any expression in the content.
- **Provenance-Driven Strict Rendering:**
  - The strict rendering flow must inspect structured failure provenance to determine whether a strict conversion function failed.
  - If structured failure provenance indicates a failed strict conversion, the rendering process must fail closed and reject request execution.
  - If failure provenance indicates only non-strict or unrelated expression failures, existing safe literal fallback behavior must be preserved.
- **Elimination of Textual Regex Heuristics:**
  - The rendering engine must not rely on pattern-matching regexes against function names or token prefixes to detect strict conversion failures.
- **Expression Grammar Independence:**
  - The detection of failed strict conversion functions must operate reliably regardless of arbitrary formatting, whitespace, or nested function structures supported by the grammar.

## Non-functional Requirements

- **Reliability & Safety:** Downstream APIs must remain strictly protected from receiving uncoerced or invalid data. The fail-closed guarantee must not be weakened.
- **Backward Compatibility:** Existing valid collections, templates, and fallback behavior for benign expression errors must remain strictly backward compatible.
- **Maintainability:** Adding or extending template functions in the future must not require changes to the rendering layer's error-detection logic.
- **Performance:** Providing structured failure provenance must introduce negligible overhead during template resolution and request execution.

## Constraints and Assumptions

- Issue type: Technical Debt / Improvement; Parent: PYPOST-1037; Jira: PYPOST-1120.
- Source reference: `ai-tasks/PYPOST-1037/60-tech-debt.md` (line 91).
- Implementation language: Python.
- Testing: Must run completely in local automated test suites using `make` commands without requiring external network access or credentials.

## STEP 1 Approval Basis

The applicable `sprint-runner` / `sprint-task-runner` workflow operates autonomously under the top-down methodology and preauthorizes continuation without an interactive user prompt. Acceptance will be verified via the autonomous review gate.

## Main Entities

| Entity | Business Role | Key Attributes |
| --- | --- | --- |
| **Template Expression** | A dynamic placeholder embedded within a request template. | Raw expression text, delimiters, referenced variables, function calls. |
| **Conversion Function** | A registered transformation function enforcing strict data conversion rules. | Function name, parameter constraints, conversion policy (strict vs. standard). |
| **Failure Provenance** | Structured record of an expression or function failure produced during resolution. | Targeted function name, expression snippet, failure category, severity/strictness flag. |
| **Strict Rendering Mode** | Operational policy that refuses to dispatch requests if designated critical functions fail. | Enforced functions list, fail-closed error handling policy. |
| **Literal Fallback** | Fallback policy preserving raw template text when non-critical expressions cannot resolve. | Preserved raw content, fallback condition criteria. |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this task needed from a business perspective? | Relying on regex pattern matching in the rendering engine to detect failed conversion functions is brittle. It risks failing to catch broken conversions when expression formats vary, and obstructs adding new conversion functions safely. |
| What business value does structured provenance provide? | It guarantees robust fail-closed behavior across all valid syntactic variations of template expressions and decouples the rendering engine from expression lexical details. |
| Does this change template author syntax? | No. Template authors continue to write template expressions exactly as before; only the internal diagnostic and failure-handling mechanism is modernized. |
| How does this affect non-conversion template errors? | Benign, non-strict template expression failures continue to follow the existing safe literal fallback behavior. |
