# Roadmap: PYPOST-1070

## Task Metadata

- **Implementation language**: Python (confirmed — the repo is a Python project; `tests/` is
  the pytest suite whose files trigger the flake8 E402 findings this ticket addresses, and any
  fix mechanism — noqa comments or import reordering — is applied to Python source files).
- **Branch name**: `style/PYPOST-1070-fix-pytestmark-e402` (reference only; work remains on
  `dev`)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1070/00-roadmap.md` — this file.
  - `ai-tasks/PYPOST-1070/10-requirements.md` — requirements for resolving repo-wide flake8
    E402 noise caused by the `pytestmark`-before-imports convention in `tests/`.
  - Verified current flake8 E402 count against Jira's claimed "692 hits across 207 files":
    measured **642 hits across 110 files** (see requirements doc Q&A for the discrepancy
    analysis and reproduction command).
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1070/20-architecture.md`.
  - **Decision**: fix mechanism = **restructure** (move `pytestmark = pytest.mark.timeout(...)`
    to immediately after the last top-level import), not `# noqa: E402` suppression. Verified via
    `tests/conftest.py` (`item.get_closest_marker("timeout")`, position-independent) and
    `pycodestyle.py`'s `module_imports_on_top_of_file` source (installed 2.14.0) that no
    ordering constraint forces `pytestmark` before imports, and that ~106-124 of the 234 files
    already using the convention already place it after imports (the target shape is already
    the in-repo majority). See architecture doc for full justification.
  - Mechanical fix: one AST-located, line-slice-based Python script (design only — Step 4
    implements/runs it) scoped to the 110 currently-flagged files.
  - Failing repro (Step 3) design: new permanent regression test
    `tests/test_lint_pytestmark_e402.py` asserting `flake8 --jobs=1 --select=E402 tests/` is
    empty; naturally red today (642 hits), runs forever after via `make test` (no Makefile
    change, `make lint` scope explicitly stays `pypost/`-only per requirements DoD).
- [x] **STEP 3: Failing Repro Test**
  - Test: `tests/test_lint_pytestmark_e402.py` (new, permanent regression test) —
    shells out to `sys.executable -m flake8 --jobs=1 --select=E402 tests/` via
    `subprocess` and asserts zero findings; `pytest.mark.timeout(30)`,
    subprocess `timeout=20`. Written directly in the target (imports-first,
    `pytestmark`-last) shape so it does not trip the very check it enforces —
    confirmed via `flake8 tests/test_lint_pytestmark_e402.py` (exit 0, zero
    findings of any code, not just E402).
  - Confirmed RED today (`.venv/bin/python -m pytest
    tests/test_lint_pytestmark_e402.py -v`): 1 failed in 1.93s (subprocess
    itself measured 1.89s, matching Step 1/2's ~1.9s figure). Failure message:
    "flake8 --jobs=1 --select=E402 tests/ reported 642 finding(s) (expected
    0). returncode=1", with the first 10 concrete `file:line` E402 hits
    embedded (e.g. `tests/test_alert_manager.py:6:1: E402 module level import
    not at top of file`) plus a "... and 632 more" count and empty stderr. 642
    matches Step 1/2's re-confirmed baseline exactly — this is the intended
    real defect (pytestmark-before-imports pattern across 110 files), not a
    broken fixture, import error, or flake8-invocation bug (returncode 1 =
    findings present, not a config/invocation error; stderr empty).
  - No `xfail`/`skip` markers used. No files touched other than this new test
    file and this roadmap. `pypost/` untouched. None of the 110 flagged
    `tests/*.py` files restructured (deferred to Step 4).
