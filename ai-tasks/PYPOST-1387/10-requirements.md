# PYPOST-1387: Inline Syntax Validation and Guidance for Hidden Field Selectors

## Goals

Response masking in PyPost depends on users correctly authoring **field selector** expressions in the Request Editor **Hidden Fields** table. Those selectors decide which JSON keys, nested paths, array elements, or response headers are redacted in the desktop response view and in MCP tool output.

Today the table accepts any free-text string with **no live feedback**. Unsupported or malformed expressions (for example full JSONPath such as `$.users[0].name`, filter expressions, or other patterns outside the supported selector vocabulary) are typically **ignored at masking time without a clear error**. Users can believe sensitive fields are protected when they are not — a silent configuration failure with security and privacy impact.

This task closes that gap as a non-blocker follow-up from [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) technical debt (reaffirmed after the [PYPOST-1386](https://pypost.atlassian.net/browse/PYPOST-1386) virtualized table delivery): while the user enters or reviews selectors in `HiddenFieldsTable`, the product must provide **live inline syntax validation**, **visible indication of syntax problems**, and **helpful tooltip suggestions** that explain what is wrong and how to write a supported selector.

The business goal is to make masking configuration **self-correcting and trustworthy**: users discover mistakes immediately while editing, learn the supported selector forms without leaving the editor, and reduce the risk of shipping collections that silently fail to mask sensitive data.

## Implementation Language

- **Implementation language**: Python

## User Stories

- As a **security-conscious API developer**, I want immediate feedback when a selector I type cannot be interpreted by the masking rules, so I do not save a request that appears configured but fails to redact secrets.
- As an **enterprise compliance engineer**, I want invalid selectors visually distinguished in the Hidden Fields list, so I can scan large catalogs and spot broken rules before releasing a collection.
- As a **new PyPost user**, I want short tooltip guidance with examples of supported selector forms (simple key, dotted path, array wildcard, header selector), so I can learn the vocabulary without reading separate documentation.
- As an **API developer editing existing selectors**, I want validation to update as I type or leave a cell, so I can fix typos and unsupported syntax without running a request first.
- As a **user with a large selector list**, I want validation feedback to remain usable and responsive while editing, including after the table was virtualized for large catalogs (PYPOST-1386).
- As a **maintainer of existing requests**, I want previously saved valid selectors and normal editing workflows (trailing empty row, dirty tracking, add/remove) to keep working unchanged when syntax is correct.

## Definition of Done

This task is considered complete when:

1. While editing field selectors in the Hidden Fields table, the product evaluates each non-empty selector against the **supported selector vocabulary** used for response masking.
2. Selectors that are **syntactically invalid or unsupported** are visually highlighted in the table so the problem is obvious without leaving the cell.
3. Hovering (or an equivalent in-cell affordance) on a problematic selector shows a **tooltip** that states the problem in plain language and offers **helpful suggestions or examples** of valid forms.
4. Valid selectors in the supported forms receive **no error highlight** and do not show error tooltips:
   - Simple key (e.g. `token`, `password`)
   - Dot-notation object path (e.g. `auth.token`, `data.user.secret`)
   - Array wildcard path (e.g. `users[*].email`, `items[*].secret`)
   - Header selector (e.g. `header:Authorization`)
5. Feedback is **live** during normal editing (as the user types and/or commits a cell edit), not only after sending a request or reloading the collection.
6. Invalid syntax **does not crash** the editor; empty trailing rows remain editable without false errors; blank/whitespace-only rows continue to be omitted from persisted data as today.
7. Existing table behaviors remain intact: trailing empty row, add/remove (context menu and Delete/Backspace), multi-select removal, dirty-state signals, and public get/set data contracts used by the request editor.
8. Scope stays on **in-table guidance** for `HiddenFieldsTable`; it does not redefine masking algorithms, persistence schemas, or MCP sanitization outcomes for already-saved bad strings beyond what the UI surfaces.
9. Automated tests cover valid vs invalid examples and tooltip/highlight expectations; repository quality gates pass via `make check`.

## Task Description

### Problem Statement

`HiddenFieldsTable` was introduced in PYPOST-1377 and later virtualized in PYPOST-1386. Entry remains free-text. The masking engine understands a fixed set of selector patterns; anything outside that set tends to be skipped quietly. Users have no in-editor signal that a selector will not match, which produces false confidence that PII or credentials are masked.

Related debt ([PYPOST-1395](https://pypost.atlassian.net/browse/PYPOST-1395) / [PYPOST-1483](https://pypost.atlassian.net/browse/PYPOST-1483)) notes the same class of problem for broader collection-editor linting and autocompletion. **This ticket is specifically** live inline validation, error highlighting, and tooltip suggestions **inside the Hidden Fields table**, not a full collection-schema linter or autocomplete product.

### Scope

- Live syntax checking of selector expressions as users edit them in `HiddenFieldsTable`.
- Clear visual indication of syntax errors / unsupported forms on affected rows or cells.
- Helpful tooltips that explain the issue and suggest supported patterns with concise examples.
- Alignment of “valid” with the selector forms already documented for response masking (simple key, dotted path, array wildcard, header selector).
- Preservation of current editing, dirty-tracking, and data get/set behavior for valid content.

### Out of Scope / Constraints

- Changing how the masking engine redacts JSON or headers at runtime (beyond ensuring UI validity aligns with what that engine accepts).
- Redesigning persistence of `hidden_response_fields` (remains an ordered list of strings).
- Full autocompletion / suggestion dropdowns or collection-wide schema linting (tracked separately, e.g. PYPOST-1483).
- Semantic “does this path exist in the last response?” matching — this task is **syntax / form** validation, not payload-aware path discovery.
- Blocking save or forcing removal of invalid selectors as a hard gate (unless product behavior already requires it; default expectation is **advisory visual guidance** so users can still draft and fix).
- Selector deduplication policy (separate follow-up PYPOST-1533).
- Per-row enable/disable checkboxes (separate follow-up PYPOST-1530).

### Functional Requirements

- **FR1: Live syntax evaluation**
  - Each non-empty selector string entered in the Hidden Fields table must be evaluated for conformance to the supported selector vocabulary as the user edits.
  - Evaluation must cover the four supported families: simple key, dotted path, array wildcard path, and header selector.

- **FR2: Syntax error highlighting**
  - Selectors that fail evaluation must be visually highlighted so invalid rows are distinguishable from valid ones at a glance.
  - Highlight state must clear when the user corrects the expression to a valid form.
  - The trailing empty row used for new entry must not appear as an error while empty.

- **FR3: Helpful tooltip suggestions**
  - For an invalid or unsupported selector, a tooltip (or equivalent hover/help text) must describe why the expression is not accepted.
  - Tooltips must include brief constructive guidance — for example pointing the user toward supported patterns and short examples — rather than only saying “invalid”.
  - Valid selectors must not show error tooltips.

- **FR4: Unsupported familiar alternatives**
  - Expressions that look like common but unsupported dialects (e.g. `$`-prefixed JSONPath, filter predicates, numeric index brackets other than the documented `[*]` wildcard) must be treated as invalid/unsupported for highlighting and tooltip purposes, with guidance toward the supported forms.

- **FR5: Workflow parity**
  - Add, edit, remove, multi-select delete, trailing empty row, dirty notifications, and request-editor data load/save must continue to work for valid selectors exactly as after PYPOST-1386.
  - Whitespace trimming and omission of empty rows on read must remain consistent with current behavior.

- **FR6: Non-destructive drafting**
  - Validation feedback must not prevent the user from continuing to type or navigate the table.
  - Invalid text may remain visible in the cell until the user fixes it; the product must not silently rewrite user input into a different selector without explicit user action.

### Non-Functional Requirements

- **NFR1: Responsiveness**
  - Inline validation and highlight updates must not introduce perceptible UI freezes during normal typing in lists up to the large-catalog sizes already targeted by PYPOST-1386 (on the order of 1,000 selectors).

- **NFR2: Clarity**
  - Error messaging must be understandable to API developers without requiring knowledge of internal engine class names.

- **NFR3: Consistency**
  - What the UI marks as valid must match the selector forms that response masking and MCP redaction already honor, so users are not told a selector is fine when masking will ignore it, or vice versa.

- **NFR4: Quality gates**
  - Changes must pass repository `make lint`, `make typecheck`, and `make check`, with automated coverage for representative valid and invalid selector cases.

## Entities

- **Field Selector**: A user-authored string that identifies which response field(s) or header(s) should be masked (e.g. `token`, `user.email`, `items[*].ssn`, `header:Authorization`).
- **Supported Selector Vocabulary**: The closed set of selector forms the product documents and honors for masking (simple key, dotted path, array wildcard, header selector).
- **Syntax Validation Result**: The outcome of checking one selector — valid, or invalid/unsupported with a human-readable explanation and suggested correction patterns.
- **Inline Feedback**: The combination of visual highlight and tooltip guidance shown on a selector row while the user configures Hidden Fields.
- **Selector Collection**: The ordered list of selectors attached to a request’s hidden-response-fields configuration.

## Q&A

### Q1: Why is this needed if the masking engine already “fails closed” by ignoring bad selectors?
**A**: Ignoring bad selectors avoids crashes, but it also creates a **false sense of security**. Users configure masking to protect secrets and PII; a silently ignored selector means those values remain visible in the GUI and may leak through MCP. Live feedback converts silent no-ops into actionable editor guidance before the collection is shared or automated.

### Q2: Is the business need “prettier UI” or “correct masking configuration”?
**A**: The primary need is **correct, trustworthy configuration**. Highlights and tooltips are the means; the outcome is fewer misconfigured masking rules and faster authoring of valid selectors.

### Q3: Does this ticket include autocomplete or collection-wide lint?
**A**: No. Those are related UX improvements tracked elsewhere (e.g. PYPOST-1483). This ticket is limited to **live inline validation, error highlights, and tooltip suggestions** in the Hidden Fields table.

### Q4: Should invalid selectors block saving the request?
**A**: By default, no hard save block is required. The goal is immediate advisory feedback so users can fix mistakes. Hard blocking would be a separate product decision; this task focuses on visibility and guidance.

### Q5: Does “valid” mean the path exists in the last API response?
**A**: No. Validity here means the expression conforms to the **supported selector syntax**, not that a particular payload currently contains that path. Payload-aware discovery is out of scope.

### Q6: What programming language is used?
**A**: Python (PyPost desktop application and existing Hidden Fields / selector stack).
