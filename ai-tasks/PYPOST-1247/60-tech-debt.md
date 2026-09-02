# PYPOST-1247: Technical Debt Analysis

## Shortcuts Taken

None. The implementation keeps registration scoped to each `FunctionRegistry` instance and
updates callable and strictness metadata together.

## Code Quality Issues

- The flexible `register` signature supports several decorator forms; future API stabilization
  may split direct registration and decorator construction into separate named helpers.

## Missing Tests

- No blocking gaps identified. A future test could verify concurrent registration if registries
  become shared across threads.

## Performance Concerns

`allowed_names()` creates a small immutable snapshot on each call. This is appropriate for the
current catalog size and avoids stale metadata after dynamic registration.

## Follow-up Tasks

No Jira follow-up is required for this scoped change. Thread-safe shared registries and broader
plugin discovery remain outside PYPOST-1247.
