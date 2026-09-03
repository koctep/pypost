# PYPOST-1100: Type-check runtime MCP tool-call arguments

## Goals

PyPost exposes selected request definitions as MCP tools. Each exposed tool
declares the kinds of values its parameters accept, but runtime calls currently
allow a client to send a different kind of value and still begin execution.

The business goal is to make the MCP tool contract dependable at the point of
use. A client or AI agent should receive a clear, actionable failure for an
invalid argument, while valid calls should continue with their values
unchanged. Rejecting invalid input protects request authors from unexpected
downstream behavior and gives MCP clients a predictable contract to follow.

This task is a runtime follow-up to the default-value validation delivered in
[PYPOST-1089](../PYPOST-1089/10-requirements.md). It covers values supplied by
an MCP caller, not a redesign of parameter authoring or default storage.

## User Stories

- As an **MCP tool author**, I want the parameter types I declare to be enforced
  for every runtime call, so that malformed input cannot begin my tool's action.
- As an **MCP client or AI agent**, I want a wrong-typed argument to produce a
  clear validation failure naming the affected parameter and expected type, so
  that I can correct the call without guessing what went wrong.
- As an **MCP client or AI agent**, I want accepted argument values to retain
  their supplied form, so that strict checking does not unexpectedly alter
  request data.
- As an **MCP tool author**, I want existing optional parameters and defaults to
  keep their current behavior, so that adding validation does not break valid
  established tool calls.
- As an **MCP tool author**, I want numeric identifiers declared as
  `integer_or_string` to accept both native integers and whole-number strings,
  so that clients using either published form remain compatible.
- As an **MCP client or AI agent**, I want the same argument rules when I use
  any supported MCP tool-call transport, including WebSocket, so that changing
  transport does not create a different feature contract.

## Definition of Done

- [ ] Every non-null runtime argument for a declared parameter is checked
      against that parameter's declared type before the tool executes.
- [ ] The accepted value categories are defined consistently as follows:

  | Declared type | Accepted runtime values |
  | --- | --- |
  | `string` | Text values. |
  | `integer` | Whole-number integer values; booleans are not integers for this contract. |
  | `integer_or_string` | Whole-number integer values or whole-number decimal strings. |
  | `number` | Integer or decimal-number values; booleans are not numbers for this contract. |
  | `boolean` | Boolean values only. |
  | `array` | Array/list values. |
  | `object` | Object/map values. |

- [ ] A wrong-typed argument is rejected, not silently converted, substituted,
      or allowed to begin the tool action.
- [ ] A rejected call produces a client-visible validation failure that
      identifies the parameter and expected type. The failure is distinguishable
      from a successful tool result and from a failure during tool execution.
- [ ] Tool execution does not begin and no externally visible action occurs
      after an argument validation failure.
- [ ] Valid arguments continue in their accepted supplied form. In particular,
      a whole-number string accepted by `integer_or_string` remains a string,
      and a native integer remains an integer.
- [ ] The published `integer_or_string` contract remains compatible with its
      two accepted forms: a native whole-number integer or a string containing
      an optional leading sign followed only by decimal digits. Arbitrary
      strings, decimal fractions, exponent notation, and booleans are not
      accepted under this type.
- [ ] If a parameter is omitted or supplied as `null`, existing default
      application behavior is preserved. When a non-null default is applied,
      the effective value is subject to the same declared-type contract.
- [ ] A supplied wrong-typed non-null value is rejected; it must not trigger a
      fallback to the parameter default.
- [ ] Existing required-argument and optional-argument semantics are preserved.
      This task adds type enforcement and does not introduce a new policy for
      missing arguments.
- [ ] Existing valid MCP calls continue to execute successfully, including
      calls using the two supported `integer_or_string` forms.
- [ ] Validation failures provide only safe diagnostic information and do not
      disclose the rejected argument's contents or other sensitive request data.
- [ ] The same declared-parameter rules apply to every supported MCP tool-call
      transport, including WebSocket. A transport change does not change which
      argument values are accepted or how invalid values are reported.

## Task Description

### Problem

The MCP tool contract tells clients what types to send, but the runtime tool
path does not currently enforce those declarations. A client can therefore
send, for example, text for an integer parameter and allow an unexpected value
to flow into execution. The resulting behavior may be confusing, may fail
later than the call boundary, and may cause an unintended action to be
attempted.

### Scope

In scope:

- Runtime values supplied to exposed MCP tools through any supported MCP
  tool-call transport, including WebSocket.
