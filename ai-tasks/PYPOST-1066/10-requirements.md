# PYPOST-1066: Verify clean mypy baseline boundaries

## Goals

PyPost's mypy baseline gate helps contributors distinguish accepted type-checking debt from changes
that require attention. Maintainers need confidence that the gate remains reliable at its cleanest
boundaries: when neither the current run nor the baseline contains errors, and when the current run
is clean because every previously accepted error has been fixed.

Those boundaries currently lack focused automated coverage. A regression could incorrectly report
a difference for two clean inputs or silently treat a fully resolved baseline as ordinary success,
leaving stale debt recorded. The business goal is predictable gate behavior that recognizes a
genuinely clean state while still drawing attention to a baseline that should be updated after all
known errors are fixed.

**Implementation language**: Python.

## User Stories

- As a contributor with a clean mypy run and a clean baseline, I want the comparison to report no
  difference so that the gate does not create a false failure.
- As a maintainer whose current mypy run has fixed every baselined error, I want the gate to identify
  the complete resolution so that the stale baseline is not mistaken for current debt.
- As a maintainer, I want automated regression coverage for both boundary states so that later gate
  changes preserve correct pass/fail and diagnostic behavior.

## Definition of Done

- Automated verification confirms that comparing an empty current error set with an empty baseline
  reports neither new nor fixed differences.
- Automated verification exercises the complete gate flow when the current run contains zero mypy
  errors and the baseline contains one or more previously accepted errors.
- In the fully fixed scenario, the gate reports the baselined errors as resolved, requests baseline
  maintenance, and does not report any newly introduced error.
- In the fully fixed scenario, the gate does not report ordinary baseline success while stale
  baseline entries remain.
- The focused checks run as part of the existing automated test suite and comply with the project's
  test timeout policy.
- Existing behavior outside these clean and fully fixed boundaries remains unchanged.

## Task Description

PYPOST-1007 strengthened the mypy baseline comparison and its technical-debt review identified two
related missing boundary checks. PYPOST-1066 closes that gap by verifying both the degenerate clean
comparison and the user-visible gate outcome after all historical type errors have been resolved.

### Scope

- Verification of comparison behavior when both sides contain zero errors.
- Verification of the complete gate behavior for zero current errors against a non-empty baseline.
- Verification that fully resolved historical errors remain actionable until the baseline is
  brought into agreement with the clean current state.
- A behavior correction only if the specified verification reveals that the established gate
  contract is not met.

### Out of Scope

- Changes to the mypy error identity, duplicate-occurrence semantics, or line-shift handling.
- Changes to the baseline data format, error parsing, path scope, or baseline-generation workflow.
- Coverage of report-formatting qualifiers, legacy baseline rejection, or path-scope synchronization.
- Broad cleanup of existing type errors or regeneration of the repository's committed baseline.

### Constraints and Assumptions

- A non-empty baseline with zero current errors represents fully resolved historical debt, not an
  invalid or missing current run.
- Resolved baseline entries require an actionable gate result so maintainers update the recorded
  debt rather than silently retaining stale entries.
- This is a verification-focused follow-up and production behavior is expected to remain unchanged
  unless the new checks expose a mismatch.
- The source is follow-up 2 in `ai-tasks/PYPOST-1007/60-tech-debt.md`.

## Main Entities and Interactions

| Entity | Business role |
| --- | --- |
| Current mypy result | The type-checking findings present in the contributor's current code |
| Mypy baseline | The previously accepted findings used as the comparison point |
| New difference | A current finding that was not accepted in the baseline |
| Resolved difference | A baselined finding that is absent from the current result |
| Gate outcome | The pass/fail and diagnostic signal that directs contributor action |

The current mypy result is compared with the baseline. Two empty collections produce no
differences. A clean current result compared with a non-empty baseline produces only resolved
differences, which the gate communicates as required baseline maintenance rather than ordinary
success.

## Non-Functional Requirements

- **Reliability**: verification must distinguish clean agreement from a clean current result with a
  stale non-empty baseline.
- **Determinism**: the same current result and baseline must always produce the same gate outcome.
- **Maintainability**: failures must clearly identify which boundary contract was violated.
- **Performance**: focused checks must remain fast enough for routine execution in the existing
  suite.
- **Security**: verification requires no credentials, network access, or sensitive data.

## Q&A

### Why is a clean current run with a non-empty baseline not ordinary success?

The code is clean, but the recorded baseline is stale. Calling that state ordinary success would
hide completed debt reduction and allow obsolete entries to remain committed. The gate should make
the required baseline maintenance visible.

### Why verify the empty-to-empty comparison separately?

It is the true no-debt boundary. Direct coverage prevents future comparison changes from producing
false new or resolved differences when both inputs are clean.

### Is this task intended to change the gate policy?

No. It protects the established distinction between no differences and resolved historical debt.
A production change is warranted only if focused verification shows that distinction is broken.
