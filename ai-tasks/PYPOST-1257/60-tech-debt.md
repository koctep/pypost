# PYPOST-1257 Technical Debt

## Shortcuts Taken

None. The existing reflection behavior was extracted intact, and the helper
accepts an explicit protocol so it can be reused by future structural contract
tests.

## Remaining debt

- The helper retains its historical metrics-oriented function name for
  compatibility with the originating test and Jira description.
- Negative tests for each diagnostic branch remain unnecessary for this
  extraction ticket; the existing metrics parity tests exercise the successful
  contract path.

No new Jira debt issue is required.

## Verdict

Acceptable for merge: the shared helper removes the duplication boundary while
preserving the established conformance checks and adding independent coverage.
