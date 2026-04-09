# PYPOST-450: Support Functions Where Variables Are Allowed

## Goals

Provide users with a consistent way to use functions in every place where variables are
currently supported. This expands expression capabilities while keeping existing user
workflows simple and predictable.

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
- As a security reviewer, I want function execution to be controlled by product rules, so users
  cannot run arbitrary Python code.

## Definition of Done

1. Functions are available in all user-facing contexts where variables are currently
   available.
2. User interaction and expectations for functions are consistent with existing variable
   usage patterns.
3. Users can provide arguments when using functions.
4. Existing variable-based scenarios remain operational and unchanged in behavior.
5. Documentation and examples clearly describe when and how users can use functions with
   arguments.
6. Acceptance checks confirm the new function capability works across the full existing
   variable usage surface.
7. UX acceptance defines and approves a single user-visible function call format (including
   argument format) for all variable-enabled contexts.
8. Security acceptance confirms that function execution uses only an approved function catalog
   and does not execute arbitrary user-provided Python code via `eval`.
9. Canonical syntax: functions are written inside `{{...}}`, for example
   `{{urlencode(db)}}`.

## Task Description

### Problem Statement

Users can currently rely on variables in multiple product contexts, but they cannot apply
functions with the same breadth and consistency. This limits flexibility and forces users to
look for workarounds when they need derived values.

### Scope

- In scope:
  - Enable function usage everywhere variable usage is currently available.
  - Ensure function usage follows the same user-level behavior model as variables.
  - Support passing arguments to functions.
  - Preserve existing variable-based user scenarios.
  - Define a single UX pattern for function syntax and argument usage across contexts.
  - Canonical syntax: function calls are placed only inside `{{...}}`.
  - Use only a controlled, application-defined list of user-available functions.
  - Include an initial function set available to users: `urlencode(Var)`, `md5(Var)`,
    `base64(Var)`.
- Out of scope:
  - New unrelated user workflows outside current variable-enabled contexts.
  - Changes not required for enabling function usage parity with variables.
  - Execution of arbitrary user-provided Python code.

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
- **Expression Context**: any product location where variable usage is currently available.
- **Function Call**: user-provided function with optional arguments used in an expression.
- **Evaluation Result**: value shown or applied after resolving variable/function usage.

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
  functions, without generic code evaluation from userspace.

## Q&A

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
- Q: Will userspace expressions be executed with Python `eval`?
  - A: No. Arbitrary userspace code evaluation is out of scope and prohibited by the security
    requirement.
