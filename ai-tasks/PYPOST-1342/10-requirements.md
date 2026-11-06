# PYPOST-1342: Support enum and array items in MCP tool parameter schemas

## Programming Language

Python is the implementation language for the application runtime, collection tooling,
UI request editor, and automated test suites. English Markdown is used for workflow
documentation and technical artifacts.

## Goals

MCP tool parameter contracts today advertise only a JSON type. Closed-choice arguments
(for example review actions, issue/PR state, diff side, job-list filter, and close
reasons) are described in free text, and array arguments (labels, assignees) are
published without item-type information. Some MCP clients reject or weakly validate
those schemas, and callers discover invalid values only after an upstream API error.

**Business goal:** Let tool authors declare allowed values and array element shapes on
MCP parameters so published contracts are accepted by strict clients, agents can choose
valid values from the schema, and invalid caller values are rejected before the HTTP
call — then apply that capability to the curated GitHub and GitLab MCP example
collections.

## User Stories

- As an **AI agent calling MCP tools**, I want closed-choice parameters to expose their
  allowed values in the tool schema, so that I can pick a valid value without guessing
  or waiting for a remote `422`.
- As an **AI agent sending array arguments**, I want array parameters to declare their
  item type, so that strict MCP clients accept the schema and I supply correctly shaped
  lists (for example string labels).
- As an **API collection author**, I want to attach allowed-value lists and array item
  shapes to MCP parameter metadata, so that curated tools publish accurate contracts.
- As a **collection author editing a request in the UI**, I want enum and items metadata
  to round-trip through the request editor and collection save/load, so that contracts
  survive editing and export.
- As a **contributor / maintainer**, I want offline tests to prove schema emission,
  argument rejection for illegal enum/item values, persistence round-trips, and that
  GitHub/GitLab curated params use the new fields where they apply.
- As a **product steward**, I want existing tools without enum/items to keep working
  unchanged, and validation errors never to echo raw argument values into logs or
  messages.

## Definition of Done

- [ ] MCP parameter metadata can optionally declare an allowed-value list and an array
  item shape.
- [ ] Published MCP tool input schemas include those fields when declared.
- [ ] Runtime argument validation rejects values outside an allowed list and array
  elements that do not match the declared item type, without exposing raw values in
  error text.
- [ ] Enum and items survive collection format v2 persistence and the request editor.
- [ ] Curated GitHub MCP params that are closed choices or string arrays declare enum or
  items as appropriate (`event`, `state`, `side`, `filter`, `state_reason`, `labels`,
  `assignees`, and sibling closed fields such as `start_side` / `subject_type` where
  documented).
- [ ] Curated GitLab MCP params `state_event`, `membership`, and `recursive` declare
  their allowed values.
- [ ] Offline automated tests cover schema emission, validation, persistence/UI
  round-trip expectations, and fixture contracts for the tightened collections.
- [ ] Developer documentation describes enum and items on MCP parameters.

## Task Description

**Problem:**
Follow-up from PYPOST-1334 TD-5 (architecture risks R6, R11). Published MCP input
schemas carry only `type`. Closed GitHub/GitLab choices live only in descriptions, and
arrays omit `items`, which some MCP clients reject. Invalid values reach the remote API
instead of failing closed locally.

**Scope (in):**
- Optional allowed-value lists and array item shapes on MCP tool parameters.
- Publish them in agent-visible tool schemas.
- Enforce them during MCP argument value validation.
- Keep them through collection persistence and the request editor.
- Tighten GitHub and GitLab curated example collection params listed above.
- Tests and developer docs for the new contract fields.

**Scope (out):**
- Changing HTTP templates, auth, or remote API coverage beyond schema/metadata.
- Type-preserving JSON body helpers (PYPOST-1343).
- Live GitHub/GitLab network tests.
- Open-ended free-text filters that are not closed sets in the curated descriptions
  (for example arbitrary workflow event names beyond documented examples remain
  free-form unless a closed list is already documented for that tool).

**Constraints and assumptions:**
- Omitted enum/items means “no extra constraint” (backward compatible).
- Validation must stay value-safe (no raw argument leakage).
- Verification is offline and deterministic.

## Main Entities and Interactions

- **MCP Tool Parameter:** Agent-visible metadata for one tool argument (type,
  description, required, default, and optionally allowed values / array item shape).
- **Published Tool Schema:** The contract MCP clients read when listing tools.
- **Argument Validator:** Checks caller values against the parameter contract before
  execution.
- **Collection / Request Editor:** Where authors define and persist parameter metadata.
- **Curated Provider Collections:** GitHub and GitLab example MCP tools that should
  advertise closed choices and string arrays accurately.

**Interaction Flow:**
1. An author declares allowed values or array item shape on a parameter.
2. An agent lists tools and sees those constraints in the schema.
3. An agent calls with an illegal value or wrong array element type; validation fails
   closed with a safe diagnostic.
4. An agent calls with a valid value; execution proceeds as today.

## Non-Functional Requirements

- **Compatibility:** Existing params without enum/items behave as before.
- **Client interoperability:** Schemas include standard JSON Schema `enum` / `items`
  when declared so strict MCP clients accept them.
- **Safety:** Validation errors never include raw argument values.
- **Deterministic offline verification:** No live provider credentials required.

## Q&A

**Q: Why is this a business need and not just a schema nicety?**
**A:** Strict clients reject incomplete array schemas, and agents waste calls discovering
closed choices only via upstream errors. Clear contracts improve reliability and
ergonomics of curated MCP tools.

**Q: Must every string parameter gain an enum?**
**A:** No. Only closed, documented value sets and array string lists in the curated
GitHub/GitLab tools (plus the general capability for any author).

**Q: Does this change remote API behavior?**
**A:** No. It improves the published contract and local validation; successful calls
still hit the same HTTP templates.
