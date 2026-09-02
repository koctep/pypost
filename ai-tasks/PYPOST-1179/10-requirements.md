# PYPOST-1179: Refresh the mypy baseline for known type-checking drift

## Goals

Restore a trustworthy `make typecheck` quality signal by ensuring the repository's recorded
baseline accurately represents the currently reported type diagnostics. The task addresses the
known drift involving stream-export snapshot typing and the Settings dialog layout contract,
without hiding new type regressions or expanding into unrelated cleanup.

## User Stories

- As a contributor, I want `make typecheck` to distinguish known technical debt from new type
  regressions, so that I can trust failures during development.
- As a maintainer, I want the baseline to reflect the current accepted diagnostic set, so that
  resolved or newly introduced findings are visible and actionable.
- As a reviewer, I want the two identified areas to have an explicit, evidence-based outcome, so
  that this debt item does not silently broaden beyond its stated scope.

## Definition of Done

1. The type-checking result for the stream-export snapshot area has been evaluated and the
   accepted baseline accurately reflects its verified outcome.
2. The type-checking result for the Settings dialog layout area has been evaluated and the
   accepted baseline accurately reflects its verified outcome.
3. `make typecheck` reports no unexplained baseline drift after the scoped work is complete.
4. New diagnostics are not concealed by the baseline refresh; any diagnostic outside the agreed
   scope remains separately identified for follow-up.
5. Existing runtime behavior and user-visible Settings and stream-export behavior remain
   unchanged.
6. The task documentation records the scoped findings, evidence, and any residual follow-up.
7. `make verify-ai-tasks` and `make lint` pass.

## Task Description

### Programming Language

Python.

### Problem

The repository's type-checking gate has known baseline drift rather than a trustworthy one-to-one
record of current diagnostics. The identified findings concern `StreamExportSnapshot` versus the
stream contract in `pypost/core/qt/websocket_stream_export_worker.py`, and the `layout()` versus
`addWidget` contract in `pypost/ui/dialogs/settings_dialog.py`.

### Scope

In scope:

- Investigating the two type-checking areas named by PYPOST-1179.
- Correcting the accepted baseline or the scoped type contracts when evidence shows that is
  required to make the gate truthful.
- Recording the resulting diagnostic status and any residual work.

Out of scope:

- Unrelated type-checking findings elsewhere in the repository.
- Broad refactoring, new product behavior, or Settings UI redesign.
- Changes to stream-export functionality beyond what is necessary to preserve its existing
  behavior while making the type-checking result truthful.
- Replacing the baseline gate or weakening its regression detection.

### Constraints and Assumptions

- The issue is a 3-point technical-debt task in the active CI and GUI Reliability sprint.
- Existing runtime behavior is the compatibility boundary.
- The baseline must continue to expose newly introduced diagnostics.
- Verification commands must be run through the repository's Make targets.
- Any findings outside the two named areas must remain explicitly separated from this task.

### Main Entities

| Entity | Business role | Relevant attributes |
| --- | --- | --- |
| Type-checking diagnostic | A reported compatibility or correctness finding | Location, category, message, known/novel status |
| Mypy baseline | The repository's accepted record of known diagnostics | Recorded findings, comparison outcome, scope |
| Stream export snapshot | A captured stream result consumed by export behavior | Entries, dropped-entry information, stream-compatible interface |
| Settings dialog | The user-facing settings surface whose layout is type-checked | Layout ownership, child widgets, existing behavior |
| Quality gate | The contributor-facing pass/fail signal | Command, result, unexplained drift |
| Follow-up item | Work intentionally left outside this task | Reason, affected area, tracking reference |

### Functional Requirements

- **FR-1:** The task shall evaluate the current type-checking diagnostics for both named areas.
- **FR-2:** The accepted baseline shall match the verified diagnostics for the agreed scope.
-
 **FR-3:** The quality gate shall continue to distinguish known findings from unexplained new
  findings.
- **FR-4:** Residual diagnostics outside the agreed scope shall be identified rather than
  silently absorbed into this task.
- **FR-5:** Existing stream-export and Settings dialog behavior shall remain functionally
  unchanged.

### Non-Functional Requirements

- **NFR-1 — Trustworthiness:** A passing gate must not depend on suppressing newly introduced
  diagnostics.
- **NFR-2 — Compatibility:** The user-visible behavior of the affected areas must be preserved.
- **NFR-3 — Traceability:** The final baseline outcome must be reproducible from the documented
  evidence and repository verification.
- **NFR-4 — Maintainability:** The scope and rationale for accepted findings must remain clear to
  future contributors.
- **NFR-5 — Process compliance:** Repository quality checks must be invoked through Make targets.

### User Scenarios

1. A contributor runs the type-checking gate and receives a pass when only documented, accepted
   findings are present.
2. A contributor introduces a new finding in either named area and the gate reports it as
   unexplained rather than accepting it automatically.
3. A maintainer reviews the baseline outcome and can tell which findings were resolved, retained,
   or moved to a separately tracked follow-up.

## Q&A

**Q: Why is this a separate debt task?**

A: The drift was observed during PYPOST-1173 validation and is broader than that feature change.
This issue isolates baseline/type-contract maintenance from the MCP header-forwarding work.

**Q: Does this task change Settings or stream-export product behavior?**

A: No. Existing behavior is a constraint and acceptance condition.

**Q: Does this task absorb every current type-checking error?**

A: No. Only the two named areas are in scope; unrelated findings remain separately identified.

**Q: What is the implementation language?**

A: Python, matching the affected application modules and repository tooling.

## References

- [PYPOST-1179](https://pypost.atlassian.net/browse/PYPOST-1179)
- [PYPOST-1173](https://pypost.atlassian.net/browse/PYPOST-1173) — source of the observed baseline-drift follow-up
