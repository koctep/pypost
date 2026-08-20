# PYPOST-1070: Code Cleanup Report

## Scope

Changed set (per `git status`): 110 modified `tests/*.py` files (the E402 restructuring from
Step 4), plus two new untracked files — `scripts/fix_pytestmark_e402.py` (permanent repo
utility) and `tests/test_lint_pytestmark_e402.py` (Step 3's regression test, unedited since
Step 3). `pypost/` is untouched (`git diff --stat -- pypost/` is empty).

`make lint` only runs `flake8 --jobs=1 pypost/`, so it does not cover any of this ticket's
changed files (same conclusion Steps 1/2/4 already reached). Ran `flake8 --jobs=1` directly
against the 110 changed files + the new script + the new test file instead, matching the
approach used in prior steps.

## Method: isolating NEW findings from pre-existing debt

To distinguish findings this ticket's edits caused from pre-existing debt in the same files:

1. Ran `flake8 --jobs=1 <112 files>` on the current (post-Step-4) working tree → 264 findings.
2. `git stash push -u -- tests/ scripts/fix_pytestmark_e402.py` to restore the 110 tracked files
   to their pre-ticket `HEAD` content and remove the two new untracked files, then re-ran the
   same `flake8` command on the original 110 files → 943 findings (`git stash pop` restored the
   working tree immediately after).
3. Diffed before/after per file+code. Result: for every one of the 110 restructured files, every
   pre-existing finding code either stayed at the same count or *decreased* (E402: 642 → 0 as
   intended; E304 and E305 each dropped by exactly 1, in one file each; E302 dropped by a net 43
   across 42 files — 41 files −1 each, plus `tests/test_request_save_orchestrator.py` −2 (the
   file where `_mock_save_dialog` was also relocated per Step 4) — moving `pytestmark` also
   happened to resolve a handful of adjacent blank-line findings). **No file gained a new
   finding of any pre-existing code.** The only additions were in the two new files, which by
   definition cannot have "pre-existing" findings.

## Linter Fixes

