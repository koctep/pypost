# PYPOST-1066: Technical Debt Analysis

## Scope and Verdict

The reviewed implementation is limited to two regression tests in
`tests/test_mypy_baseline.py`. It changes no production code, public interface, dependency,
baseline data, or runtime behavior.

**SAFE TO CLOSE** — no new in-scope technical debt or release blocker was identified. The known
repository-wide failures and type-check baseline drift are pre-existing, tracked separately, and
do not justify duplicate follow-up issues from PYPOST-1066.

## Shortcuts Taken

- The gate-flow test substitutes the module-owned `_run_mypy` and `BASELINE_PATH` seams instead of
  launching mypy or changing the committed baseline. This is the approved hermetic design, not a
  temporary workaround: the requirement begins with a clean current result and concerns the gate's
  branch selection, diagnostics, and exit status.
- No production refactor was performed because both required boundary behaviors were already
  correct. Adding abstractions solely for these tests would expand scope without improving the
  contract under test.

No temporary implementation, feature flag, compatibility shim, skipped test, `xfail`, or disabled
validation was introduced.

## Code Quality Issues

No new code-quality issue was found. The additions use the existing test classes and fixtures,
descriptive test names, local setup, and direct assertions over the stable observable contract.
They introduce no duplicated production logic, unused helper, broad mock, debug output, or
unnecessary dependency.

The synthetic baseline construction is intentionally local to the single orchestration test. A
shared fixture would add indirection for one use and is not currently warranted.

## Missing Tests

No in-scope coverage gap remains:

- `_diff_errors([], [])` is directly verified to return no new or fixed differences.
- A clean current run against a non-empty baseline is verified end to end through `main()` for the
  actionable exit status, resolved-debt details, aggregate counts, and absence of false new-error
  or ordinary-success output.
- Existing behavior outside these two boundaries was explicitly out of scope and was not changed.

Both added tests inherit the module-level `pytestmark = pytest.mark.timeout(30)`. They contain no
polling, event loop, subprocess, network operation, or other internal wait requiring an additional
bound. Timeout coverage is therefore complete and no timeout blocker exists.

## Performance Concerns

None introduced. The pure comparison uses empty collections, and the gate-flow test uses one local
temporary JSON entry with a patched mypy result. It performs no real type-check invocation, network
request, or unbounded work. The focused pair completed in 0.03 seconds during Step 5 validation.

## Deviations from Initial Architecture

None. The implementation follows `20-architecture.md` exactly:

- one focused test exercises the deterministic `_diff_errors()` core;
- one hermetic test exercises the `main()` orchestration boundary;
- external boundaries are substituted at symbols owned by `scripts.check_mypy_baseline`;
- production modules, interfaces, baseline schema, and output policy remain unchanged.

## Hardcoded Values

The temporary baseline's version, scope, error count, path, code, and message are deterministic
test fixture values. The version and scope use production constants, while the representative
error identity is asserted in the resulting diagnostic. These values are local test inputs rather
than production configuration and do not require extraction.

## Follow-up Tasks

### NON-BLOCKER — pre-existing failures

All three failures below reproduced unchanged at base commit
`04db6e383002a359e5866e6bed9698cec91ee821` and are outside the PYPOST-1066 diff:

#### [PYPOST-1111: PYPOST-1077 artifact audit](https://pypost.atlassian.net/browse/PYPOST-1111)

```text
tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates
```

#### [PYPOST-1111: SOLID audit snapshot](https://pypost.atlassian.net/browse/PYPOST-1111)

```text
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics
```

#### [PYPOST-1110: QApplication alignment](https://pypost.atlassian.net/browse/PYPOST-1110)

```text
tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication
```

These failures are documented baseline-relative non-blockers. They must not be fixed or reticketed
inside PYPOST-1066.

### Existing type-check baseline drift

`make typecheck` reports repository baseline drift in unchanged production files: 9 new mypy error
occurrences and 2 resolved entries, with 219 baseline errors versus 226 current errors. The active
sprint issue [PYPOST-1086](https://pypost.atlassian.net/browse/PYPOST-1086) owns that work. No
duplicate issue is needed.

### New in-scope debt

None. No new follow-up task should be created for PYPOST-1066.

## Documentation Impact

No developer or user documentation update is applicable in Step 7. The task verifies established
gate behavior without changing commands, interfaces, setup, policy, or runtime behavior. Step 8
retains ownership of its independent developer-documentation assessment.

## Validation

- The two focused regression tests passed through `make test`: 2 passed in 0.04 seconds.
- `make lint` passed, including the repository's documentation and relative-link checks.
- Direct Markdown lint and relative-link checks passed for `00-roadmap.md` and this artifact.
- `git diff --check` passed; the edited Markdown has UTF-8 text, LF endings, no trailing
  whitespace, and a final newline.
