# PYPOST-453: Align and enforce nested-function policy

## Goals

Users who compose template expressions need **clear, predictable rules** for whether they
may chain allow-listed functions inside a single placeholder (for example, encoding a
value and then hashing it in one expression). Today the product **behaves** as if such
nesting is allowed, but earlier design notes described nesting as unsupported. That
mismatch creates confusion for maintainers and risks silent drift in future work.

This task exists to **document the agreed** nested-function policy, **align** all
product-facing and maintainer-facing descriptions with that decision, and **enforce** it
so valid nested chains keep working and invalid forms stay rejected—without widening the
approved function surface.

## Programming Language

Python (pypost codebase).

## User Stories

- **As a pypost user**, I want to chain allow-listed functions in one placeholder (for
  example, a hash of an encoded variable), so I can compose transformations inline without
  extra steps.
- **As a pypost user**, I want nested chains to behave the same everywhere function
  placeholders are evaluated (request rendering and hover preview), so I trust what I see
  before I send a request.
- **As a maintainer**, I want one agreed product rule for nested calls, documented and
  enforced consistently, so future changes do not silently contradict prior behavior or
  architecture notes.
- **As a security reviewer**, I want nested calls limited to the same allow-listed
  catalog and argument rules as single-level calls, so nesting does not introduce
  arbitrary code execution or expand the callable surface.

## Definition of Done

1. **Product policy is explicit:** allow-listed nested function calls are **allowed**. A
   top-level function call may use a single argument that is either a plain variable name
   or another allow-listed function call with the same rules applied recursively. There is
   no fixed depth limit as long as each call in the chain satisfies catalog and
   single-argument rules.
2. **Artifacts are aligned:** requirements, architecture notes, developer documentation,
   and maintainer guidance **agree** on this policy. There are no remaining contradictory
   statements that nested calls are out of scope or must always fail validation.
3. **Existing valid nested templates keep working:** users who already rely on supported
   nested chains (for example `{{md5(urlencode(db))}}`) see **no unexpected breakage**
   where the product currently succeeds.
4. **Unsupported forms stay rejected predictably:** unknown functions, invalid syntax,
   wrong argument count, and non-catalog arguments remain invalid. Nesting does **not**
   bypass catalog or argument restrictions.
5. **Acceptance checks guard the policy:** automated checks confirm at least:
   - representative **valid** nested allow-listed chains are accepted;
   - representative **invalid** nested forms are rejected;
   - **parity** across every user-facing context where function placeholders are already
     supported (including request rendering and hover preview) for the same nested inputs.
   Policy-level invalid cases for this task are: unknown functions, wrong argument count,
   and arguments that are neither a plain variable nor an allow-listed nested call.
   Malformed formatting, spacing variants, and deep malformed nesting edge cases remain
   [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454).
6. The outcome is traceable to Jira
   [PYPOST-453](https://pypost.atlassian.net/browse/PYPOST-453) and the PYPOST-450
   follow-up chain (PYPOST-451, PYPOST-452 completed; PYPOST-454 related).

## Task Description

### Problem Statement

Architecture and implementation disagree about nested function-call policy. The running
product accepts nested allow-listed calls, while earlier architecture for PYPOST-450
stated that nested calls were not in scope and should fail validation. Documentation
partially reflects current behavior but still marks the area as a known deviation pending
alignment.

### Scope

**In scope:**

- Adopt and document the product policy: **allow** nested allow-listed function calls.
- Align maintainer and product documentation so nested policy is no longer ambiguous.
- Enforce the policy through explicit validation rules and acceptance checks so drift is
  detectable.

**Out of scope:**

- Adding new functions to the catalog.
- Multi-argument function calls (still unsupported).
- Arbitrary user-provided Python execution.
- Comprehensive edge-case testing for malformed nesting, spacing variants, and hover
  parity beyond policy alignment — covered by
  [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454).

### Constraints and Assumptions

- Constraint: this step documents **what** the product must guarantee, not **how** it is
  implemented.
- Constraint: backward compatibility for existing valid nested templates is mandatory.
- Constraint: nesting must not widen security exposure beyond the existing allow-listed
  catalog and single-argument model.
- Assumption: users already understand single-level function placeholders from PYPOST-450;
  nesting extends that model rather than introducing a separate interaction pattern.
- Assumption: prior work (PYPOST-451 catalog ownership, PYPOST-452 validation separation)
  is complete and provides the baseline behavior to align against.

### Main Entities and Interactions (Business Perspective)

- **User** — configures expressions in contexts that already support variables and
  functions.
- **Expression placeholder** — user text inside `{{ ... }}` delimiters in request fields.
- **Function call** — a named call from the product-managed allow-list with one argument.
- **Nested function chain** — a function call whose argument is another allow-listed
  function call rather than a bare variable.
- **Policy rule** — the product decision that such chains are supported when every call
  in the chain complies with catalog and argument rules.
- **Validation outcome** — accepted or rejected; for end users, invalid placeholders
  continue to follow the same fallback experience as today (no new hard failures where
  the product currently degrades gracefully).

Interaction flow:

1. User writes a placeholder that chains allow-listed functions.
2. Product evaluates whether each call in the chain complies with catalog and argument
   rules.
3. If valid, the chain resolves like other supported placeholders across runtime and
   preview contexts.
4. If invalid, the product rejects the placeholder under the same predictable rules as
   single-level invalid calls.

## Non-Functional Requirements

- **Consistency:** nested policy applies uniformly in every context where variables and
  functions are already supported.
- **Predictability:** users and maintainers can state unambiguously whether nesting is
  supported without reading conflicting documents.
- **Stability:** aligning documentation and enforcement must not break working nested
  templates.
- **Security:** nested chains use only the approved function catalog; nesting must not
  enable arbitrary code execution or calls outside the catalog.

## Q&A

| Question | Answer |
|----------|--------|
| Allow or reject nested calls? | **Allow** allow-listed nested function calls. |
| Why allow instead of rejecting per early PYPOST-450 architecture? | Product decision: chaining transformations is useful; the live product already supports it; rejecting would break existing valid templates. |
| What is the boundary with PYPOST-454? | PYPOST-453 owns policy decision, documentation alignment, and enforcement acceptance checks. PYPOST-454 owns detailed edge-case tests (malformed nesting, spacing variants, hover/runtime parity for edge forms). |
| Does UX change for invalid nested placeholders? | No unexpected change: invalid forms remain invalid with the same user-visible fallback behavior as today. |
| Does nesting change the function catalog? | No. Only existing allow-listed functions may appear at any depth in a chain. |
| Is there a maximum nesting depth? | No fixed limit. Each call in the chain must use an allow-listed function with a single argument that is either a plain variable or another valid nested call. |
| Who is the primary audience for this work? | Maintainers and contributors; end users benefit through clearer rules and stable nested-chain behavior. |
| Source of this task? | Follow-up from [PYPOST-450 technical-debt analysis](ai-tasks/PYPOST-450/60-tech-debt.md); Jira [PYPOST-453](https://pypost.atlassian.net/browse/PYPOST-453). |