- The seven currently supported declared parameter types listed above.
- The client-facing behavior for accepted values and rejected values.
- The relationship between client values, non-null defaults, and existing
  required/optional behavior.
- Compatibility between runtime acceptance and the existing
  `integer_or_string` contract.

Out of scope:

- Validation of parameter defaults, which was delivered by PYPOST-1089, except
  for ensuring an applied default is treated as the effective value.
- Changes to the request editor, parameter authoring UI, or default parsing.
- A new policy for unknown argument names.
- A new policy for omitted or null required arguments.
- Changes to unrelated MCP tool behavior or the meaning of any supported
  tool-call transport.

### Constraints and Assumptions

- The implementation language is Python.
- The existing seven MCP parameter types are the complete supported type set
  for this task; no new parameter type is introduced.
- Strict rejection is preferred over conversion because silent conversion can
  hide client defects and alter request meaning. The explicit
  `integer_or_string` union remains the one intentional compatibility case for
  whole-number identifier strings.
- A validation failure identifies the affected parameter and expected type and
  provides safe diagnostic information without disclosing the raw argument.
- Existing successful calls are the compatibility baseline. A client that
  already sends an accepted value should see no change in tool behavior.

## Main Entities and Interactions

- **MCP tool definition** — an exposed capability with named parameter
  declarations, accepted value types, optional defaults, and required/optional
  status.
- **MCP client or AI agent** — submits a tool name and a set of runtime
  argument values.
- **Runtime argument** — a client-supplied value associated with a declared
  parameter, or the effective default when the existing default rule applies.
- **Validation outcome** — either an accepted argument set or a rejected call
  with a client-visible explanation.
- **Tool execution** — the downstream action that may run only after all
  applicable declared arguments are accepted.

The business interaction is: the client requests a tool call; PyPost compares
each supplied or effective declared value with the tool definition; PyPost
executes the tool only when the values are acceptable; otherwise PyPost
returns a validation failure and does not attempt the action.

## Non-Functional Requirements

- **Predictability:** The same invalid value must be rejected consistently for
  every call to the same tool definition and through every supported transport.
- **Compatibility:** Valid existing calls, including native-integer and
  whole-number-string `integer_or_string` calls, must retain their current
  meaning.
- **Safety:** Rejected input must not trigger an action or expose the rejected
  raw value in client-facing diagnostics.
- **Clarity:** A caller can identify the affected parameter and expected type
  from the validation failure and distinguish it from a tool execution failure.
- **Performance:** Checking a normal MCP argument set must not introduce a
  material delay for the caller.
- **Observability:** A rejected call remains distinguishable from a successful
  call and from a tool execution failure in operational reporting.

## Q&A

**Q: Why is runtime validation needed when the MCP contract already declares
the parameter types?**

A: The contract guides well-behaved clients but is not a sufficient runtime
boundary. Enforcing the same contract on arrival prevents malformed values from
reaching tool execution and gives clients a deterministic correction path.

**Q: Should PyPost reject a wrong-typed value or convert it?**

A: Reject it. Automatic conversion can change the meaning of a tool call and
can hide a client or agent defect. The only two-form behavior is the already
declared `integer_or_string` contract.

**Q: How should a validation failure surface to an MCP client?**

A: It should be a client-visible validation failure, not a normal successful
tool result and not an execution outcome. The failure should name the parameter
and expected type, and should provide only safe diagnostic information without
echoing the raw argument.

**Q: What does `integer_or_string` accept?**

A: It accepts a native whole-number integer or a string containing an optional
leading `+` or `-` followed only by one or more decimal digits. The string form
is preserved as a string. Booleans, arbitrary strings, decimal fractions, and
exponent notation are rejected.

**Q: How do defaults interact with validation?**

A: Omitted or null arguments continue to use the existing default-application
rule. If a non-null default is applied, the effective value must satisfy the
declared type. A wrong-typed non-null client value is rejected and never
replaced by the default.

**Q: Does this task change required-argument handling?**

A: No. Existing required and optional behavior for omitted or null values is
preserved. This task governs type validity for values that are supplied or
become effective through the existing default rule.

**Q: Are unknown argument names rejected by this task?**

A: No new unknown-argument policy is defined here. Existing behavior remains
unchanged; this task concerns values associated with declared parameters.

**Q: Are WebSocket MCP tool calls included?**

A: Yes. The same declared-parameter rules apply to WebSocket and every other
supported MCP tool-call transport. No transport-specific variant of the
feature is introduced.
