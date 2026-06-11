# PYPOST-470: Expand variable name validation tests (Unicode, boundaries)

## Goals

PYPOST-163 introduced validation when users create new environment variable names so names
remain usable in Jinja2 templates across PyPost (URLs, headers, body, and related flows).
Initial validation was verified manually; baseline automated tests were added in PYPOST-477,
but edge-case behavior is still under-specified and under-tested. This follow-up closes that
gap so unusual names — Unicode letters, mixed character classes, and boundary-length or
boundary-position inputs — have documented, repeatable verification. The outcome is higher
confidence that users receive consistent accept/reject decisions and that future changes do
not silently weaken validation.

## Programming Language

Python 3.10+ (pytest), consistent with the existing pypost test suite.

## User Stories

- As a user creating a new environment variable, I want names with non-ASCII letters to be
  handled consistently with Jinja2 expectations so I am not surprised by template errors
  after a name is accepted.
- As a user entering an unusual name (for example, a valid prefix with an invalid
  character, or a very long name), I want the same validation outcome every time — whether
  I use the ResponseView “New Variable…” flow or edit keys in Manage Environments.
- As a maintainer, I want automated tests that cover Unicode, mixed valid/invalid strings,
  and boundary inputs so regressions in variable name validation are caught in CI before
  release.
- As a reviewer, I want validation behavior for edge cases written down alongside tests so
  policy ambiguities (especially Unicode vs documented ASCII-only wording) are resolved or
  explicitly recorded.

## Definition of Done

- Automated tests verify variable name validation for Unicode-related inputs beyond the
  three valid-letter examples already present (including cases that should be rejected when
  they would break Jinja2 or current product rules).
- Automated tests verify mixed valid/invalid strings (for example, valid leading characters
  with invalid trailing characters, digits after letters with illegal symbols, combined
  failure modes) and assert the correct user-facing rejection category.
- Automated tests verify boundary conditions such as minimum-length valid names, long valid
  names, names at typical upper bounds, and inputs on the edge between empty and non-empty.
- Tests assert both acceptance/rejection and the associated failure reason where the
  product distinguishes empty, starts-with-digit, and invalid-character cases.
- Existing baseline tests from PYPOST-477 remain passing; new cases tighten rather than
  duplicate happy-path and obvious-invalid coverage.
- Any deliberate Unicode acceptance policy is recorded in requirements Q&A or dev docs in a
  later step if tests confirm behavior differs from older ASCII-only documentation.
- Project test suite passes with the expanded coverage.

## Task Description

Technical-debt follow-up from `ai-tasks/PYPOST-163/60-tech-debt.md` (formerly item 163-1).
PYPOST-478 centralized rules in a shared validation capability; PYPOST-477 added first-pass
unit tests (basic valid/invalid paths and a small Unicode-letters-allowed set). PYPOST-470
completes the remaining coverage called out in review: Unicode relevance to Jinja2, mixed
valid/invalid strings, and boundary conditions.

### In Scope

- Expanding automated tests for the shared environment variable name validation rules used
  when users create or rename variable keys.
- Documenting expected outcomes for edge-case inputs as part of the task artifacts (dev
  docs in Step 7 if policy changes are needed).
- Aligning test expectations with the product rule: names must be compatible with Jinja2
  template use in PyPost.

### Out of Scope

- Rewriting validation logic unless a failing edge-case test proves incorrect behavior
  (any rule change is a separate decision).
- Integration or GUI flow tests (PYPOST-475 / existing presenter tests remain separate).
- Centralizing validation (PYPOST-478 — done).
- Error-message deduplication, logging levels, or metrics (PYPOST-472, PYPOST-473,
  PYPOST-479).
- Changing how existing stored variables are validated on load (validation applies to new
  name entry only, per PYPOST-163 scope).

### Constraints and Assumptions

- Validation rules today: non-empty; cannot start with a digit; only letters, digits, and
  underscore in the name (user-facing messages already defined for each failure type).
- Product documentation once described ASCII-only names while some Unicode letter names may
  still be accepted in practice; this task must clarify the intended policy through tests
  and Q&A rather than leave the ambiguity open.
