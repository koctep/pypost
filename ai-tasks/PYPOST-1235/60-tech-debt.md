# PYPOST-1235: Technical Debt Analysis

## Shortcuts Taken

No implementation shortcuts were found within the accepted scope. The reader normalises
`ast.Assign` and `ast.AnnAssign` targets and values, returns string names for list/tuple
literals, and returns `None` when no readable literal exists. Its caller distinguishes that
outcome from an empty literal before checking required names.

The static-only design intentionally does not evaluate computed manifests, follow mutations,
or resolve conditional exports. Multiple declarations retain the existing first-readable-literal
behaviour. These are accepted scope limits in `10-requirements.md` and `20-architecture.md`,
not new shortcuts introduced by this task.

## Code Quality Issues

No new blocking code-quality issue or deviation from the accepted architecture was found.
The required helper names, literal required-export collection, ownership test signature, and
discoverability regions are preserved. No production file is changed.

The regression file reuses private source-substitution helpers from the existing repro file.
That coupling is an explicit accepted architecture choice; the repro file is protected by AC-8.
It does not require a new follow-up issue for this change.

The existing automated quality gates have limited coverage of test code:

- `make lint` applies flake8 to `pypost/`, excluding `tests/`. Step 5 records direct inspection
  of the two task test files instead. The existing follow-up is linked below.
- `make typecheck` covers `pypost/core`, `pypost/models`, and `pypost/ui`, excluding these
  test files. Its passing baseline is not evidence that the changed tests were type-checked.
  Step 5 records source inspection of the optional result narrowing before set operations.

## Missing Tests

No missing test required by AC-1 through AC-8 was found. The regression file contains 16 cases:
9 reader cases and 7 ownership-test cases. These cover plain and annotated list/tuple literals,
absent, bare-annotation and computed manifests, an empty literal, a bare annotation followed
by a literal, annotated success, and both failure diagnostics.

Both changed test modules declare `pytestmark = pytest.mark.timeout(10)`. No missing explicit
timeout marker was found, and the tests introduce no unbounded waits. The unchanged ownership
family passed in Step 4 and Step 5; the 16 regression cases passed again in Step 6.

Tests of computed-value evaluation, conditional exports, mutations, and competing declarations
are outside this task's accepted scope and are not proposed as additional work here.

## Performance Concerns

No new performance concern was found by inspection. The helper retains one traversal of
module-level AST children and filters literal elements once. It neither imports the inspected
module nor adds runtime I/O, dependencies, or application instrumentation. Existing timeout
markers remain in place. No performance benchmark was run or claimed.

## Follow-up Tasks

- **NON-BLOCKER — pre-existing:**
  [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299) tracks the exit-policy
  failure observed before and after this task. Step 4 records `make check` with 364 passed
  files, 6 skipped files, and 1 failed file: `tests/test_pytest_exit_policy.py`, reaching its
  120-second file timeout. The retained evidence identifies the failed file, not an individual
  test node ID; no narrower node or cause is asserted here. Consequently, the full quality
  gate remains red for this known issue, while task-specific ownership checks pass.
- **NON-BLOCKER — pre-existing:**
  [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) tracks the exclusion of
  `tests/` from the flake8 scope of `make lint`. Step 5 compensates with documented inspection
  of the changed test files; the passing lint gate must not be described as automated lint
  coverage for them.

No new Jira follow-up is required by this scope review. Existing typecheck scope is disclosed
above without widening the task or inventing a separate debt item. Developer-facing contract
and troubleshooting updates in `doc/dev/ui_actions.md` remain the planned Step 8 deliverable.

## Evidence and Review Status

This analysis reviewed the implementation, regression tests, requirements, architecture, roadmap,
`40-code-cleanup.md`, and `50-observability.md`. It reuses the recorded Step 4–6 results;
no passed test gate was repeated during Step 7. Only Markdown artifacts were changed.
Step 7 remains in progress until the autonomous orchestrator accepts its independent review.
