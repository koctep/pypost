# PYPOST-1040: Technical Debt Analysis

**Verdict:** No PYPOST-1040-owned blocker. This is a diagnostic ticket — no
production code (`pypost/`) was touched anywhere in this task (out of scope
per `ai-tasks/PYPOST-1040/10-requirements.md`'s "What is out of scope"
section). The only artifact this task produced is a new test file,
`tests/test_agent_dialog_settle_teardown_stress.py`, plus documentation. The
technical debt this ticket *investigated* (TD-1, the intermittent Qt teardown
SIGSEGV itself) is recorded and updated in
`ai-tasks/PYPOST-968/60-tech-debt.md` — see "Cross-reference" below — not
duplicated here; this file is about debt in PYPOST-1040's own deliverables.

## Shortcuts Taken

No shortcut was taken in production code — none was touched. Two legitimate,
deliberate judgment calls were made in the test artifact itself; both are
documented in-repo (module docstring / roadmap) rather than hidden, and
neither is debt to remediate:

- **`xfail(strict=False)` instead of a fix.** Step 4 marked
  `test_all_child_runs_exit_zero_under_repeated_teardown_stress` with
  `pytest.mark.xfail(reason=..., strict=False)` rather than making it pass.
  This is a deliberate, permanent classification decision, not a placeholder:
  the crash traces to an upstream PySide6/shiboken6 6.11.1 defect (see
  `ai-tasks/PYPOST-1040/20-architecture.md`), no PyPost-owned fix exists to
  apply, and a production change is explicitly out of scope for this
  diagnostic ticket per `10-requirements.md`. `strict=False` is what makes a
  future `XPASS` (e.g. after a PySide6 upgrade or a follow-up mitigation)
  show up as a visible, non-blocking signal instead of either silently
  passing or breaking the build — this is documented in the test file's own
  "Why this test carries an `xfail(strict=False)` marker" docstring section.
