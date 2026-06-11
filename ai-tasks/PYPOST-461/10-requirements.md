# PYPOST-461: Expand FunctionExpressionResolver edge-case test matrix

## Goals

This section describes why this task is needed from a business perspective.
- Ensure that template expression parsing is extremely robust, stable, and predictable.
- Avoid regressions where templates fail to parse with clear, consistent error codes.
- Guarantee that evaluation and validation ordering across multiple template placeholders follows a stable, deterministic, and documented first-failure strategy. This provides a consistent experience for template authors when diagnosing failures across multiple inputs.

## Programming Language

Python

## User Stories

Section with a list of user stories. Use roles defined in the project (if applicable).
- As a **Template Author**, I want my malformed template expressions to report clear, stable error codes and function names, so that I can easily diagnose syntax and structure mistakes without guessing.
- As a **Template Author**, I want evaluation failures in multi-placeholder templates to always report the very first validation error from left-to-right, so that the feedback is predictable and consistent.
- As a **Developer**, I want an expanded test matrix covering edge cases like empty arguments, unmatched nesting parentheses, and mixed multi-placeholder results to ensure code behavior remains locked and regression-free.

## Definition of Done

This section describes when the task is considered `done`, with a list of acceptance criteria (business logic verification).
- Add robust unit tests that verify empty-argument calls (e.g., `md5()`) raise stable errors (`invalid_argument`).
- Add tests verifying malformed nested parenthesis patterns (e.g., unbalanced or extra parentheses) map to correct, stable error codes and associate with the appropriate function context.
- Add tests verifying evaluation ordering across multiple placeholders: when mixed valid/invalid inputs are supplied, the first failure from left-to-right is consistently returned (first-failure behavior).
- The entire PyPost test suite must remain green and pass cleanly.

## Business Entities

This section describes the main business entities and their attributes from a business perspective (not database tables or technical classes).

### Template Expression
A text template containing a mix of static content and dynamic placeholders that requires evaluation and validation.
- **Attributes**:
  - *Raw Template Content*: The full string representation of the template.
  - *Placeholders*: A collection of individual dynamic elements embedded within the template.

### Template Placeholder
An individual dynamic expression enclosed in double curly braces (e.g., `{{ ... }}`) that represents a value to be resolved or a function to be evaluated.
- **Attributes**:
  - *Raw Expression*: The exact string content inside the curly braces.
  - *Sequence Position*: The left-to-right position/order of the placeholder within the template expression.

### Function Expression
A specific type of placeholder representing a function call with arguments (e.g., `md5(x)`).
- **Attributes**:
  - *Function Identifier*: The name of the function to invoke (e.g., `md5`, `urlencode`, `base64`).
  - *Arguments*: The input values or nested function expressions passed to the function.

### Validation Result
The outcome of checking a template expression or placeholder for syntactic and semantic correctness.
- **Attributes**:
  - *Is Valid*: A boolean flag indicating whether the validation succeeded.
  - *Error Code*: A stable, unique identifier representing the failure type (e.g., `invalid_argument`, `unknown_function`) if validation failed.
  - *Error Context*: Additional metadata describing the failure, such as the associated function identifier.

## Task Description

This section describes the problem, goals, and constraints.
The PyPost engine parses and validates template expressions using a function expression resolver. However, edge-case coverage is currently missing for empty-argument calls, malformed nested-parenthesis patterns, and evaluation ordering under multi-placeholder setups. To prevent future regressions and ensure stable behavior:
- We need to explicitly lock down error-code stability for empty-argument invocations and malformed nested structures.
- We need to verify and document first-failure evaluation order semantics.

### Functional Requirements
- **Empty-Argument Validation**: The system must validate that function expressions with empty arguments (such as `md5()`, `urlencode()`, `base64()`) are treated as invalid, producing a stable `invalid_argument` error code with the correct function name.
- **Malformed Nested Parenthesis Validation**: The system must validate that malformed parenthesis structures (such as extra closing parentheses, unmatched nesting, etc.) are detected and map to stable, predictable error codes associated with the appropriate function context.
- **Multi-Placeholder Evaluation Ordering**: When validating a template with multiple placeholders, the system must evaluate them sequentially from left to right. It must stop at the first encountered failure and report that specific error (first-failure behavior).
- **Test Matrix Completeness**: Implement comprehensive, table-driven unit tests to lock down all functional requirements and prevent future regressions.

### Non-Functional Requirements
- **Error Code Stability**: Error codes returned for edge-case validation failures must remain completely stable and consistent across releases to avoid breaking downstream clients.
- **Deterministic Evaluation**: Placeholder validation must be strictly deterministic, ensuring that the same input template always produces identical validation outcomes and error ordering.
- **No Performance Regression**: The addition of the expanded test matrix and validation checks must not introduce any performance degradation to the template parsing and validation engine.
- **Backward Compatibility**: Existing valid template expressions and their validation behaviors must remain entirely unaffected.

### Scope Boundaries (Out of Scope)
- **Production Code Changes**: Modifying the core parser, grammar, nesting policy, function catalog, or resolver logic is strictly out of scope unless a test proves incorrect behavior. This task is focused on expanding the test matrix and locking down existing behavior.
- **Runtime Integration**: Integration with downstream services like `TemplateService` or runtime-hover features is out of scope.
- **Observability Enhancements**: Adding logs, metrics, or telemetry to the resolver module is out of scope.

Constraints:
- Strictly no technical implementation details, regex patterns, or code architectures are allowed in this requirements phase.
- All testing behavior and assertions must align with the existing resolver's contract and design rules.

## Q&A

List of questions and answers. Add links if used.
- **Why is empty-argument behavior considered `invalid_argument` rather than `invalid_arity`?**
  In PyPost, functions like `md5()` expect a single argument. When the argument is omitted, the empty content within the parenthesis is treated as a malformed or missing argument, mapping to an `invalid_argument` error context. This behavior is locked down for stability.
- **How does evaluation ordering across multiple placeholders behave?**
  When a template contains multiple placeholders (e.g., `{{ valid(x) }} {{ invalid(y) }}`), validation scans the placeholders sequentially from left to right. The validation stops and reports the very first error encountered. This is known as "first-failure ordering."
