# Roadmap: PYPOST-1040

## Task Metadata

- **Implementation language**: Python (repo is a single Python/PySide6 application; the
  affected test module, teardown code, and any resulting fix/regression test are all Python —
  see `pypost/agent/lifecycle.py`, `tests/test_agent_dialog_settle_e2e.py`).
- **Branch name**: `test/PYPOST-1040-diagnose-qt-teardown-crash` (reference only — commit
  landed directly on `dev` per this task's instructions; do not switch branches)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
  - [ ] `ai-tasks/PYPOST-1040/20-architecture.md` — crash reproduced on Linux/Python 3.13.5/
    PySide6 6.11.1 (13/40 = 32.5% crash rate, same order as macOS's ~1/3); DoD branch (a)
    applies. Ablation pinpoints trigger: pytest's `unraisableexception` forced GC
    (0/20 crashes with it disabled) acting on `SettingsDialog`'s nested-layout widget subtree
    specifically (0/20 crashes on a no-dialog `AgentAppSession` smoke test under identical
    forced-GC conditions). No PyPost-owned anti-pattern found (no raw `QWidgetItem`/
    `QLayoutItem` reference held; `AgentAppSession.shutdown()` completes cleanly before the
    crash every time). Step 3 recommendation: subprocess-based stress detector
    (N=25, >99.9% detection power), `xfail(strict=False)`, no fix in this ticket's scope.
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_dialog_settle_teardown_stress.py` — subprocess-based stress
    detector (N=25 isolated child `pytest` runs of `tests/test_agent_dialog_settle_e2e.py`,
    asserting all exit 0). Reviewer live-verified the crash-signal detection mechanism
    (synthetic SIGSEGV child correctly reported) and architecture-plan fidelity; the
    underlying upstream crash did not reproduce in the reviewer's 50-run sandbox sample
    (consistent with per-instance heap/ASLR sensitivity noted in Step 2, not a harness
    defect). No production code touched. Intentionally unmarked (no `xfail`/`skip`) per
    Step 3 rules; final CI marking deferred to Step 4.
- [x] **STEP 4: Development**
  - [x] Added the final CI marker deferred by Step 3:
    `@pytest.mark.xfail(reason=..., strict=False)` on
    `test_all_child_runs_exit_zero_under_repeated_teardown_stress` in
    `tests/test_agent_dialog_settle_teardown_stress.py` (line 123). Reason string
    names PYPOST-1040, the upstream PySide6/shiboken6 6.11.1 `QWidgetItem`
    GC-teardown defect, the measured ~32.5% (13/40) crash rate, and points at
    `ai-tasks/PYPOST-1040/20-architecture.md` for full evidence. `strict=False`
    is set per architecture's Q&A so a future `XPASS` (e.g. after a PySide6
    upgrade fixes the defect) is a visible, non-blocking signal rather than a
    build failure. Also replaced the module docstring's now-stale "Why this
    file is committed without an xfail/skip marker" section with a "Why this
    test carries an xfail(strict=False) marker" section explaining the
    Step 3 → Step 4 handoff. No production code (`pypost/`) touched — this is
    an upstream binding defect, no PyPost-owned fix is in scope per
    `10-requirements.md`'s "out of scope" section, and
    `tests/test_agent_dialog_settle_e2e.py`'s existing assertions were not
    edited. `STRESS_ITERATIONS`, subprocess mechanics, and all other detection
    logic left unchanged.
  - [x] Confirmation: `pytest tests/test_agent_dialog_settle_teardown_stress.py
    --collect-only -m slow -q` collects the 1 test cleanly (valid marker
    syntax, still selected under `-m slow`). A throwaway standalone script
    outside the repo (not committed) exercised `xfail(reason=..., strict=False)`
    on a deliberately-failing and a deliberately-passing dummy test via a real
    pytest run: result was `1 xfailed, 1 xpassed` with **exit code 0** for
    both, confirming neither an XFAIL (current status quo — crash still
    reproduces) nor a future XPASS (upstream fix) would block CI — matching
    the marker's intended behavior on the real test. Full `STRESS_ITERATIONS
    = 25` stress run was deliberately not executed here (multi-minute,
    probabilistic, and not needed to confirm marker wiring); the committed
    constant is unchanged.
  - Follow-up "attempt a mitigation" Jira ticket and the TD-1
    (`ai-tasks/PYPOST-968/60-tech-debt.md`) evidence update remain Step 7/8
    work per architecture — not created/edited in this step.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1040/40-code-cleanup.md` — nothing to fix. `flake8` (repo's linter, run
    directly against the test file since `make lint` hardcodes `pypost/`) is clean (0 findings);
    no unused imports/variables, dead code, commented-out code, or debug prints found; no line
    exceeds 100 chars; 4-space indentation, no tabs/trailing whitespace; no `black`/`ruff format`
    target or package exists in this repo to run. Module-level `pytestmark` timeout(150) marker
    confirmed present (not duplicated). `pytest --collect-only -m slow -q` still collects the 1
    test cleanly. Only `tests/test_agent_dialog_settle_teardown_stress.py` was in scope; no other
    file was touched.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1040/50-observability.md` — no production code (`pypost/`) was touched by
    this task (see `10-requirements.md`'s "What is out of scope"), so this step's scope was
    limited to auditing the Step 3/4 test artifact's own failure-diagnostic output. Found and
    fixed a real gap: `tests/test_agent_dialog_settle_teardown_stress.py`'s carefully-built
    per-child crash detail (signal name, stdout/stderr tail) was passed only to `pytest.fail()`,
    but because the test is `xfail(strict=False)`, pytest's default `--xfail-tb=False` (not set
    anywhere in this repo) silently drops that detail from the terminal report on the expected
    XFAIL path — only the static marker `reason=` string would show. Added one `_LOGGER =
    logging.getLogger(__name__)` + one `_LOGGER.warning(summary)` call (stdlib `logging`, no new
    dependency) right before the existing `pytest.fail(summary)`, so the same detail is also
    emitted at WARNING and surfaces via this repo's already-configured `log_cli`/`--log-file`
    (`pyproject.toml`) regardless of XFAIL/FAIL classification. `STRESS_ITERATIONS`, subprocess
    mechanics, and all detection/failure logic are unchanged — only python module compiles and
    `flake8` is clean, `pytest --collect-only -m slow -q` still collects the 1 test.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1040/60-tech-debt.md` — created. No production code was
    touched by this task, so no PYPOST-1040-owned blocker; documents the two
    legitimate judgment calls made in the test artifact (`xfail(strict=False)`
    as a deliberate permanent classification, and bounded/reduced
    confirmation runs vs. the full `STRESS_ITERATIONS=25` during Steps 3/4/6
    review), no missing tests beyond existing coverage, and records the
    recommended (not yet ticketed) mitigation-attempt follow-up referencing
    architecture's three candidates.
  - `ai-tasks/PYPOST-968/60-tech-debt.md` — extended TD-1 in place (not
    duplicated): priority raised **Low → Medium**; added the new Linux/Python
    3.13.5/PySide6 6.11.1 reproduction evidence (32.5%, 13/40, N=40), root
    cause (`SettingsDialog` nested-layout subtree + pytest's forced cyclic
    GC), a pointer to the new
    `tests/test_agent_dialog_settle_teardown_stress.py` stress detector, and
    a link to `ai-tasks/PYPOST-1040/20-architecture.md`. Prior Jira links
    (PYPOST-1040, PYPOST-429 lineage) and original evidence text kept intact.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/agent_dialog_settle.md` — updated (not duplicated) in place. Rewrote the stale
    "Native crash after tests report PASS" Troubleshooting row: states the crash **is**
    diagnosed (upstream PySide6/shiboken6 6.11.1 `QWidgetItem` GC-teardown defect triggered
    by pytest's forced cyclic GC acting on `SettingsDialog`'s nested-layout widget subtree),
    names the measured rate (32.5%, 13/40, Linux/Python 3.13.5/PySide6 6.11.1), and points at
    the new detector. Added a new "Teardown stress detector (PYPOST-1040)" subsection under
    API / Usage (sibling to the existing "Timeout companion" / "Forced-timeout DEBUG contract"
    subsections) introducing `tests/test_agent_dialog_settle_teardown_stress.py`: what it does
    (`STRESS_ITERATIONS = 25` isolated child `pytest` runs, asserts each exits 0), why it is
    `xfail(strict=False)` (upstream defect, no PyPost fix in scope, XPASS is a visible
    non-blocking signal), how to run it (`pytest tests/test_agent_dialog_settle_teardown_stress.py
    -m slow -v` / `make test-slow`), and that it is excluded from default CI (`-m "not slow"`).
    Added two Related links to `ai-tasks/PYPOST-1040/20-architecture.md` (full investigation)
    and `ai-tasks/PYPOST-1040/60-tech-debt.md` (disposition + PYPOST-1115 follow-up), matching
    this doc's existing `../../ai-tasks/...` relative-link convention. No other file under
    `doc/dev/` touched; existing structure, tone, and unrelated content preserved.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1040/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1040/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1040/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1040/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1040/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash: `deabefb7e2c453a0864b90a5b81d37fea991cb39` (on `dev`)
- Message: `test(agent): PYPOST-1040 diagnose intermittent Qt teardown SIGSEGV`
- Follow-ups: [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) (mitigation
  attempt), [PYPOST-1116](https://pypost.atlassian.net/browse/PYPOST-1116)
  (`duration_report.py` xfail mis-reporting)
