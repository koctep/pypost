# PYPOST-1538: One header-selector prefix

## Goals

A person who writes a header selector must have that selector recognized the
same way in three places: when it is validated, when it selects response data,
and when sensitive header text is sanitized.

The prefix that marks a header selector is one agreement. Validation,
selection, and sanitization each keep their own spelling of that prefix today.
A later edit can change one spelling and leave the others behind. The person
can then be told the selector is valid while the named header is left
unselected, or while its sensitive text stays visible. That split can ship
with nobody noticing.

This task makes that prefix one agreement shared by the three uses, and it
makes a divergence of the agreement visible. Masking stays trustworthy: the
header the person named is the header the product validates, selects, and
sanitizes.

**Implementation language:** Python

## User Stories

- As a **person configuring response masking**, I want a header selector I
  write to be recognized the same way when it is checked, when it selects
  response data, and when sensitive header text is sanitized, so the header I
  named is the header that is protected.
- As a **person protecting credentials in response headers**, I want the
  prefix that marks a header selector to be one agreement, so validation,
  selection, and sanitization use the same marker.
- As a **maintainer of masking behavior**, I want a divergence of that prefix
  to be caught, so the three uses stay on one agreement.

## Definition of Done

This task is done when all of the following are true:

1. Validation, response-data selection, and sensitive-header sanitization
   share one header-selector prefix.
2. A selector written with that prefix is recognized as a header selector in
   all three uses: it validates as a header selector, it selects response
   header data, and it sanitizes that header's sensitive text.
3. The prefix is one agreement shared by the three uses. Separate spellings
   that only happen to match are short of this agreement.
4. If any of the three uses stops recognizing that same prefix, the
   divergence is caught. The split is visible before it can pass unnoticed.
5. Header selectors people already rely on, such as `header:Authorization`,
   keep their current meaning under that shared prefix.

## Task Description

### Problem

People name a response header to mask by writing a header selector. A prefix
on that text tells a header selector from a body-field selector. Three uses
must honor the same prefix:

- **Validation** tells the person whether the text is a header selector.
- **Selection** uses it to choose response header data.
- **Sanitization** uses it to redact the sensitive text of the named header.

Each use currently spells that prefix on its own. Nothing holds the spellings
to one agreement, and nothing reports when they differ. The gap is follow-up
2 in [PYPOST-1387 technical debt](ai-tasks/PYPOST-1387/60-tech-debt.md)
(the header-prefix item near lines 78-80) together with the missing-test note
on the header prefix. The work is tracked by
[PYPOST-1538](https://pypost.atlassian.net/browse/PYPOST-1538).

That parent note left two endings open: compare the three spellings, or keep
one shared spelling. This task closes the fork. The ending is one shared
prefix, and a caught divergence. A comparison of three private spellings
leaves three agreements. A shared spelling that one use can bypass with no
signal still lets the split ship unnoticed. Either leftover fails the
outcome: the three uses cannot drift apart unnoticed.

### Scope

- One header-selector prefix shared by validation, response-data selection,
  and sensitive-header sanitization.
- The same recognition of that prefix in all three uses.
- A catch for divergence, so a later change that splits the three uses is
  visible.
- The header-selector meaning people already rely on stays in place.

### Out of Scope

- Rejecting a literal `..` draft
  ([PYPOST-1539](https://pypost.atlassian.net/browse/PYPOST-1539)).
- Specialized explanations for particular unsupported forms
  ([PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540)).
- Open-edit warning and advisory accept
  ([PYPOST-1537](https://pypost.atlassian.net/browse/PYPOST-1537), already
  done).
- Changing which selector forms are supported, beyond locking the
  header-selector prefix those forms already use.
- Changing which header names are sensitive when the person left them
  unnamed.
- Autocomplete, selector deduplication, and per-row enable controls.

### Functional Requirements

- **FR1: One prefix.** The prefix that marks a header selector is a single
  agreement. Validation, selection, and sanitization use that agreement.
- **FR2: Same recognition.** A selector written with that prefix is a header
  selector for validation, for selecting response data, and for sanitizing
  sensitive header text.
- **FR3: Caught divergence.** A change that makes one of the three uses
  recognize a different prefix is caught. The three uses stay aligned, and a
  split is visible.
- **FR4: Stable meaning.** An existing header selector such as
  `header:Authorization` remains a header selector under the shared prefix.
  It still selects that header's data and still takes part in sanitizing
  that header's sensitive text.

### Non-Functional Requirements

- **NFR1: Trust.** Validation, selection, and sanitization agree on the
  prefix, so a selector marked valid is a selector the other two uses honor.
- **NFR2: Visible split.** People who maintain the product see a divergence
  of the prefix. The split surfaces before a header value leaks or the wrong
  data is selected.
- **NFR3: Quality gates.** The change passes the repository quality gate
  (`make check`).

### Constraints and Assumptions

- The prefix people write today stays the prefix. This task keeps that
  marker and leaves the typed form unchanged.
- Sharing one prefix means one agreement used by all three uses. Where that
  agreement lives is an architecture choice. Requirements stop at the shared
  prefix and the caught divergence.
- Catching divergence means a split of that agreement is detected. The
  detection mechanism is an architecture choice.
- Letter case of the prefix is part of the agreement. The three uses
  recognize that case in the same way.
- Empty header names, body-path grammar, and the open editor stay with the
  tasks listed under Out of Scope.

## Entities

- **Header selector**: Text a person writes to name a response header to
  mask, marked by the header-selector prefix. Example:
  `header:Authorization`.
- **Header-selector prefix**: The single marker that distinguishes a header
  selector from a body-field selector.
- **Validation**: The check that tells the person whether the text is a
  recognized header selector.
- **Selection**: Using the selector to choose response header data.
- **Sanitization**: Redacting the sensitive text of the header the selector
  names.
- **Divergence**: One of the three uses recognizing a different prefix than
  the shared agreement.

## Q&A

### Q1: Why is this needed?

**A**: A person who writes a header selector is naming a response header
whose value must be protected. The prefix is the agreement that this text is
a header selector. When validation, selection, and sanitization share that
prefix, the header the person named is the header that is checked, selected,
and sanitized. A split among the three can leave the value visible, or can
select different data than the person configured, and can ship unnoticed.

### Q2: What ending closes the test-versus-constant fork?

**A**: The three uses share one prefix, and a divergence of that prefix is
caught. That is the only ending. Comparing three private spellings leaves
the prefix as three agreements. A single spelling with no catch still allows
one use to drift unnoticed. Both miss the outcome that the uses cannot drift
apart unnoticed.

### Q3: What stays true for a header selector people already write?

**A**: `header:Authorization` stays a header selector. It is still accepted,
still applied to that response header, and still used when that header's
sensitive text is sanitized. Body paths, empty-name explanations, and the
open editor stay as they are.

### Q4: What is out of scope?

**A**: Literal `..` rejection (PYPOST-1539), specialized invalid messages
(PYPOST-1540), and open-edit chrome (PYPOST-1537, already done).

### Q5: What programming language is used?

**A**: Python.
