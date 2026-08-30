# PYPOST-1152: Orchestrator pre-investigation notes (read before Step 1)

These are raw findings gathered by the orchestrator before launching Step 1-7
subagents. Use them as evidence; do not treat them as a substitute for the
step artifacts themselves — cite/expand them in `10-requirements.md`,
`20-architecture.md`, etc. as appropriate.

## Original Jira report

- Summary: "Investigate test_ui_wait.py PySide6 segfault in isolated subprocess"
- Filed from `ai-tasks/PYPOST-1149/60-tech-debt.md` (row: "NON-BLOCKER —
  pre-existing", test node id `tests/test_ui_wait.py` (entire module — native
  segfault during collection/execution), suspected cause "PySide6/Shiboken
  segfault in isolated subprocess (`QT_QPA_PLATFORM=offscreen`)").
- Filed repro: `make test PYTEST_ARGS=tests/test_ui_wait.py` or
  `pytest tests/test_ui_wait.py`.
- No captured crash log/traceback exists anywhere in the repo or ai-tasks/
  history for this specific filing — the PYPOST-1149 tech-debt row is the only
  record, and it does not include a Fatal Python error backtrace (unlike the
  fresh segfault the orchestrator did capture below for a DIFFERENT, already
  ticketed module).

## Repro attempts performed by the orchestrator (2026-08-30, this session)

Environment: Linux, Python 3.13.5, PySide6/shiboken6 (pinned versions per
repo), `QT_QPA_PLATFORM=offscreen`, working tree at `dev` HEAD `8389a490`.

1. `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ui_wait.py -v --tb=short`
   x1: **12 passed, exit 0**, 6.37s.
2. Same direct-pytest invocation x10 in a loop (`for i in 1..10`): **10/10 runs
   exit 0**, no segfault, no core dump, no `Fatal Python error` in any log.
3. `make test PYTEST_ARGS=tests/test_ui_wait.py` (goes through
   `scripts/run_parallel_tests.py`'s per-file subprocess-isolation model, the
   exact repro command named in the Jira description) x6: **6/6 runs exit 0**,
   ~7.1-7.4s each, `Total Files: 1 | Passed: 1 | Failed: 0`.
4. Full `make test` (no PYTEST_ARGS — runs the entire 311-file suite with 8
   parallel workers, `QT_QPA_PLATFORM=offscreen`) x1: **311 files, 306 passed,
   4 failed, 1 skipped, wall-clock 174.41s**. `tests/test_ui_wait.py` is
   **among the 306 passed** (`[291/311] tests/test_ui_wait.py ... PASSED
   (9.65s)`) — not one of the 4 failures. Full log saved at
   `/tmp/claude-501/-home-src/a849658f-6a35-453e-a7b9-195eef1ee5a4/scratchpad/full_test_run1.log`
   (scratchpad; not part of the repo).

**Total: 17/17 executions of `tests/test_ui_wait.py` completed cleanly** across
three distinct invocation shapes (direct pytest, orchestrator single-file
subprocess, and embedded in the full 311-file/8-worker batch) — no segfault,
no core dump, no `Fatal Python error` observed in this session.

## The 4 unrelated failures observed in the one full-suite run (all already ticketed — do NOT re-file)

| File | Symptom | Already tracked |
| --- | --- | --- |
| `tests/test_main_window_alert_reload.py::test_open_settings_reloads_alert_manager_when_webhook_changes` | Native `SIGSEGV` (exit -11) inside `pypost/ui/styles/style_manager.py:102 apply_theme` — matches the known PYPOST-1117 `apply_theme` crash class | **PYPOST-1251** (confirmed via `jira_get_issue`/JQL: "Pre-existing failure: tests/test_main_window_alert_reload.py crashes with SIGSEGV under full-suite run") |
| `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | LOC/inventory baseline drift assertion | **PYPOST-1252** and/or **PYPOST-1111** |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::{test_audit_module_inventory_within_caps,test_markdown_snapshot_matches_current_metrics}` | SOLID baseline snapshot/cap drift (`template_service.py` now 241 LOC vs cap 225) | **PYPOST-1111** ("Regenerate audit/baseline metrics snapshots drifted by recent MCP refactors (2 pre-existing failures)") |
| `tests/test_makefile.py` | `WORKER_TIMEOUT=120` exceeded under full-suite parallel load (`TIMED_OUT`, exit -9) | **PYPOST-1234** ("Pre-existing failure: tests/test_makefile.py exceeds WORKER_TIMEOUT=120 under full-suite parallel load") |

Confirmed via `jira_search_issues_jql` against `key in (PYPOST-1234, PYPOST-1111,
PYPOST-1251, PYPOST-1252, PYPOST-1253)` — all five already exist in the backlog
(status "To Do"). **Do not file new issues for any of these** — they are
pre-existing, unrelated to `tests/test_ui_wait.py`, and out of this task's scope
per the failing-tests-triage dedupe instruction. `PYPOST-1253` (flake8 findings)
was not observed in this run but is also pre-tracked.

## Repo precedent worth reusing (PYPOST-1040 / PYPOST-1115 stress-detector pattern)

`tests/test_agent_dialog_settle_teardown_stress.py` (see its docstring) is the
established pattern in this repo for **probabilistic native Qt/Shiboken
crashes that cannot be captured by a single deterministic run**: it spawns N
independent isolated child `pytest` subprocesses of the target module and
asserts every child exits 0 — a "stress detector," not a single-shot repro.
That case had a *confirmed* ~32.5% single-run crash rate (13/40), so the stress
test was red at creation and later marked `xfail(strict=False)` once root
cause was confirmed as an upstream-only PySide6/shiboken6 defect (Step 4
decision, not hidden in Step 3).

**Key difference for PYPOST-1152**: unlike PYPOST-1040, this session's 17/17
clean-run rate is 0% observed crash frequency — there is no confirmed red
state to reproduce, at any sample size tried so far. A stress test built the
same way here would be **green**, not red — it is a regression-detection
guard for the future, not a repro of a currently-observed defect. Step 3 for
this task should very likely be documented `N/A` (defect not currently
reproducible after 17 clean executions across 3 invocation shapes; see
evidence above) rather than force a red test that cannot honestly demonstrate
a currently-existing defect. Step 4/Step 7 should decide whether adding a
green stress-detector test (regression guard, following the established
pattern) is proportionate value for the 5-point budget, and/or whether a
scoped follow-up ticket (e.g. "re-open PYPOST-1152-class investigation if
`tests/test_ui_wait.py` segfaults again in CI, with instructions to capture
`faulthandler`/core dump next time") is the right closing move. Either is
consistent with the task's explicit "mitigated + follow-up" allowance — do
not force a fabricated root cause or a fix for a bug that isn't currently
observed.

## Documentation cross-references already in the repo

- `doc/dev/gui_testing.md` troubleshooting table — has rows for
  `apply_theme` (PYPOST-1117) and other segfault classes; a
  PYPOST-1152/test_ui_wait.py row does not exist yet — Step 8 dev-docs should
  probably add one reflecting the "not currently reproducible, guarded by
  stress detector X" conclusion.
- `doc/dev/testing.md` "Failure Class Taxonomy" (Class 1-4) — test_ui_wait.py's
  historical segfault does not fit cleanly into any of the 4 existing classes
  (it isn't `apply_theme` state leak, isn't `SettingsDialog` GC double-free,
  isn't port collision, isn't event-loop starvation) — worth noting as an
  unclassified/unreproduced entry rather than force-fitting it into an
  existing class.
