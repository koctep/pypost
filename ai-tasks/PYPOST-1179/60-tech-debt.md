# PYPOST-1179: Technical Debt Analysis

## Shortcuts Taken

No task-scoped shortcuts were taken. The implementation uses a narrow optional annotation,
the PySide6 enum spelling supported by the repository's type stubs, and removes only the four
diagnostics proven resolved by the complete baseline check.

## Code Quality Issues

- **Low — static-baseline coupling.** The accepted diagnostic set remains dependent on the
  installed mypy and PySide6 stub versions. A future dependency refresh may legitimately change
  diagnostic messages or codes and require another evidence-based baseline reconciliation.
  This is an inherent maintenance cost of the repository's baseline strategy, not a defect in
  the task-scoped implementation. **Jira follow-up: not required.**

No production refactoring, broad type ignores, or hardcoded runtime workarounds were introduced.

The Jira scope also mentions `StreamExportSnapshot` / `stream-export`. That area was inspected
against the task evidence and verified N/A for PYPOST-1179: no StreamExportSnapshot diagnostics
were introduced or resolved by this task, so no stream-export debt or follow-up ticket is
required.

## Missing Tests

No task-scoped test gap was identified. The deterministic reconciliation test covers stale,
new, and unrelated diagnostic keys, including the post-refresh clean scoped diff. Existing
SettingsDialog tests remain the behavioral coverage for the unchanged dialog lifecycle and
layout behavior.

The new test has a module-level `pytest.mark.timeout(30)` and uses no unbounded waits.

## Performance Concerns

None identified. The change affects static analysis metadata and type annotations only; the
runtime dialog path and baseline comparison algorithm are unchanged in complexity.

## Follow-up Tasks

- **NON-BLOCKER — pre-existing:** `make typecheck` still accepts 185 known diagnostics outside
  the four resolved `SettingsDialog` records. Those findings are outside PYPOST-1179's agreed
  scope and remain visible to the baseline checker. They are not ticketed here because this
  analysis found no new, actionable task-scoped debt requiring a Jira follow-up.

## Verification

- `make lint` — passed.
- `make typecheck` — passed with 185 known diagnostics.
- `make test PYTEST_ARGS='tests/test_pypost_1179_mypy_baseline_repro.py -q' WORKERS=1` — passed,
  2 tests.
- `make verify-ai-tasks` — passed.
