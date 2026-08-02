# PYPOST-1037: Safely coerce template string values to integers

## Goals

PyPost template authors need a supported way to express an integer value when
an MCP tool receives its input as text but the destination operation requires
an integer. Without this capability, otherwise valid tool calls can be rejected
before they reach the requested operation, forcing collection authors to use
workarounds or leave a useful tool scenario unavailable.

**Programming language:** Python

## User Stories

- As an **MCP client user**, I want a text value I supply for an integer input
  to be understood as an integer by a compatible MCP operation, so the tool can
  complete the action I requested.
- As a **collection author**, I want a documented, supported integer-conversion
  expression, so I can author compatible request templates without inventing
  one-off workarounds.
- As a **maintainer**, I want the available template expressions to remain
  controlled and predictable, so adding this capability does not broaden the
  set of expressions users can execute unexpectedly.

## Definition of Done

- [ ] A template author can use `to_int(...)` with one supplied value to obtain
      an integer value for a compatible request field.
- [ ] Valid whole-number text values can be converted for use in URL, parameter,
      and body template contexts where the destination expects an integer.
- [ ] Empty, invalid, and non-numeric inputs follow the established safe template
      failure behavior and do not cause an unintended outbound operation.
- [ ] The new expression is documented together with its intended input and
      failure behavior.
- [ ] Automated coverage protects successful conversion and rejected input.
- [ ] Existing documented template expressions and ordinary variable
      substitution continue to behave as before.

## Task Description

**Problem:** MCP and agent inputs commonly arrive as strings, while some
destination operations require integers. A live Jira MCP smoke test showed that
an integer identifier provided as text was rejected by input validation. This
prevents users from completing otherwise valid operations with the values they
supplied.

**Business outcome:** Collection authors can declare an explicit, reusable,
and safe conversion from a supplied string to an integer. MCP clients can use
integer-requiring operations without needing a special collection-specific
workaround.

### In Scope

- A supported `to_int(...)` template expression for a single supplied value.
- The observable conversion of valid whole-number text into an integer value.
- Safe handling of empty, invalid, and non-numeric values.
- Automated evidence and developer-facing documentation of the expression.

### Out of Scope

- Changing external MCP schemas so integer inputs are accepted as strings.
- Updating the Jira MCP example collection to use this expression; that is
  covered by the dependent follow-up story.
- Adding other coercion expressions, including floating-point or boolean
  conversion.
- Changing unrelated collection contracts or external service configuration.

## Functional Requirements

- The system must recognize `to_int(...)` as a supported template expression
  with exactly one supplied value.
- For a valid whole-number textual value, the expression must yield an integer
  value that a destination operation requiring an integer can consume.
- The expression must be usable wherever a request template accepts a rendered
  value, including URL, parameter, and body contexts.
- Invalid, empty, or non-numeric values must preserve the product's existing
  safe behavior for an invalid template expression: no altered or unintended
  request value is sent.
- Existing template authors must retain the current behavior of supported
  expressions and ordinary variables.

## Non-functional Requirements

- **Safety:** Only the explicitly supported conversion capability is available;
  inputs must not introduce arbitrary expression execution.
- **Reliability:** Invalid input must fail predictably and consistently with
  established template behavior.
- **Compatibility:** Existing collections, template variables, and supported
  expressions must continue to work without changes.
- **Maintainability:** The supported use, boundaries, and failure outcome must
  be clear to collection authors and maintainers.
- **Testability:** Automated tests must run without live Jira credentials or a
  real Jira project.

## Constraints and Assumptions

- Issue type: Story; priority: Medium; labels: `mcp`, `templates`; story
  points: 3.
- Jira browse: https://pypost.atlassian.net/browse/PYPOST-1037
- The primary motivating use case is a Jira MCP operation that expects an
  integer identifier but receives a string from an MCP or agent request.
- This story provides the reusable capability; PYPOST-1038 is the dependent
  collection-wiring follow-up.
- Python is the repository's implementation and test language.

## STEP 1 Approval Basis

The applicable `sprint-runner` workflow explicitly runs in autonomous mode and
preauthorizes continuation without a separate user gate. That explicit
preapproval is the approval basis for this completed requirements step.

## Main Entities

| Entity | Description |
| --- | --- |
| MCP client | User or agent that supplies values when calling a published MCP tool |
| Collection author | Person who defines request templates for a collection |
| Supplied value | Text value provided by an MCP client or agent |
| Integer-required operation | Destination operation that accepts a whole-number input |
| Template expression | Author-visible instruction that derives a request value from a supplied value |
| Converted value | Integer result made available to the destination operation |
| Invalid input | A supplied value that cannot represent the required whole number |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this task needed? | A live Jira MCP smoke test showed that an integer identifier supplied as text is rejected before the requested operation can run. The task removes that user-facing compatibility gap. |
| What value does it provide? | It lets collection authors support integer-requiring operations for MCP/agent inputs while keeping the template language controlled and reusable. |
| What happens for invalid input? | It follows the product's existing safe template-failure behavior, preventing an unintended altered request from being sent. |
| Does this change Jira's input schema? | No. External schemas and the Jira collection wiring are outside this story. |
| Why is this a reusable feature rather than a Jira-only change? | String-to-integer mismatch can occur in any collection whose clients supply textual arguments to an integer-requiring operation. |
