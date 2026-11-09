# PYPOST-1539: Reject a broken double-dot field selector

## Goals

A person writing a field selector must be told the truth about the text they
wrote. Those selectors decide which response fields are masked. A broken
draft such as `users..email` is not a field they named. Two dots in a row
leave an empty step in the path. The product must not call that draft
acceptable.

The product can call it acceptable today because cleanup that keeps a
deliberate whole-element form readable also collapses the extra dot. The
person is then shown a healthy selector while the text they wrote still
contains the double dot. They can believe a response field will be masked
when the written selector is not a supported form. Masking configuration is
trustworthy only when "acceptable" means the text they wrote.

A deliberate whole-element form such as `users[*].email` stays acceptable.
That form is how a person names every element's field. Tightening the check
must not treat that deliberate form as broken.

**Implementation language:** Python

## User Stories

- As a **person writing a field selector**, I want a broken draft such as
  `users..email` rejected, so I am not told a typo is an acceptable masking
  rule.
- As a **person writing a field selector**, I want a deliberate whole-element
  form such as `users[*].email` to stay acceptable, so naming every element's
  field still works.

## Definition of Done

This task is done when both of the following are true:

1. The broken double-dot draft `users..email` is rejected. The person is not
   told that draft is acceptable.
2. The deliberate whole-element form `users[*].email` stays acceptable.

## Task Description

### Problem

People name response fields to mask by writing field selectors. A broken
draft with two dots in a row, `users..email`, leaves an empty step in the
path. That text is not a supported selector. The product still treats it as
acceptable, because cleanup that supports the whole-element form also
collapses the extra dot. The written text still contains the double dot, and
the person is shown that the draft is fine.

The deliberate form `users[*].email` names every element's email. That form
must remain acceptable. The false reading is the broken double-dot draft.

The gap is follow-up 3 in
[PYPOST-1387 technical debt](ai-tasks/PYPOST-1387/60-tech-debt.md) (the
literal `..` item near lines 81-84). The work is tracked by
[PYPOST-1539](https://pypost.atlassian.net/browse/PYPOST-1539).

### Scope

- A broken double-dot field-selector draft is not acceptable.
- The acceptance example of that rejection is `users..email`.
- A deliberate whole-element form stays acceptable.
- The acceptance example of that acceptance is `users[*].email`.

### Out of Scope

- Specialized explanations for particular unsupported forms
  ([PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540)).
- The shared header-selector prefix
  ([PYPOST-1538](https://pypost.atlassian.net/browse/PYPOST-1538), already
  done).
- Open-edit warning and advisory accept
  ([PYPOST-1537](https://pypost.atlassian.net/browse/PYPOST-1537), already
  done).
- Autocomplete, selector deduplication, and per-row enable controls.

### Functional Requirements

- **FR1: Honest double-dot verdict.** A broken double-dot draft is rejected,
  and a deliberate whole-element form stays acceptable. `users..email` is
  the rejected example. `users[*].email` is the accepted example.

### Non-Functional Requirements

- **NFR1: Trust.** "Acceptable" describes the selector the person wrote. A
  broken draft is not presented as healthy because cleanup hid the extra
  dot.
- **NFR2: Quality gates.** The change passes the repository quality gate
  (`make check`).

### Constraints and Assumptions

- This is one requirement. The broken draft is rejected and the
  whole-element form stays acceptable. There is no second ending.
- How the product distinguishes the broken draft from the whole-element form
  is an architecture choice. Requirements name the two examples and the
  verdict for each.
- The wording of the rejection stays as it is today. Specialized messages
  are PYPOST-1540.
- Header-prefix agreement and open-edit chrome stay with the tasks listed
  under Out of Scope.

## Entities

- **Field selector**: Text a person writes to name a response field to mask.
- **Broken double-dot draft**: A field selector with an empty step between
  two dots. Acceptance example: `users..email`.
- **Whole-element form**: A deliberate field selector that names every
  element of a list. Acceptance example: `users[*].email`.
- **Verdict**: What the person is told about the selector they wrote:
  acceptable, or rejected.

## Q&A

### Q1: Why is this needed?

**A**: A person writing a field selector is deciding which response fields
are masked. If a broken draft such as `users..email` is called acceptable,
they can believe the email field is protected when the text they wrote is
not a supported selector. The false reading happens because internal cleanup
that supports the whole-element form also collapses the extra dot. Trust
requires the verdict to match the text they wrote.

### Q2: What is the decided requirement?

**A**: One requirement. The broken double-dot draft `users..email` is
rejected. The deliberate whole-element form `users[*].email` stays
acceptable. No other ending is open.

### Q3: What is out of scope?

**A**: Specialized invalid messages (PYPOST-1540), the shared header prefix
(PYPOST-1538, already done), and open-edit chrome (PYPOST-1537, already
done).

### Q4: What programming language is used?

**A**: Python.