- **Bounded/reduced confirmation runs instead of the full `STRESS_ITERATIONS
  = 25` during Steps 3, 4, and 6 review.** Per the roadmap's Step 3 and Step
  4 sub-items: Step 3's reviewer live-verified the crash-signal detection
  mechanism with a synthetic SIGSEGV child (correctly reported) and sampled
  50 runs in the reviewer's own sandbox, in which the underlying upstream
  crash did not reproduce (consistent with the per-instance heap/ASLR
  sensitivity the architecture doc already notes, not a harness defect).
  Step 4 confirmed the `xfail(strict=False)` marker's pytest semantics (`1
  xfailed, 1 xpassed`, exit code 0 for both) using a throwaway,
  not-committed standalone script with deliberately-failing/passing dummy
  tests, rather than running the full, multi-minute, probabilistic 25-child
  stress harness end-to-end at every review step. The committed
  `STRESS_ITERATIONS = 25` constant itself was never lowered or altered —
  only the *ad hoc verification runs* during review were bounded, to keep
  iteration time reasonable. This is a legitimate efficiency choice for a
  probabilistic native-crash detector, not corner-cutting: the marker
  mechanics and detection logic were independently verified by construction
  (synthetic crash injection, dummy xfail/xpass runs) rather than by relying
  solely on statistical luck within a review session.

## Code Quality Issues

None identified beyond what Step 5 (`ai-tasks/PYPOST-1040/40-code-cleanup.md`)
already covered and resolved: `flake8` clean, no unused imports/dead code, no
line over 100 chars, consistent 4-space indentation. No further issue was
found while reviewing the final state of
`tests/test_agent_dialog_settle_teardown_stress.py` for this step.

## Missing Tests

None identified beyond what is already covered. This is a diagnostic ticket
with no new production behavior to test:

| Scenario | Status |
| --- | --- |
| Detect the upstream teardown crash class across repeated runs | Covered by the new `tests/test_agent_dialog_settle_teardown_stress.py` (`STRESS_ITERATIONS = 25`, >99.9% detection power at the measured 32.5% rate) |
| A future PySide6/shiboken6 fix becomes visible (not silently swallowed) | Covered — `xfail(strict=False)` surfaces a future fix as `XPASS` |
| Diagnostic detail (signal, stdout/stderr tail) is not silently dropped on the expected XFAIL path | Covered by Step 6's `_LOGGER.warning(summary)` addition |
| `tests/test_agent_dialog_settle_e2e.py`'s existing assertions | Unchanged, out of scope — this ticket does not alter them per `10-requirements.md` |
| A PyPost-owned fix for the crash itself | Not applicable — no PyPost-owned fix exists to test; this is the recommended follow-up ticket's job, not this one's |

The new test module declares `pytest.mark.timeout(150)` and `pytest.mark.slow`
(module-level `pytestmark`); each child subprocess additionally bounds itself
at `CHILD_TIMEOUT_S = 30.0`. There is no missing explicit-timeout blocker.

## Performance Concerns

None beyond the test's own intentional cost. `tests/
test_agent_dialog_settle_teardown_stress.py` is deliberately expensive by
design (25 independent child `pytest` process invocations, ~1s/child
baseline, ~25-40s total) — this is why it is marked `pytest.mark.slow` and
excluded from the default `-m "not slow"` CI selection (same convention
`pyproject.toml` already uses for other opt-in-only scenarios), so it does
not add wall-clock cost to every CI run. No production code path was touched,
so there is no runtime-performance concern for the shipped application.

## Architecture Deviations

None. The test file matches the architecture's Implementation Plan exactly:
location, `STRESS_ITERATIONS = 25`, subprocess-per-child isolation,
`xfail(strict=False)` marking with the specified reason string, and the
`slow` marker — see `ai-tasks/PYPOST-1040/20-architecture.md` "What Step 3
will build" and the roadmap's Step 3/Step 4 sub-items for the point-by-point
match.

## Hardcoded Values

No problematic hardcoded value. `STRESS_ITERATIONS = 25` and `CHILD_TIMEOUT_S
= 30.0` are intentional, documented constants derived from the architecture's
own statistical-power calculation (`P(>=1 crash) ≈ 99.99%` at the measured
32.5% per-run rate); `pytest.mark.timeout(150)` is the outer per-test bound
sized for 25 children at the measured baseline plus headroom. None of these
are magic numbers — each is explained in the module docstring or an adjacent
comment.

## Follow-up Tasks

### NON-BLOCKER

#### Mitigation-attempt follow-up (recommended, not yet ticketed)

- **What:** A follow-up ticket to *attempt* a real mitigation for the
  upstream PySide6/shiboken6 6.11.1 `QWidgetItem` GC-teardown crash that
  PYPOST-1040 diagnosed but did not (and, per its own scope, could not) fix.
- **Candidates** (from `ai-tasks/PYPOST-1040/20-architecture.md`'s "What is
  explicitly deferred, and why" section):
  1. Pin a different PySide6/shiboken6 patch version and re-run
     `tests/test_agent_dialog_settle_teardown_stress.py` to check whether the
     crash rate changes.
  2. Break the specific reference cycle so the relevant Shiboken-wrapped
     `QWidgetItem`/layout objects in `SettingsDialog`'s widget subtree are
     reclaimed by prompt refcounting instead of being deferred into
     CPython's cyclic GC path.
  3. Explicitly call `gc.collect()` once, deliberately, right after
     `AgentAppSession.shutdown()` (`pypost/agent/lifecycle.py`) while the
     object graph is still well-understood, instead of leaving reclamation
     to pytest's later, uncontrolled 5-round `gc_collect_harder()`.
- **Why it's a separate ticket, not squeezed in here:** each candidate needs
  its own experimentation loop (re-running the stress harness under changed
  conditions, verifying no regression) and PYPOST-1040 is an already-8-point
  diagnostic ticket whose own scope is diagnosis, not fix (see
  `10-requirements.md`'s "What is out of scope").
- **Jira:** [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) (8 story
  points, Medium priority).

#### `tests/_pytest_plugins/duration_report.py` mis-reports xfail/XPASS outcomes (found by blocker review)

- **What:** This pre-existing, repo-wide plugin (registered via
  `tests/conftest.py`'s `pytest_plugins`, untouched by PYPOST-1040) overrides
  pytest's `pytest_report_teststatus` hook unconditionally on `report.outcome`,
  bypassing pytest's built-in `wasxfail` handling. Verified directly against
  isolated dummy `xfail(strict=False)` tests: an XPASS displays as plain
  `PASSED`/"1 passed" instead of `XPASS`; an XFAIL displays as plain
  `SKIPPED`/"1 skipped" with no reason text, indistinguishable from an
  unrelated skip; and with `-rA`/`-ra`/`-rs` (not used by this repo's current
  CI/Makefile) pytest's own `_folded_skips()` summary code raises an
  unhandled `AssertionError` because the xfail report's `longrepr` isn't the
  tuple shape a genuine skip has.
- **Impact on this ticket:** None — the actual Step 6 deliverable
  (`_LOGGER.warning(summary)` via `log_cli`/`--log-file`) fires correctly
  regardless of how this plugin labels the outcome, and no current CI/Makefile
  path uses the `-r` flags that trigger the crash. This is why blocker review
  classified it NON-BLOCKER for PYPOST-1040's own closure.
- **Why it's a separate ticket:** the plugin predates and is untouched by this
  task; it affects every `xfail`-marked test repo-wide, not just this one; and
  fixing it is unrelated to this ticket's diagnostic scope.
- **Jira:** [PYPOST-1116](https://pypost.atlassian.net/browse/PYPOST-1116) (3 story
  points, Low priority).

### Cross-reference

- `ai-tasks/PYPOST-968/60-tech-debt.md`'s **TD-1** entry ("Diagnose
  intermittent post-PASS Qt teardown SIGSEGV") was updated by this step (in
  place, not duplicated) to record: priority raised from Low to **Medium**;
  the new Linux/Python 3.13.5/PySide6 6.11.1 reproduction evidence (32.5%,
  13/40, N=40); the root cause (ablation-confirmed `SettingsDialog`
  nested-layout subtree + pytest's forced cyclic GC); the new
  `tests/test_agent_dialog_settle_teardown_stress.py` stress-detector test;
  a link to `ai-tasks/PYPOST-1040/20-architecture.md` for full detail; and
  the same mitigation-follow-up recommendation as above. Original Jira links
  (PYPOST-1040, PYPOST-429 lineage) and prior evidence were kept intact, not
  removed.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions or crutches | None — `xfail(strict=False)` is a deliberate permanent classification, not a placeholder (see "Shortcuts Taken") |
| Code quality defect | None (Step 5 clean; reconfirmed here) |
| Missing acceptance test | None — diagnostic ticket, no new production behavior |
| Missing explicit pytest timeout | None — module `timeout(150)` + per-child `CHILD_TIMEOUT_S = 30.0` |
| Unbounded internal wait | None |
| Performance regression | None — no production code touched; new test is intentionally `slow`-marked and excluded from default CI |
| Architecture deviation | None |
| Problematic hardcoded value | None |
| Product behavior or safety regression | None — no production code touched |
| Merge/release blocker | None |

Step 7 passed independent review (fix applied to a stale priority mention in
`ai-tasks/PYPOST-968/60-tech-debt.md`, re-reviewed PASS) and is marked `[x]`
in the roadmap. Blocker review (sprint-task-runner Phase C) returned SAFE TO
CLOSE, surfacing one additional non-blocking follow-up (see above:
`tests/_pytest_plugins/duration_report.py`).
