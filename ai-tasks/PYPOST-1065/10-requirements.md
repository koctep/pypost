# PYPOST-1065: Verify mypy baseline report formatting

## Goals

PyPost's mypy baseline gate distinguishes newly introduced type-checking
errors from errors already known to the project and reports errors that have
been fixed. Maintainers rely on that report to understand whether a change
adds type risk, reduces existing debt, or merely changes the number of
occurrences of a known error.

The report-formatting behavior currently lacks focused automated coverage.
A regression could therefore show misleading occurrence counts, unnecessary
qualifiers, or an unstable line order even while the underlying comparison is
correct. The business goal is stable, regression-resistant mypy gate reporting
that lets maintainers quickly and accurately interpret type-checking changes.

**Implementation language**: Python.

## User Stories

- As a maintainer reviewing a mypy gate failure, I want a partially new error
  to state how many occurrences are new out of the current total, so that I
  can understand the size of the regression.
- As a maintainer reviewing resolved type debt, I want a partially fixed error
  to state how many occurrences remain baselined out of the previous total,
  so that I can understand the amount of progress without mistaking it for a
  complete fix.
- As a maintainer, I want entirely new and entirely fixed errors reported
  without a redundant partial-occurrence qualifier, so that reports remain
  concise and unambiguous.
- As a maintainer investigating newly reported occurrences, I want source line
  numbers presented in ascending order, so that the report is predictable and
  easy to scan.
- As a contributor, I want automated verification of these reporting rules so
  that future changes cannot silently degrade the mypy gate's diagnostics.

## Definition of Done

- Automated verification covers a partially new error and confirms the report
  expresses `N new of M total` with accurate counts.
- Automated verification covers a partially fixed error and confirms the
  report expresses `N of M baselined` with accurate counts.
- Automated verification confirms that the partial-occurrence qualifier is
  omitted when every current occurrence is new.
- Automated verification confirms that the partial-occurrence qualifier is
  omitted when every baselined occurrence is fixed.
- Automated verification confirms that line numbers in a new-error report are
  presented in ascending numerical order regardless of their input order.
- The focused verification runs as part of the existing automated test suite
  and follows the project's timeout requirements.
- Existing user-visible mypy report behavior remains unchanged; this task
  protects the established contract and only requires behavioral changes if
  verification exposes a defect.

## Task Description

PYPOST-1007 introduced report behavior that distinguishes partial occurrence
changes from whole-key changes. Its technical-debt review found that the
display contract is not directly verified. This task closes that gap for the
new-error and fixed-error reports.

### Scope

- Verification of partial-new occurrence wording and counts.
- Verification of partial-fixed occurrence wording and counts.
- Verification that entirely new and entirely fixed cases omit partial-only
  wording.
- Verification that new-error line numbers are sorted ascending.
- A production correction only if the newly specified checks reveal that the
  established reporting contract is not currently met.

### Out of Scope

- Changes to how mypy errors are collected, parsed, or compared with the
  baseline.
- Changes to the baseline file format or baseline update workflow.
- Coverage of empty baselines, zero-error runs, legacy baseline rejection, or
  path-scope synchronization; those are separate concerns and follow-ups.
- New report fields, wording beyond the established occurrence qualifiers, or
  changes to the mypy gate's pass/fail policy.

### Constraints and Assumptions

- The established report wording and omission rules are the expected product
  behavior, not a request to redesign the output.
- The work is test-focused and is expected to be isolated from external
  services and environment-specific state.
- The source is PYPOST-1007 technical-debt follow-up 1, recorded in
  `ai-tasks/PYPOST-1007/60-tech-debt.md`.

## Main Entities and Interactions

| Entity | Business role |
| --- | --- |
| Current mypy error occurrence | A type-checking finding present in the current run |
| Baselined occurrence | A previously accepted occurrence used as the comparison point |
| New-error report | Communicates newly introduced occurrences to maintainers |
| Fixed-error report | Communicates resolved baselined occurrences to maintainers |
| Occurrence qualifier | Clarifies a partial change without cluttering whole-key changes |
| Source line number | Locates a current occurrence and provides a stable scan order |

Current occurrences are compared with baselined occurrences. The resulting new
and fixed groups are communicated through reports. Partial changes include the
relevant occurrence qualifier, whole-key changes omit it, and current source
locations appear in ascending order.

## Non-Functional Requirements

- **Reliability**: verification must detect incorrect counts, qualifier
  inclusion or omission, and line ordering.
- **Determinism**: the same occurrences must produce the same expected report
  independent of their supplied order.
- **Maintainability**: each reporting rule should be clear from the verification
  intent and failure output.
- **Performance**: focused checks must remain suitable for routine execution in
  the existing test suite.
- **Security**: no credentials, network access, or sensitive data are required.

## Q&A

### Why is this work needed if the comparison logic already has tests?

The comparison and the human-readable report are distinct contracts. Existing
coverage can prove which occurrences are new or fixed without detecting a
misleading count, redundant qualifier, or unstable line order in the report
that maintainers actually read.

### Why should qualifiers appear only for partial changes?

They explain the relationship between changed and total occurrences when some
instances remain known. For an entirely new or entirely fixed key, the same
qualifier adds no information and makes the report harder to scan.

### Why require ascending line order?

Stable source order makes multiple occurrences predictable to review and
prevents incidental input ordering from producing noisy reports.

### Is production behavior expected to change?

No. This is a verification-debt task. A production change is only warranted if
the focused checks demonstrate that the established contract is not satisfied.
