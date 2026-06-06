# PYPOST-454: Add edge-case tests for expression variants

## Goals

Users who write function placeholders — including nested allow-listed chains — should see
**consistent, predictable outcomes** whether an expression is evaluated during request
rendering or hover preview. After PYPOST-450 and PYPOST-453, policy and happy-path nested
coverage exist, but **edge-case acceptance checks** called out in the PYPOST-450 technical-debt
analysis remain missing.

This task exists to close that gap: add focused acceptance coverage for malformed nested
expressions, whitespace-heavy variants, and runtime/hover parity for those forms. The
primary deliverable is **test coverage** that guards against silent regression; product
behavior should remain as today unless an existing inconsistency is discovered and fixed.

## Programming Language

Python (pypost codebase).

## User Stories

- **As a pypost user**, I want spaced function placeholders (for example, extra spaces inside
  `{{ ... }}`) to resolve the same way in live rendering and hover preview, so what I see on
  hover matches what gets sent.
- **As a pypost user**, I want malformed nested placeholders to fail gracefully and
  consistently across contexts, so I am not surprised by different behavior in tooltips versus
  rendered requests.
- **As a maintainer**, I want automated checks for expression edge cases identified in
  PYPOST-450 technical debt, so future validation or parsing changes are guarded by tests.
- **As a security reviewer**, I want edge-case tests to confirm malformed or oddly formatted
  expressions still cannot bypass allow-list rules, so expanding test coverage does not widen
  the callable surface.

## Definition of Done

1. **Malformed nested expressions** are covered by acceptance checks: expressions where
   nested function structure is syntactically broken (for example, unbalanced or incomplete
   nesting) are verified to produce the same predictable rejection or fallback behavior as
   today.
2. **Spacing variants** are covered: whitespace-heavy forms (spaces inside delimiters, around
   function names, around arguments, including nested chains) are verified as **valid where the
   product already accepts them**, and as **invalid with consistent fallback where rejected**.
3. **Runtime/hover parity** is verified for the edge-case forms above: the same expression
   input yields the **same user-visible outcome** in request rendering, hover preview, and
   table-cell hover for the covered edge-case forms.
4. **No behavior change** unless an existing **runtime/hover parity** inconsistency is
   discovered; the primary deliverable is **test coverage**, not new product features. Any
   fix must be limited to restoring consistent user-visible outcomes for the covered edge-case
   forms.
5. Acceptance checks trace to the PYPOST-450 technical-debt items they close: malformed
   nested expressions, whitespace-heavy variants, and runtime/hover/table parity for those
   forms.
6. The outcome is traceable to Jira
   [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454) and the PYPOST-450 follow-up
   chain (PYPOST-451, PYPOST-452, PYPOST-453 completed; PYPOST-461 related).

## Task Description

### Problem Statement

PYPOST-453 resolved the nested-function policy mismatch and added policy-guard acceptance
checks for valid and invalid nested chains. Coverage gaps remain for edge-case expression
forms identified in
[PYPOST-450 technical-debt analysis](ai-tasks/PYPOST-450/60-tech-debt.md): malformed nested
expressions, whitespace-heavy variants, and runtime/hover parity for those cases.

### Scope

**In scope:**

- Acceptance coverage for malformed nested expressions (syntactically broken nesting).
- Acceptance coverage for whitespace-heavy expression variants, including nested chains and
  spaced forms such as `{{ md5( db ) }}`.
- Runtime/hover/table-cell parity checks for the edge-case forms above.

**Out of scope:**

- Adding new functions to the catalog.
- Changing nested-function policy (established by PYPOST-453).
- Internal refactors of rendering or validation orchestration (tracked separately).
- Expression or template caching improvements (tracked separately).
- Empty-argument calls and multi-placeholder first-failure stability —
  [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461).
- Observability changes (new logs or metrics).

### Constraints and Assumptions

- Constraint: this step documents **what** must be verified, not **how** tests are
  implemented.
- Constraint: backward compatibility for existing valid templates (including nested chains
  from PYPOST-453) is mandatory.
- Constraint: edge-case tests must not widen security exposure beyond the existing
  allow-listed catalog and single-argument model.
- Assumption: PYPOST-453 policy-guard tests provide the baseline; this task extends coverage
  to edge forms deferred from that work.
- Assumption: when validation or render fails, the product continues to use the existing
  backward-compatible fallback (return original placeholder content) unless a parity bug is
  found and fixed.

### Main Entities and Interactions (Business Perspective)

- **User** — writes placeholders in request fields and previews values via hover.
- **Expression placeholder** — user text inside `{{ ... }}` delimiters, optionally chaining
  allow-listed functions.
- **Evaluation context** — where placeholders resolve (request rendering versus hover preview).
- **Edge-case expression form** — a spacing-heavy or syntactically broken nested variant.
- **Fallback outcome** — product returns original token content when validation or render
  fails (existing backward-compatible behavior from PYPOST-450).

Interaction flow:

1. User writes a placeholder that uses spacing quirks or broken nested structure.
2. Product evaluates the placeholder in request rendering and hover preview contexts.
3. For valid edge forms, both contexts produce the same resolved value.
4. For invalid edge forms, both contexts produce the same predictable fallback (original
   content preserved).

## Non-Functional Requirements

- **Consistency:** the same expression produces the same user-visible outcome across runtime
  and hover for all covered edge cases.
- **Stability:** adding acceptance checks must not break existing valid templates, including
  nested chains validated by PYPOST-453.
- **Maintainability:** acceptance checks are focused and traceable to the PYPOST-450
  technical-debt items they close.
- **Security:** edge-case forms still respect allow-list and argument rules; tests confirm
  no bypass through formatting or nesting quirks.

## Q&A

| Question | Answer |
|----------|--------|
| Is this a feature or test task? | **Test-coverage debt task**; behavior should remain as today unless a parity bug is found. |
| What did PYPOST-453 cover vs. PYPOST-454? | PYPOST-453 = nested policy decision, documentation alignment, and policy-guard checks for valid/invalid nested chains. PYPOST-454 = edge-case matrix (malformed nesting, spacing variants, parity for those forms). |
| What is the boundary with PYPOST-461? | PYPOST-454 owns syntactically broken **nested structure** (unbalanced or incomplete nesting), whitespace-heavy variants, and runtime/hover/table parity for those forms. PYPOST-461 owns **empty-argument** calls, **multi-placeholder first-failure** behavior, and standalone malformed **closing-paren or arity** patterns that are not primarily nesting-structure cases. If a placeholder fits both (for example, a nested call with a missing closing parenthesis), PYPOST-454 covers parity for the nesting/spacing dimension; PYPOST-461 owns the empty-arg and multi-token matrix unless explicitly coordinated. |
| Are table cells in scope? | Yes — hover in table cells must behave the same as hover elsewhere for the covered edge-case forms. |
| Should UX change for invalid edge placeholders? | No unexpected change: invalid forms remain invalid with the same user-visible fallback as today. |
| Does this change the function catalog or nesting policy? | No. PYPOST-453 policy stands; this task only adds acceptance coverage. |
| Who is the primary audience? | Maintainers and contributors; end users benefit through consistent edge-case behavior and regression protection. |
| Source of this task? | Follow-up from [PYPOST-450 technical-debt analysis](ai-tasks/PYPOST-450/60-tech-debt.md); deferred from [PYPOST-453 technical-debt analysis](ai-tasks/PYPOST-453/60-tech-debt.md); Jira [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454). |