- [x] **STEP 4: Development**
  - [x] Iteration 1 (mechanical bulk fix): wrote `scripts/fix_pytestmark_e402.py`
    (AST-located line-slice edit, per architecture doc's algorithm; `--dry-run`
    mode + built-in self-verification via `flake8 --select=E402 tests/`).
    Dry-run first (107 fixed / 3 skip / 0 error), spot-checked 3 sample diffs
    (`tests/test_code_editor.py`, `tests/test_settings_encryption.py`,
    `tests/test_worker_race.py` — all call-form; confirmed 0 of the 18
    list-form `pytestmark = [...]` files are in the flagged set, matching the
    architecture doc). Ran for real: 107 files fixed, 3 skipped (flagged for
    manual review by the 4th trigger — see below), 0 errors. Self-verification
    correctly exited non-zero (3 files still have E402 findings, expected —
    those need the manual follow-up in iteration 2).
    **Discrepancy from architecture doc found during implementation**: the
    4th-trigger predicate (any top-level statement between imports that is not
    `pytestmark`/`Import`/`ImportFrom`) flagged **3** files, not the "exactly
    one" the architecture doc asserted. The two extras
    (`tests/test_request_manager.py`, `tests/test_request_manager_delete.py`)
    each have a top-level `try: import platformdirs / except
    ModuleNotFoundError: ...` block between import groups. Traced against
    pycodestyle's actual `allowed_keywords` list (quoted in the architecture
    doc's own Research section) — `try`/`except` are pycodestyle-exempt, so
    this shape does **not** actually block E402-cleanliness the way the
    known `def _mock_save_dialog` exception does; the mechanical script's
    stray-node check is deliberately conservative (flags more than strictly
    necessary) rather than hardcoding pycodestyle's full exemption list. Both
    files only need the standard pytestmark relocation (no function move), see
    iteration 2.
  - [x] Iteration 2 (manual follow-up for the 3 flagged files): manually
    relocated `pytestmark` in `tests/test_request_manager.py` and
    `tests/test_request_manager_delete.py` to immediately after their last
    top-level import (same target shape as the mechanical fix; the
    intervening `try: import platformdirs / except ModuleNotFoundError:`
    block was left in place since pycodestyle exempts `try`/`except` from
    `seen_non_imports`) — verified individually E402-clean. Manually fixed
    the architecture doc's documented known exception,
    `tests/test_request_save_orchestrator.py`: relocated `pytestmark` after
    all imports, and relocated the `_mock_save_dialog` function definition
    (previously sandwiched between two import groups, pre-existing from
    PYPOST-317) to after `pytestmark` and before the
    `@pytest.mark.usefixtures("qapp")` / `TestRequestSaveOrchestrator` class,
    per the architecture doc's explicit guidance. Verified `ast.parse`
    succeeds and `flake8 --select=E402` is clean on this file too.
  - [x] Iteration 3 (verification): `flake8 --jobs=1 --select=E402 tests/` →
    **0 findings** (down from 642). `tests/test_lint_pytestmark_e402.py` →
    **PASSED**. `pytest tests/ --collect-only -q` → 2338/2361 collected, 0
    collection errors (23 deselected, pre-existing `-m "not slow"` default,
    unrelated). Ran all 110 changed files for real in 8 batches of ~14 files
    each (`QT_QPA_PLATFORM=offscreen pytest <batch> -m "not slow"`) — **1384
    tests passed, 0 failures** across all batches.
    A single full-batch run of all 110 files together in one process
    segfaulted (native crash in `pypost/ui/styles/style_manager.py:102
    apply_theme`, triggered from different GUI test files across two
    attempts) — investigated and confirmed **pre-existing, unrelated to this
    change**: reproduced identically when running the same full-batch command
    against the original (pre-fix, git-stashed) file contents (via `git stash
    push -- tests/` / `pop`), and each individual file passes cleanly on its
    own and in the chunked batches. This is native Qt/PySide6 resource
    accumulation across many `QApplication`-based tests sharing one process,
    unrelated to import/pytestmark ordering — noted for the orchestrator to
    triage separately (e.g. candidate for `pytest-forked`/process isolation
    or reduced per-process GUI-test batch size in CI), not a Step 4 blocker.
    `flake8 --jobs=1 pypost/` (the `make lint` scope) still 0 findings —
    confirms `pypost/` untouched. `git diff --stat` — exactly 110
    `tests/*.py` files changed (283 insertions, 222 deletions), nothing
    under `pypost/` or elsewhere; only new untracked file besides the script
    is `tests/test_lint_pytestmark_e402.py` (Step 3's own artifact, not
    edited, only re-run).
    **Scope note**: the architecture doc's own sequencing suggested folding
    the `doc/dev/testing.md` example-order update into Step 4, but the
    roadmap's STEP 8 artifact mapping (`doc/dev/`) and this step's explicit
    instructions (git diff --stat limited to `tests/*.py` + the script) place
    doc updates in STEP 8 — deferred there rather than duplicated here to
    avoid conflicting scope boundaries. Flagged explicitly so it is not
    silently dropped. The out-of-repo global `do-testing` skill file
    (`/home/.claude/skills/do-testing/SKILL.md`) update was attempted but the
    file is read-only in this environment; also deferred/flagged for Step 8
    or a follow-up outside this repo.
  - **Fix script disposition**: `scripts/fix_pytestmark_e402.py` kept
    committed (untracked, staged for the eventual commit step) — this repo's
    existing `scripts/` convention already contains multiple one-shot,
    ticket-scoped bulk-fix scripts left in place permanently as historical
    record (e.g. `scripts/fix_jira_debt_summaries.py`,
    `scripts/encryption_migrate.py`), matching the architecture doc's
    proposed location and precedent citation.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1070/40-code-cleanup.md`.
  - `make lint` still only covers `pypost/` (confirmed empty, unaffected). Ran
    `flake8 --jobs=1` directly on the 110 changed `tests/*.py` files plus
    `scripts/fix_pytestmark_e402.py` and `tests/test_lint_pytestmark_e402.py`, matching prior
    steps' approach. Isolated new-vs-pre-existing findings via a `git stash push -u --
    tests/ scripts/fix_pytestmark_e402.py` / re-run / `git stash pop` before/after diff: every
    pre-existing finding code in the 110 files stayed the same or decreased (E402: 642 → 0 as
    intended; a handful of E302/E304/E305 disappeared incidentally); **zero new findings in the
    110 files**.
  - Found 2 new `E203` findings in `scripts/fix_pytestmark_e402.py` (slice spacing,
    100% new code from this ticket) — fixed (2-line whitespace-only edit, behavior verified
    unchanged via `--dry-run` re-run). Left the script's 6 `T201 print found.` findings as-is —
    matches the established repo-wide convention of bare `print()` in `scripts/` (18 other
    scripts do the same; `scripts/` is outside `make lint`'s scope).
  - Confirmed `tests/test_lint_pytestmark_e402.py` still carries `pytest.mark.timeout(30)`
    (untouched since Step 3) and all 110 restructured files still carry their own `pytestmark`
    timeout markers (0/110 missing; spot-checked 10 files' actual values 10/30/60/120s intact).
  - No merge-conflict markers, no unused imports/variables, no dead code, no commented-out code
    in any touched file. `ast.parse` clean on all 112 touched files. `pypost/` untouched
    (`git diff --stat -- pypost/` empty; `flake8 --jobs=1 pypost/` still 0).
  - Re-ran `tests/test_lint_pytestmark_e402.py` (1 passed) and a 10-file / 94-test spot sample
    of restructured files (94 passed, 0 failures) after the script edit.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1070/50-observability.md`.
  - No `pypost/` production code exists to instrument in this task — scope limited to
    assessing the two artifacts' own diagnostic output.
  - `tests/test_lint_pytestmark_e402.py`: reviewed its `pytest.fail()` message fresh (not
    assumed fine from prior review). Found one genuine, low-risk clarity gap — the message's
    closing clause read "not fixed until Step 4's mechanical restructure lands," which is
    stale/misleading once Step 4 has landed (a *future* regression firing this test would read
    like a still-open known issue rather than a new regression the triggering change just
    introduced). Fixed: reworded that clause only (message text, not detection/fix logic) to
    describe the test as a permanent regression guard and state the concrete remediation
    (relocate the new/reordered `pytestmark` to after the file's imports). Re-ran
    `flake8 --jobs=1 tests/test_lint_pytestmark_e402.py` (0 findings) and
    `pytest tests/test_lint_pytestmark_e402.py -v` (1 passed, 1.90s) after the edit — no
    behavior change.
  - `scripts/fix_pytestmark_e402.py`: reviewed its run-time output — already prints a
    found-count line, a per-file `path: status` line for every processed file, an aggregate
    `Summary: N fixed, M skipped, K errors (...)` line, and (non-dry-run only) a
    self-verification re-run of `flake8 --select=E402` with remaining findings printed to
    stderr on failure. Judged adequate for a one-shot, unlikely-to-be-rerun bulk-fix utility;
    no changes made.
  - Full assessment, judgment, and template in `ai-tasks/PYPOST-1070/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1070/60-tech-debt.md`.
  - **Shortcuts Taken**: none — no `pypost/` production code touched; the judgment calls from
    Steps 1-6 (conservative 4th-trigger detection, bounded/spot-check verification rather than
    exhaustive) are legitimate engineering choices, not corner-cutting.
  - **Code Quality Issues**: `scripts/fix_pytestmark_e402.py`'s `main()` loop has no catch-all
    exception handler around `fix_file()` calls beyond the internal `ast.parse`-related
    `SyntaxError` catches (Step 6 finding). Assessed as genuinely low-risk (every target file
    already passed flake8's own tokenization, and the script is a one-shot bulk-fix utility, not
    a maintained recurring tool) — recorded as a documentation-only note, no follow-up ticket.
  - **Missing Tests**: none beyond this ticket's own scope.
  - **Timeout audit correction**: replaced the earlier 10-file marker-value spot-check with a
    bounded exhaustive audit of all 110 edited test modules plus the new regression module;
    111/111 have explicit module-level `pytest.mark.timeout` coverage (exit 0).
  - **Architecture deviations / hardcoded constants**: corrected the deviation analysis to
    record that the tracked developer-guide update was deferred from implementation to Step 8;
    implementation conformance is unchanged and the documentation gap is now resolved. This
    substantive correction requires Step 7 re-review. Assessed the 60/30/20-second bounds,
    10-finding diagnostic preview, and canonical blank-line spacing in `60-tech-debt.md`.
  - **Performance Concerns**: `tests/test_lint_pytestmark_e402.py`'s flake8 subprocess adds
    ~2s to every `make test` run — accepted, deliberate tradeoff per the architecture doc's
    Step 3 design, not a defect.
  - **Follow-up Tasks**: the pre-existing native segfault found during Step 4 verification
    (`pypost/ui/styles/style_manager.py:102 apply_theme`, full-batch 110-file run only,
    confirmed pre-existing via git-stash reproduction) is a genuine, reproducible, unrelated
    infra issue. Compared against `ai-tasks/PYPOST-968/60-tech-debt.md` TD-1 and
    `ai-tasks/PYPOST-1040/20-architecture.md` (which diagnosed a *related-class* but distinct
    Qt/PySide6 teardown crash in `SettingsDialog`/`QWidgetItem`, triggered by pytest's
    forced-GC at session end after just 2 tests): different crash site (`apply_theme`'s
    `app.setStyle()`/`QStyleFactory` churn vs. `QLayout`/`QWidgetItem` cyclic-GC teardown),
    different trigger condition (resource accumulation across a large 110-file/1384-test batch
    vs. forced GC after a single 2-test module) — same broad class (Qt/PySide6 native
    instability under GUI test load), not confirmed same root cause. Recommendation: file a
    **new** Jira Debt ticket (not an extension of PYPOST-1040/PYPOST-1115), scoped to
    diagnosing GUI-test-process instability at large batch size, explicitly cross-referencing
    PYPOST-1040 as related prior art. Full detail and reasoning in
    `ai-tasks/PYPOST-1070/60-tech-debt.md`. Phase D created
    [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) (13 SP, Medium).
- [x] **STEP 8: Dev Docs**
  - Final `make check`: lint and documentation checks passed; full suite completed with
    2,335 passed and three baseline-confirmed pre-existing failures tracked by PYPOST-1110
    and PYPOST-1111. No PYPOST-1070-caused failures remain.
  - Updated `doc/dev/testing.md` overview and declaration guidance to establish the canonical
    ordering: all standard-library, third-party, and project imports first, followed by the
    module-level `pytestmark` assignment.
  - Added usage and troubleshooting guidance that explicitly rejects `# noqa: E402`
    suppression and directs contributors to move `pytestmark` after the final import.
  - Validation: Markdown structure inspected; policy phrases and example ordering verified;
    `git diff --check` passed. Execution is complete and awaiting Step 8 review.
- [x] **COMMIT: Commit Changes**
  - Implementation commit: `98dd93d6` — `style(tests): PYPOST-1070 fix pytestmark E402 noise`.
  - Current branch: `dev`; suggested branch reference:
    `style/PYPOST-1070-fix-pytestmark-e402`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1070/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1070/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1070/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1070/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1070/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- `98dd93d6` — `style(tests): PYPOST-1070 fix pytestmark E402 noise`