- Whitespace trimming, if any, may occur in UI layers before validation; tests should
  reflect the strings passed into the shared validator unless a separate story covers
  trim behavior.
- PYPOST-474 was consolidated into PYPOST-477; PYPOST-470 narrows to the edge-case gaps
  still listed under PYPOST-163 follow-up, not re-testing the entire baseline matrix.

## Functional Requirements

- The product must continue to reject empty variable names with the empty-name message.
- The product must continue to reject names starting with a digit with the
  starts-with-digit message.
- The product must continue to reject names containing disallowed characters (spaces,
  punctuation, symbols outside underscore) with the invalid-characters message.
- The product must define and verify behavior for Unicode inputs: which Unicode letter
  names are accepted, which Unicode symbols or combining marks are rejected, and how that
  relates to safe Jinja2 variable use.
- The product must define and verify behavior for mixed strings where only part of the
  input satisfies the rules (invalid character embedded after valid prefix, multiple failure
  types with a single canonical reason returned).
- The product must define and verify boundary behavior for shortest valid names, long valid
  names, and edge inputs adjacent to rule thresholds (without changing user-visible limits
  unless a defect is found).

## Non-functional Requirements

- **Reliability**: edge-case tests run in CI on every change touching validation or its
  consumers.
- **Clarity**: test names and grouped cases make the intended policy readable without
  reading implementation details.
- **Maintainability**: new edge cases build on the PYPOST-477 baseline without duplicating
  obvious happy-path or already-covered invalid scenarios.
- **Performance**: not applicable — validation remains lightweight; no performance targets
  for this task.

## Main Entities and Interactions

| Entity | Attributes | Role |
|--------|------------|------|
| **Environment variable name** | proposed name, accepted/rejected status | User-chosen key used in templates and environment storage; subject to validation on create/rename. |
| **Validation outcome** | accept/reject, failure reason | Accept or reject with a specific user-facing reason (empty, starts with digit, invalid characters). |
| **Jinja2 template usage** | variable name reference | Consumer context that motivates which names are considered valid in PyPost. |
| **Automated test suite** | input cases, expected outcomes | Records expected outcomes for edge inputs and guards against regressions. |

Interaction overview:

1. User proposes a variable name in a create/rename flow.
2. Shared validation evaluates the name against Jinja2-compatible rules.
3. User sees success or a specific error; templates must work for accepted names.
4. Automated tests assert outcomes for Unicode, mixed, and boundary inputs so future edits
   preserve user-visible behavior.

## Q&A

- **Q:** Why is this task separate from PYPOST-477 if baseline tests already exist?  
  **A:** PYPOST-477 delivered broad branch coverage and a small Unicode sample.
  PYPOST-163 review still called out Unicode policy vs Jinja2, mixed strings, and
  boundaries as under-tested; PYPOST-470 closes that specific debt.

- **Q:** Should Unicode letters (for example café, 变量, über) be accepted?  
  **A:** Current baseline coverage treats some as valid; this task must add enough Unicode
  cases — accepted and rejected — to state the intended product policy explicitly and
  ensure it matches Jinja2-safe usage. If policy should be ASCII-only, that is a product
  decision to record when tests expose the mismatch.

- **Q:** What counts as a “mixed valid/invalid” string?  
  **A:** Names where some characters satisfy the rules and others do not, such as
  `api_key!`, `valid-name`, `a b`, or `letter1emoji` — the validator must reject with the
  correct single primary reason (invalid characters vs starts-with-digit vs empty).

- **Q:** What boundary conditions matter for users?  
  **A:** Single-character valid names, very long but otherwise valid names, names that are
  only underscores, names immediately above typical length limits, and inputs that are
  empty or visually blank — each should have an expected accept/reject outcome recorded in
  tests.

- **Q:** Does this task change UI error text?  
  **A:** Not by default. Scope is verification and documentation of existing messages and
  reasons unless a test proves incorrect behavior.

- **Q:** Source of truth for scope?  
  **A:** Jira PYPOST-470 summary/description, `ai-tasks/PYPOST-163/60-tech-debt.md` item
  163-1, variable validation dev docs, and the existing validation test suite from
  PYPOST-477.
