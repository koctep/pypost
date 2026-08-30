# PYPOST-1152: Technical Debt Analysis

## Shortcuts Taken

1. **`STRESS_ITERATIONS = 15` and `CHILD_TIMEOUT_S = 30.0` are judgment calls, not empirically
   derived values.** The repo's own precedent for this exact test shape,
   `tests/test_agent_dialog_settle_teardown_stress.py` (PYPOST-1040), sized its
   `STRESS_ITERATIONS = 25` against a *measured* 32.5% (13/40) crash rate from that task's own
   Step 2 ablation — the sample size was chosen to hit a stated detection-power target (>99.9%)
   against a known, confirmed defect rate. `test_ui_wait_stress.py` has no such number to size
   against: this task's own evidence is 0 crashes across 47 reproduction attempts (17
   orchestrator + 20 sequential + 8 concurrent + 2 final sanity re-runs), so there is no measured
   current crash rate at all. `STRESS_ITERATIONS = 15` was instead chosen against a
   **hypothetical future** regression rate (~20%/run, picked as an order of magnitude below
   PYPOST-1040's confirmed rate, for `P(>=1 detected in 15) ≈ 96.5%`) — a defensible but
   admittedly invented threshold, not a measurement. `CHILD_TIMEOUT_S = 30.0` is reused verbatim
   from PYPOST-1040 on the reasoning that this session's slowest single observed run of
   `tests/test_ui_wait.py` was well under 10s, but it was not independently re-derived for this
   module's own timing distribution.

   **Statistical honesty limit**: a guard built on zero observed failures cannot bound detection
   power the same way PYPOST-1040's could. PYPOST-1040's stress test demonstrably *works* — it
   was validated against a defect that was known to exist and known to occur at ~32.5%, so its
   N=25 could be checked against ground truth. `test_ui_wait_stress.py`'s N=15 has never been
   validated against any real crash (because none is currently reproducible) — its ~96.5%
   detection-power figure is a projection against an assumed future rate, not a confirmed
   capability. It is honest to call this a **tripwire**, not a **calibrated detector**: it will
   very likely catch a regression at or above the assumed ~20%/run rate, but there is no evidence
   basis for claiming any particular detection power against a lower, rarer, or more
   environment-specific trigger — including, notably, whatever rate (if any) the original
   PYPOST-1149 filing was actually observing.

2. **No production-code change** — this is a deliberate non-shortcut worth naming explicitly so
   it isn't mistaken for scope creep avoided by accident: `pypost/agent/ui_wait.py` was reviewed
   in full and found to have no PyPost-owned defect pattern (see `20-architecture.md`), so Step 4
   made no change there. This is the correct Branch C outcome, not a shortcut, but it does mean
   this task closes without having "fixed" anything in the conventional sense — the deliverable is
   evidence plus a regression guard, not a code fix.

## Code Quality Issues

No code quality issues were found in `tests/test_ui_wait_stress.py` itself — `flake8` reported
zero violations (see `40-code-cleanup.md`), and the module's structure deliberately mirrors the
already-reviewed `test_agent_dialog_settle_teardown_stress.py` pattern for maintainability
(shared `_describe_returncode`-equivalent helper, same subprocess-isolation shape).

One minor, non-blocking observation: `_describe_returncode` and the failure-summary/timeout
branches inside `test_all_child_runs_exit_zero_under_repeated_isolated_stress` are logically
untested in isolation (see Missing Tests below) — the same characteristic PYPOST-1040's stress
test also has, so this is not a regression relative to the pattern being followed, just an
inherited property of the "N/A — no failing-repro is written" design of this whole test family.

## Missing Tests

None anticipated for this task's own scope — Steps 4, 5, and 6 each ran the new test to
completion (118.83s, then 112.44s, then 114.26s across the three steps) and found no gaps in
their own checklists (Step 5's cleanup pass: flake8-clean, no unused imports/prints, all lines
within the 100-char limit, explicit `pytest.mark.timeout` confirmed; Step 6's observability pass:
added a passing-path INFO log line, judged the pre-existing ERR path's diagnostics — signal-name
decode, stdout/stderr tails, `PYTHONFAULTHANDLER=1` — already sufficient).

One gap worth naming rather than silently carrying forward: **the guard's own failure-handling
code path is never exercised by any test.** `_describe_returncode`'s signal-name branch, the
`subprocess.TimeoutExpired` handling, and the `pytest.fail(summary)` message construction only
run if a child crashes or hangs — and by design this guard ships green, so none of that code has
ever actually executed in CI or in any of this session's runs. This is not unique to this task
(PYPOST-1040's equivalent helper has the same property), so it is recorded here as inherited,
proportionate debt rather than a new defect: writing a "test of the tester" (e.g. mocking
`subprocess.run` to return a synthetic SIGSEGV and asserting the failure message shape) would add
real maintenance-tested confidence in the forensic-capture path, but is judged out of proportion
for this task's 5-point budget given the pattern is copied from already-shipped, unchallenged
code. Flagged here for visibility, not filed as a follow-up (see rationale in Follow-up Tasks —
this task limits itself to one scoped follow-up per the sprint-task-runner Phase D convention).

## Performance Concerns

1. **`tests/test_ui_wait_stress.py` costs ~110-120s per run** (118.83s in Step 4, 112.44s in Step
   5, 114.26s in Step 6 — consistent across runs) because it spawns `STRESS_ITERATIONS = 15`
   fully independent, isolated child `pytest` subprocesses, each re-importing PySide6/Shiboken
   from a cold interpreter. It is marked `pytest.mark.slow`, so it is **excluded from the default
   `-m "not slow"` fast suite** (`pyproject.toml` addopts) and only runs when a developer or CI
   job explicitly opts into `-m slow` / `make test-slow` / a direct `pytest
   tests/test_ui_wait_stress.py -m slow` invocation.

2. **This tradeoff is more significant than "runs nightly instead of on every commit" — as
   configured today, nothing in CI invokes it at all.** Checked `.github/workflows/test.yml` and
   the `Makefile` directly: the only job that runs anything under `-m slow` is
   `make-install-smoke`, and that job scopes pytest explicitly to
   `pytest tests/test_makefile.py -m slow -v --tb=short` — a single named file, not a broad `-m
   slow` sweep. No workflow job invokes `make test-slow` (the Makefile target that would run the
   full `tests/ -m slow` set, including this new guard) or a bare `pytest -m slow` across `tests/`.
   There is no scheduled/nightly workflow in `.github/workflows/` at all — `test.yml`'s only
   triggers are `push`, `pull_request`, and manual `workflow_dispatch`. Practically: this guard
   currently only executes when a human runs `make test-slow` (or an equivalent explicit
   invocation) locally. It will not catch a regression on any push, PR, or scheduled CI run under
   the present CI configuration — a gap consistent with, and inherited from, the equivalent
   situation for PYPOST-1040's own stress test, which has the identical `slow`-marker placement
   and the identical lack of CI wiring. Wiring `-m slow` (or specifically this file) into a CI job
   is judged out of scope for this task (it would touch shared CI configuration well beyond
   `tests/test_ui_wait.py`'s dependency surface, which the requirements doc's "What is out of
   scope" section reserves) and is not proposed as this task's follow-up below, since it is a
   pre-existing property of the whole `slow`-marked test family, not something this task
   introduced.

## Follow-up Tasks

### Scoped follow-up for Jira creation (Phase D)

1. **If `tests/test_ui_wait_stress.py` ever goes red in CI (or in any local `make test-slow` /
   `-m slow` run), re-open a PYPOST-1152-class investigation using its captured
   stdout/stderr/`PYTHONFAULTHANDLER` output as the starting evidence** — something the original
   PYPOST-1149 filing lacked (no crash log, backtrace, or core dump was ever captured for that
   report). `Priority: Low`. This is a **dormant/conditional** follow-up, not an active
   investigation to start now: there is no live defect to chase (0/47 reproductions this
   session), and the guard exists precisely so that *if* a regression ever does occur, the next
   investigator inherits real forensic signal (signal-name-decoded exit codes, stdout/stderr
   tails, and a best-effort native traceback via `PYTHONFAULTHANDLER=1`) instead of starting from
   an unsupported ledger claim the way this task had to.
   `Jira: [PYPOST-1254](https://pypost.atlassian.net/browse/PYPOST-1254)` (Debt, Low priority,
   5 story points, created in Phase D of this task's run).

### Ledger correction (not performed in this step)

2. The `tests/test_ui_wait.py` row in `ai-tasks/PYPOST-1149/60-tech-debt.md` currently asserts an
   unverified "PySide6/Shiboken segfault in isolated subprocess" as fact. This task's evidence
   (47/47 clean reproduction attempts across 4 invocation shapes, plus a full code-review pass
   finding no PyPost-owned defect pattern — see `20-architecture.md`) does not support that
   claim as written. Per the requirements doc's own instruction ("the specific mechanism is a
   Step 8/commit-time decision, not fixed here"), the correction itself — updating that row
   in-place or superseding it with a clear cross-reference to this task's artifacts and the new
   `tests/test_ui_wait_stress.py` guard — is **not made in this step**. It is recorded here as
   the plan so Step 8 (dev-docs) or the commit step carries it out rather than it being lost.

### Pre-existing failures observed and deduped, not re-filed

For completeness: this task's reproduction runs (including the one full-suite embedding recorded
in Step 1's carried-over evidence) surfaced the same four unrelated, already-ticketed failures
the PYPOST-1149 orchestrator had previously observed — `tests/test_main_window_alert_reload.py`
(PYPOST-1251/PYPOST-1117 `apply_theme` crash class), `tests/test_pypost_1077_verification_artifacts.py`
and `tests/test_solid_audit_baseline.py` (PYPOST-1252/PYPOST-1111 baseline drift), and
`tests/test_makefile.py` (PYPOST-1234 worker timeout). All four are out of this task's scope per
`10-requirements.md`'s Definition of Done and are **not** re-investigated or re-filed here —
listed only so this ledger doesn't read as having missed them.

## Verdict

**Acceptable technical debt for merge.** This task's only debt is the inherent statistical
honesty limit of a zero-observed-rate regression guard (an invented, not measured, sizing
rationale — clearly documented as such in the test's own module docstring and above) and the
`slow`-marker/CI-wiring gap it inherits from the PYPOST-1040 pattern it is modeled on. No
production code changed, no new defect was introduced, and the one live piece of follow-up work
(re-opening an investigation if the guard ever fires) is correctly deferred as a dormant,
LOW-priority conditional item rather than manufactured urgency. The PYPOST-1149 ledger correction
is tracked to happen at Step 8/commit time, not lost.
