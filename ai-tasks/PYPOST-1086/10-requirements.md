# PYPOST-1086: Restore a trustworthy mypy baseline gate

## Goals

Contributors need the optional static-analysis gate to distinguish existing accepted typing debt
from newly introduced or already resolved findings. The current mismatch makes `make typecheck`
exit unsuccessfully on the base revision, even though its findings reflect accumulated source and
baseline drift rather than a contributor's new change.

The goal is to restore a successful, trustworthy gate whose committed baseline matches the
remaining checked findings exactly, while preserving PyPost's existing Qt behavior.

## Programming Language

The implementation language is Python.

## User Stories

- As a contributor, I want `make typecheck` to succeed on an unchanged accepted revision so that I
  can use its exit status to detect typing regressions in my work.
- As a maintainer, I want resolved findings removed from the committed baseline so that the
  baseline represents current accepted debt rather than historical errors.
- As a PyPost user, I want request execution, application signal wiring, collection imports, and
  tab persistence to continue behaving as before while typing inconsistencies are cleared.

## Functional Requirements

1. `make typecheck` must exit successfully when run from the repository root on the completed
   revision.
2. The gate must report neither unbaselined current findings nor baseline findings that no longer
   occur.
3. The current typing findings associated with Qt worker signals and signal-to-callback
   connections must be cleared rather than accepted as additional baseline debt.
4. The committed baseline must retain all still-current accepted findings and exclude every
   finding that has already been resolved.
5. The checked application paths and the gate's comparison behavior must remain unchanged.
6. Runtime signal payloads, callback effects, request-worker behavior, collection-import behavior,
   and tab-persistence behavior must remain unchanged from the base revision.

## Scope

The in-scope behavior is the typecheck result and the existing Qt interactions currently reported
in these areas:

- the request worker;
- main-window signal wiring;
- collection-import signal wiring;
- tab-presenter signal wiring;
- the committed mypy baseline entries proven stale by the current gate output.

The typecheck gate, checked Python application code, Qt signals and callbacks, and committed
baseline are the main entities. Contributors invoke the gate; the gate compares current findings
with the baseline; the signals and callbacks preserve the application's existing runtime flows.

## Non-Goals

- Eliminating all accepted mypy findings from the repository.
- Expanding or reducing the directories checked by `make typecheck`.
- Making mypy part of `make check` or continuous integration.
- Changing public application behavior, Qt event flow, or user-visible features.
- Refactoring unrelated typing findings or application components.

## Constraints and Assumptions

- The implementation must remain compatible with the repository's supported Python and PySide6
  environment.
- Existing accepted baseline debt must not be hidden, broadly suppressed, or silently discarded.
- The baseline remains the source of accepted mypy debt for the existing checked scope.
- Current evidence is authoritative when it differs from the older Jira description.
- The task is a three-point Debt item and should remain narrowly focused on restoring the gate.

## Current Reproduction Evidence

At base commit `49441bb4017d17d7feb7e0182034ff21f16d90ee`, running `make typecheck`
exits with status 2 from Make after the baseline gate exits unsuccessfully. The gate reports:

- eight distinct new `(path, code, message)` comparison records across the four areas named in the
  Jira description;
- nine new source-line diagnostic instances, because one `main_window_signals.py` record occurs on
  two lines;
- seven `call-overload` instances in signal connections, plus one `assignment` instance and one
  `arg-type` instance in the request worker;
- two resolved baseline records: one in `encryption_migration_section.py` cited by Jira and an
  additional current drift record in `secret_store.py`;
- 219 baseline errors and 226 current errors.

The older Jira wording mentions eight Qt overload errors and one stale baseline entry. The current
gate output therefore expands the stale-entry scope to both proven resolved records and uses the
gate's exact clean-result contract instead of relying on the older counts.

## Definition of Done

- `make typecheck` exits 0 on the completed revision.
- Its output contains no "New mypy errors" or "Resolved baseline errors" section.
- The current Qt-related findings listed in the reproduction evidence are absent from the mypy
  result and are not added to the accepted baseline.
- Both currently resolved records are absent from the committed baseline.
- Existing tests covering the affected request, signal-wiring, import, and tab flows remain green.
- No unrelated production behavior, checked scope, or baseline debt changes.

## Q&A

### Why is this task needed if mypy is optional?

An optional quality gate is only useful when its exit status reliably identifies drift introduced
by the change being evaluated. A gate that already fails on the accepted revision cannot provide
that signal to contributors.

### Which evidence controls when Jira's older counts differ from the repository?

The reproducible output from `make typecheck` at the recorded base commit controls. Acceptance is
based on an exact match between current findings and the committed baseline, not a fixed historical
count.
