# PYPOST-450: Support Functions Where Variables Are Allowed

## Goals

Enable users to use functions in all places where variables are currently supported, so
dynamic values can be expressed with the same user experience expectations. This expands
expression capabilities while keeping existing user workflows simple and predictable.

Source: [PYPOST-450](https://pypost.atlassian.net/browse/PYPOST-450) (Jira, type: Debt,
priority: Medium).

## Programming Language

Python

## User Stories

- As a user, I want to use functions in all contexts where variables are accepted, so I can
  build more dynamic expressions without changing my workflow.
- As a user, I want function usage to feel the same as variable usage, so I do not need to
  learn a separate interaction model.
- As a user, I want functions to accept arguments, so I can pass input values and get
  context-specific results.
- As a user, I want to use functions directly in request fields (for example,
  `/{{host}}/{{urlencode(db)}}`), so I can transform values inline without extra steps.
- As a user, I want existing variable-based behavior to continue to work, so my current
  setups remain stable.
- As a UX designer, I want a clear and consistent function usage pattern, so users can easily
  understand how to write function calls with arguments in each supported context.
- As a user, I want clear feedback when a function call is invalid, so I can correct
  expressions without breaking my request.
- As a security reviewer, I want function execution to be controlled by product rules, so users
  cannot run arbitrary user-defined code.

## Definition of Done

1. Functions are available in every expression context where variables are supported today
   (request URL, header names and values, parameter names and values, request body, and
   variable hover preview in supported editors).
2. User interaction and expectations for functions are consistent with existing variable
   usage patterns.
3. Users can provide arguments when using functions.
4. Existing variable-based scenarios remain operational and unchanged in behavior.
5. Documentation and examples clearly describe when and how users can use functions with
   arguments, including catalog examples for `urlencode`, `md5`, and `base64`.
6. Acceptance checks confirm the new function capability works across every expression
   context listed in criterion 1.
7. UX acceptance defines and approves a single user-visible function call format (including
   argument format) for all variable-enabled contexts.
8. Security acceptance confirms that function execution uses only an approved function catalog
   and does not allow arbitrary user-defined code execution.
9. Canonical user-visible syntax matches the approved UX format defined in Scope.

## Task Description

### Problem Statement

Users can currently rely on variables in multiple product contexts, but they cannot apply
functions with the same breadth and consistency. This limits flexibility and forces users to
look for workarounds when they need derived values.

### Scope

- In scope:
  - Enable function usage everywhere variable usage is currently available, including
    request URL, header names and values, parameter names and values, request body, and
    variable hover preview in supported editors.
  - Ensure function usage follows the same user-level behavior model as variables.
  - Support passing a single argument per function call, referencing an existing variable
    name (for example, `{{urlencode(db)}}`).
  - Support chaining allow-listed functions so one function's argument may be another
    allow-listed function call (for example, `{{md5(urlencode(db))}}`).
  - Preserve existing variable-based user scenarios.
  - Define a single UX pattern for function syntax and argument usage across contexts.
  - Canonical syntax: function calls are placed only inside `{{...}}`, for example
    `{{urlencode(db)}}`.
  - Use only a controlled, product-defined list of user-available functions.
  - Include an initial function set available to users: `urlencode(Var)`, `md5(Var)`,
    `base64(Var)`.
- Out of scope:
  - New unrelated user workflows outside current variable-enabled contexts.
  - Changes not required for enabling function usage parity with variables.
  - Multiple comma-separated arguments in a single function call.
  - Execution of arbitrary user-defined code.

### Constraints and Assumptions

- Constraint: requirements in this step remain business and functional only, without
  architectural or implementation design details.
- Constraint: backward compatibility for existing variable usage is mandatory.
- Assumption: users already understand current variable usage patterns and should not need a
  separate conceptual model for function usage.

### Initial Function Catalog

- `urlencode(Var)` - encodes the input value for safe URL usage.
- `md5(Var)` - returns MD5 hash of the input value.
- `base64(Var)` - returns Base64-encoded representation of the input value.

### Main Entities and Interactions (Business Perspective)

- **User**: configures and uses expressions in product contexts that already support
  variables.
  - Attributes: expression text; chosen expression context; expectation of stable variable
    behavior.
- **Expression Context**: a product location where variable usage is currently available.
  - Attributes: context type (URL, header name/value, parameter name/value, body, hover
    preview); supports `{{...}}` placeholders.
- **Function Call**: an approved function name with one argument used inside `{{...}}`.
  - Attributes: function name from the catalog; single argument (variable name or chained
    allow-listed call); user-visible syntax form.
- **Evaluation Result**: value shown or applied after resolving variable and function usage.
  - Attributes: resolved string value; must not alter outcomes for plain-variable
    expressions; invalid calls surface predictable feedback without breaking unrelated
    fields.

Interaction flow:

1. User opens a context where variables are supported.
2. User uses a function in that same context.
3. User passes arguments to the function when needed.
4. System handles the function usage in a way consistent with the existing variable
   experience.
5. User receives the expected result while previous variable behavior remains stable.

## Non-Functional Requirements

- Consistency: behavior and UX patterns for function usage should align with existing
  variable usage expectations.
- Reliability: introducing function support must not degrade existing variable-based
  workflows.
- Clarity: user-facing guidance should make argument usage understandable and predictable.
- Compatibility: existing data and user scenarios that use variables must remain valid.
- Security: function execution must be restricted to a predefined allow-list of supported
  functions, without arbitrary user-defined code execution.

## Q&A

- Q: What does the Jira issue specify at a business level?
  - A: Functions are available in every user-facing context that already accepts variables;
    function usage is perceived and handled similarly to variable usage; functions can accept
    arguments. Users can apply function-based expressions without switching workflows, and
    existing variable-based workflows remain valid.
- Q: Why is this task needed from a business perspective?
  - A: Users need richer expression capabilities while preserving current workflows and
    reducing friction in adoption.
- Q: What is the minimum expected new capability?
  - A: Functions must be available wherever variables are available and must support
    arguments.
- Q: Should this change alter how current variable scenarios behave?
  - A: No. Existing variable behavior should remain stable and compatible.
- Q: Which functions are available to users?
  - A: Initial supported catalog is `urlencode(Var)`, `md5(Var)`, and `base64(Var)`.
    Additional functions may be added later through product-managed updates.
- Q: What argument forms are supported?
  - A: One argument per function call, referencing an existing variable name (for example,
    `{{urlencode(db)}}`). Chaining allow-listed functions is supported (for example,
    `{{md5(urlencode(db))}}`). Multiple comma-separated arguments in one call are out of
    scope.
- Q: Which expression contexts must support functions?
  - A: Every context where variables work today: request URL, header names and values,
    parameter names and values, request body, and variable hover preview in supported
    editors.
- Q: What happens when a function call is invalid or unknown?
  - A: The user receives predictable feedback consistent with existing variable expression
    handling; invalid calls must not break unrelated fields or existing variable behavior.
- Q: Can users execute arbitrary code through function expressions?
  - A: No. Only predefined catalog functions may run; arbitrary user-defined code execution
    is out of scope.
