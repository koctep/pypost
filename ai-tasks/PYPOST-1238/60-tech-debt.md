# PYPOST-1238: Technical Debt Analysis

## Shortcuts Taken

No temporary implementation or development-speed shortcut was introduced. The correction
follows the accepted architecture: every bare name immediately returns exact membership,
and other expressions retain the existing AST-dump fallback. No production code changes.

The non-name fallback is a lexical source-shape check, not semantic lookup resolution.
Its breadth is an existing limitation explicitly retained by the ticket and AC-4. It is
documented here as a compatibility boundary, not a newly introduced actionable defect.

## Code Quality Issues

No blocking code-quality issue was found. The two exact names are contract values rather
than unexplained configuration. Both consumers reuse the same classifier. The change
introduces no new dependency, control-flow abstraction, or unrelated refactor.

Bare names containing the full function name cannot fall through to the compatibility
fallback. The tests cover this boundary for both consuming predicates.

The guard still recognizes syntax rather than proving variable bindings or assertion
semantics. Broader semantic analysis is outside the accepted architecture and this issue.

## Missing Tests

No missing test was identified within the agreed scope. The focused regressions cover:

- Both exact supported bare names and the supported lookup expression.
- Lowercase and uppercase child substrings and a full-function-name substring.
- Unrelated tree finder names and lookup expressions.
- The reported tree-finder-only loop under both consuming predicates.

All new cases inherit the explicit ten-second module timeout. The existing real-suite
ownership checks provide compatibility coverage. Step 3 demonstrated eight intended red
cases; Step 4 passed both targeted modules after the fix.

Broader mutation-matrix coverage is tracked separately as PYPOST-1236 and excluded here.
Arbitrary alias resolution and stricter non-name expression validation are not promised by
the accepted requirements; their absence does not create a follow-up requirement here.

## Performance Concerns

None introduced. Bare-name recognition uses a fixed two-value membership test. Non-name
AST dumping retains its prior cost on small test-source expressions. This code does not
run in application request paths. No optimization or benchmark is justified by this change.

## Follow-up Tasks

None identified for PYPOST-1238. There are no newly actionable blockers or non-blockers
requiring Jira creation. No failures occurred in this task's green targeted validation;
this report does not claim a fresh full-suite pass or attribute unrelated failures to it.

Developer documentation of this narrow recognition contract belongs to Step 8. End-user
documentation is not applicable because application behavior is unchanged.