- Fixed: `scripts/fix_pytestmark_e402.py` had 2 new `E203 whitespace before ':'` findings (lines
  104 and 106, PEP8-style slice spacing `lines[a : b]`). This is 100% new code introduced by this
  ticket (the script didn't exist before Step 4), so it doesn't qualify as pre-existing debt —
  fixed by removing the space before the colon in both slice expressions
  (`lines[mark_node.lineno - 1:mark_node.end_lineno]` and
  `lines[mark_node.end_lineno:last_import_end]`). Re-ran `flake8 --select=E203` on the file
  after the edit: 0 findings. Re-ran the script's own `--dry-run` mode afterward to confirm the
  slicing logic is unaffected (still reports 0 flagged files, i.e., behavior-neutral edit).
- Not fixed (deliberately, in scope terms): 6 `T201 print found.` findings in
  `scripts/fix_pytestmark_e402.py`. These are the script's intentional CLI status/summary output
  (per-file status lines, fixed/skipped/error summary, self-verification failure report), not
  debug leftovers. Checked repo precedent: `.flake8`'s `extend-select = T201` is not scoped out
  anywhere, but 18 other files under `scripts/` use bare `print()` the same way
  (`scripts/apply_debt_summary_fixes.py`, `scripts/encryption_migrate.py`,
  `scripts/audit_test_durations.py`, etc.) and `make lint` never covers `scripts/`. Converting to
  `logging` would be inconsistent with the rest of the directory and out of scope for a
  cleanup-only pass — flagged here for reviewer visibility, not changed.
- Not fixed (pre-existing, out of scope per requirements doc): 134 `E302`, 51 `E304`, 30 `E305`,
  17 `F401`, 13 `W293`, 6 `E501`, 3 `E741`, 1 `W391`, 1 `F841` findings remaining across the 110
  files after the diff in the previous section confirmed none of them are new (breakdown sums to
  256, reconciling with the Method section's 264-finding total across all 112 files minus the 2
  `E203` and 6 `T201` findings accounted for above). These predate this ticket and are unrelated
  to the `pytestmark`-position fix; the requirements doc explicitly scopes this ticket to E402
  only.
- `tests/test_lint_pytestmark_e402.py`: `flake8 --jobs=1` → 0 findings (unchanged from Step 3).

## Code Formatting

- [x] Automatic code formatting — N/A, no formatter (black/autopep8) configured in this repo;
  edits were the Step 4 script's mechanical line-slice moves, and this step's own edit
  (E203 fix) is a one-character-per-line whitespace removal, not a reformat.
- [x] Indentation and alignment fixes — checked for stray tabs (`grep -lP '\t'`) across all 112
  touched files: none found. `ast.parse` succeeds on all 112 files (no syntax/indentation
  breakage).
- [x] Line length correction — checked all 112 touched files for lines >100 chars (byte-length
  scan, then cross-checked against `flake8 --select=E501`); the 6 real E501 hits found
  (`tests/test_env_dialog.py`, `tests/test_history_panel.py`, `tests/test_main_window.py`,
  `tests/test_script_executor.py` — 2 lines) are byte-for-byte identical to the pre-ticket
  content, just shifted by 1 line number in 3 files because `pytestmark` moved. No new
  over-length lines. (One apparent 218-"char" hit from the raw byte-count scan in
  `tests/test_history_manager.py:208` was a false positive — a decorator comment line of
  multi-byte Unicode em-dashes; `flake8`'s own codepoint-based count does not flag it.)

## Code Cleanup

- Removed unused imports: 0 (none introduced by this ticket; `scripts/fix_pytestmark_e402.py`'s
  imports — `argparse`, `ast`, `subprocess`, `sys`, `pathlib.Path` — are all used;
  `F401` count in the 110 files is unchanged at 17, pre-existing).
- Removed unused variables: 0 (`F841` count unchanged at 1, pre-existing).
- Removed commented-out code: none found in the touched files or the new script.
- Removed debug prints: none removed — the new script's `print()` calls are its intended CLI
  output, not debug statements (see Linter Fixes above for the precedent check).
- Dead code: none found in `scripts/fix_pytestmark_e402.py` — every function
  (`get_flagged_files`, `fix_file`, `main`) is reachable and used; no unreachable branches.
- Merge conflict markers: none found (`grep -rlE '^(<<<<<<<|=======|>>>>>>>)'` across all 112
  touched files — empty).

## Validation Results

- [x] All tests passed — `tests/test_lint_pytestmark_e402.py` re-run standalone: 1 passed
  (1.89s). Spot-ran 10 randomly sampled restructured files (94 tests total, `-m "not slow"`,
  `QT_QPA_PLATFORM=offscreen`): 94 passed, 0 failures. Full-suite re-run of all 1384 tests across
  the 110 files was not repeated in this step because Step 4 already ran and passed all of them
  in 8 batches, and this step made zero edits to any of the 110 test files (only
  `scripts/fix_pytestmark_e402.py` was touched, for the E203 fix, and that edit's
  behavior-neutrality was independently verified via `--dry-run`).
- [x] All tests have explicit timeout markers — confirmed `tests/test_lint_pytestmark_e402.py`
  still has `pytestmark = pytest.mark.timeout(30)` (line 41, untouched since Step 3). Verified
  all 110 restructured files still contain a `pytestmark` assignment (`grep -q pytestmark`
  across all 110: 0 missing). Spot-checked 10 random files' actual `pytestmark` line content —
  all intact with their original per-file timeout values (10/30/60/120s), confirming the
  restructuring only moved the marker's *position*, never its content.
- [x] No merge conflicts — confirmed (see Code Cleanup above).
- [x] Syntax is valid — `ast.parse` succeeded on all 112 touched files.
- [x] Types are correct — N/A, no type annotations added/changed by this ticket's edits; mypy is
  scoped to `pypost/core,models,ui` per the Makefile and this ticket never touches `pypost/`.

## Notes

- `pypost/` confirmed untouched throughout (`git diff --stat -- pypost/` empty;
  `flake8 --jobs=1 pypost/` still 0 findings, i.e., `make lint`'s actual scope is unaffected).
- The only code change made in this step was the 2-line E203 whitespace fix in
  `scripts/fix_pytestmark_e402.py` (slice spacing only, no logic change; re-verified via
  `--dry-run` and a full `flake8` re-run on the file).
- `tests/test_lint_pytestmark_e402.py`'s assertion logic was not touched, per instructions.
- Full before/after flake8 output and the per-file/per-code diff used to isolate new findings
  from pre-existing debt were generated as scratch files during this step's analysis (not
  committed; reproducible via the two-command stash/diff procedure described above).
