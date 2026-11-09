# PYPOST-1540: Name the unsupported field-selector kind

## Goals

A person writing a field selector is choosing which response fields are
masked. When the draft is unsupported, the product warns them. That warning
is the same for every bad draft. It does not say whether they wrote a
JSONPath dollar, a numeric index, or a filter.

Those three forms are familiar ways to name a field, and this product
rejects them. A shared warning leaves the person guessing which habit
caused the problem, so they can leave a masking rule that will not protect
the field they meant. The warning stays guidance. A valid selector such as
`token` stays free of a warning.

This task is follow-up 4 in
[PYPOST-1387 technical debt](ai-tasks/PYPOST-1387/60-tech-debt.md) (the
specialized invalid-message item near lines 85-87). The work is tracked by
[PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540).

**Implementation language:** Python

## User Stories

- As a **person writing a field selector**, I want a draft that uses a
  JSONPath dollar, a numeric index, or a filter to explain that kind of
  problem, so I know what to change before I rely on the masking rule.
- As a **person writing a field selector**, I want a valid selector such as
  `token` to stay free of a warning, so a correct masking rule stays quiet.

## Definition of Done

This task is done when all of the following are true:

1. The JSONPath-dollar draft `$.token` carries an explanation of that kind.
2. The numeric-index draft `users[0].email` carries an explanation of that
   kind.
3. The filter draft `users[?(@.active)].email` carries an explanation of
   that kind.
4. The three explanations differ from each other, and each differs from the
   single generic warning used for every bad draft.
5. The valid selector `token` gets no warning.

## Task Description

### Problem

People name response fields to mask by writing field selectors. A draft
that uses a JSONPath dollar, a draft that picks an element by a numeric
index, and a draft that filters elements are all unsupported. Today each of
them receives the same generic warning. The person cannot tell which kind
they typed.

A valid selector such as `token` already gets no warning. That stays true.

The parent work already warns on unsupported drafts. This task only splits
that warning for the three kinds above.

### Scope

- An unsupported draft that uses a JSONPath dollar gets its own
  explanation. The example is `$.token`.
- An unsupported draft that uses a numeric index gets its own explanation.
  The example is `users[0].email`.
- An unsupported draft that uses a filter gets its own explanation. The
  example is `users[?(@.active)].email`.
- Each explanation identifies its own kind.
- A valid selector gets no warning. The example is `token`.

### Out of Scope

- The double-dot reject
  ([PYPOST-1539](https://pypost.atlassian.net/browse/PYPOST-1539), done).
- The shared header-selector prefix
  ([PYPOST-1538](https://pypost.atlassian.net/browse/PYPOST-1538), done).
- Open-edit chrome
  ([PYPOST-1537](https://pypost.atlassian.net/browse/PYPOST-1537), done).
- Autocomplete, selector deduplication, and per-row enable controls.
- A new explanation for an unsupported draft that is neither a JSONPath
  dollar, nor a numeric index, nor a filter.

### Functional Requirements

- **FR1: Kind-specific warning.** A person who types an unsupported field
  selector is told which kind of problem it is when the draft uses a
  JSONPath dollar, a numeric index, or a filter. `$.token`,
  `users[0].email`, and `users[?(@.active)].email` are the three examples.
  A valid selector such as `token` gets no warning.

### Non-Functional Requirements

- **NFR1: Plain language.** The explanation names the kind of problem in
  words a person writing selectors can use, without internal engine names.
- **NFR2: Quality gates.** The change passes the repository quality gate
  (`make check`).

### Constraints and Assumptions

- This is one requirement. The three unsupported kinds each carry their own
  explanation, and `token` gets no warning. There is no second ending.
- Requirements name the kinds and the four examples. They leave the
  sentences of the explanations to a later step.
- The warning stays guidance. The person can keep the draft and keep
  editing.
- Acceptance uses one kind per example. A draft that mixes a dollar, an
  index, and a filter is outside this requirement.
- An unsupported draft that is none of the three kinds keeps the warning it
  has today.
- The double-dot reject, the shared header prefix, and open-edit chrome
  stay with the tasks listed under Out of Scope.

## Entities

- **Field selector**: Text a person writes to name a response field to mask.
- **JSONPath-dollar draft**: An unsupported field selector that uses a
  JSONPath dollar. Example: `$.token`.
- **Numeric-index draft**: An unsupported field selector that picks one
  element by a number. Example: `users[0].email`.
- **Filter draft**: An unsupported field selector that keeps elements by a
  condition. Example: `users[?(@.active)].email`.
- **Valid selector**: A supported field selector. Example: `token`.
- **Explanation**: What the person is told about an unsupported draft. Each
  of the three kinds has its own. A valid selector has none.

## Q&A

### Q1: Why is this needed?

**A**: A person writing a field selector is deciding which response fields
are masked. A JSONPath dollar, a numeric index, and a filter are three
familiar unsupported forms. One generic warning does not say which form
they typed, so they can leave a masking rule that will not protect the
field they meant. A valid selector such as `token` still gets no warning.

### Q2: What is the decided requirement?

**A**: One requirement. `$.token`, `users[0].email`, and
`users[?(@.active)].email` each carry their own explanation of that kind.
`token` gets no warning. No other ending is open.

### Q3: What is out of scope?

**A**: The double-dot reject (PYPOST-1539, done), the shared header prefix
(PYPOST-1538, done), and open-edit chrome (PYPOST-1537, done).

### Q4: What programming language is used?

**A**: Python.
