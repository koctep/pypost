# PYPOST-1287: Technical Debt Analysis

Scope: the uncommitted diff on `dev` (base `aef30005`) in
`tests/test_pypost_1077_verification_artifacts.py`,
`ai-tasks/PYPOST-374/30-dialogs-audit-report.md` and
`doc/dev/verification_artifact_contracts.md`, plus the new
`tests/test_pypost_1287_failing_repro.py`. No production code (`pypost/`, `scripts/`) changed.

No item below is a **BLOCKER**. Both changed test modules declare a module-level
`pytestmark = pytest.mark.timeout(10)`, so the do-testing timeout rule is met.

## Summary Table

| ID | Priority | Item | Follow-up | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Medium | Count-word `_STALE_CLAIMS` entries clash with DoD 5 | yes | [PYPOST-1308][] |
| TD-2 | Low | Bare `"446"` / `"1,747"` substring denylist entries | yes | [PYPOST-1308][] |
| TD-3 | Medium | No make target for inventory script; docs use raw calls | yes | [PYPOST-1307][] |
| TD-4 | Low | Report figures are hand-edited; no report-shaped generator | yes | [PYPOST-1307][] |
| TD-5 | Medium | `make lint` does not flake8 `tests/` (existing) | yes | [PYPOST-1303][] |
| TD-6 | Medium | No SOLID re-audit of the grown dialogs | yes | [PYPOST-1309][] |
| TD-7 | Low | Prose module count and prose LOC are not validated | yes | [PYPOST-1308][] |
| TD-8 | Low | Validator/helpers live in a test module used as a library | yes | [PYPOST-1310][] |
| TD-9 | Low | Repro drives a test function via monkeypatched globals | no | accepted (design) |
| TD-10 | Low | Repro case 5 duplicates inventory parsing and the live test | no | covered by TD-8 |
| TD-11 | Low | Brittle `_SCOPE_RE`, `_TOTAL_RE`, `_NUMBER_WORDS` | no | accepted (design) |
| TD-12 | Low | Missing-module errors reported up to three times (script, R2, R6) | no | accepted |
| TD-13 | Low | `make check` fails only on a filed exit-policy test | no | [PYPOST-1299][] |

Suggested ticket grouping: TD-1, TD-2 and TD-7 as one "count- and figure-agnostic stale-claim
rules" Debt; TD-3 and TD-4 as one "make-only dialog inventory refresh" Debt; TD-6 and TD-8 as
their own Debts. TD-5 and TD-13 are already filed (existing); do not re-file.

## Shortcuts Taken

- **TD-4 (Low): the report refresh is a hand edit.** The figures in
  `ai-tasks/PYPOST-374/30-dialogs-audit-report.md` (rows, Scope, Total) were typed from the
  validator's failure output. `scripts/audit_dialogs_inventory.py --markdown` emits a
  `| Module | LOC | Non-empty |` table with full paths, while the report uses
  `| Module | LOC | Class | Responsibility | Opened from |` with bare filenames, so it cannot be
  pasted in. The validator makes this safe (any typo fails the gate with both values), but
  each future refresh stays manual. Fix: a generator, or a `--check`-style mode, that emits or
  rewrites only the LOC column and aggregates in the report's schema.
- **TD-3 (Medium): no `make` target wraps the inventory script.** `Makefile` has targets only
  for `scripts/audit_baseline_metrics.py`. `doc/dev/verification_artifact_contracts.md`
  still shows `.venv/bin/python scripts/audit_dialogs_inventory.py --markdown` / `--check`
  under Usage, which `AGENTS.md` (make-only) forbids, and its Troubleshooting entry still says
  "Regenerate the inventory, then reconcile ...", which points at the script workflow, not at
  the make-only refresh oracle that the report itself now documents
  (`make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py -q'`).
  The same raw calls appear in two more docs: `doc/dev/testing.md` (section "Dialog audit
  inventory (PYPOST-374)", ~lines 2030-2035: `--markdown`, `--check` and a raw
  `pytest tests/test_dialogs_audit.py -v` line) and `doc/dev/solid_audit.md` (~lines 199-206:
  "Regenerate inventory" and "Verify audit report lists every dialog module" blocks, also
  ending in a raw `pytest` line). The Troubleshooting and Usage wording is current contract
  text and can be corrected in Step 8 (doc-only). Adding the `make` target and repointing all
  three docs is a follow-up.
- **DoD 3 is met by review, not by automation.** "No prose that contradicts the refreshed
  inventory" was satisfied by hand: `The 486-LOC dialog` became `The dialog`, and `At 263 LOC`
  was re-checked against discovery. The architecture deliberately added no prose-figure rule;
  see TD-7.

## Code Quality Issues

- **TD-1 (Medium): count-specific denylist entries contradict DoD 5.** `_STALE_CLAIMS` keeps,
  verbatim from PYPOST-1077, `"seven modules"`, `"eight modules"`, `"all seven modules"` and
  `"all eight modules"`. They are negative pinned counts. If discovery legitimately shrinks to
  seven or eight modules, R5 requires `Individual audit complete for all <n> modules.` while
  the denylist forbids `all eight modules`, so the only passing wording is digits (`all 8
  modules`). The failure is loud (no false pass), but it is a pinned snapshot in all but name,
  and DoD 5 says expected values come only from discovery. The clash is only in the Verdict
  phrase (`all eight modules.`): the Scope wording `eight dialog modules` does not contain the
  substring `eight modules`, so a Scope count of eight passes. Fix: drop the count-word entries
  (R5 already checks the count against discovery) or anchor them to the historical context
  they were meant to catch.
- **TD-2 (Low): bare numeric substrings.** `"446"` and `"1,747"` are matched with `in` on the
  whole normalized report. A future real figure such as `1,446 LOC`, `4,460` or a date or ID
  containing `446` would be flagged as a stale claim. `"446 LOC"` and `"1,747 LOC"` already
  cover the intended prose. Fix: remove the bare entries or match with word boundaries.
- **TD-7 (Low): prose figures are unguarded.** The Executive Summary says "The current
  individual-dialog inventory contains nine modules" and `settings_dialog.py` says "At 263 LOC".
  R5 checks only the Scope token and the Verdict phrase. On the next module addition or
  `settings_dialog.py` change, these sentences go stale while the gate stays green. This is the
  same class of silent drift the task fixed for the inventory. Fix: either a generic rule
  (every `<count-word|digits> modules` and `<file> ... <n> LOC` in prose must match discovery)
  or remove figures from prose, as was done for `mcp_servers_dialog.py`.
- **TD-8 (Low): test module used as a library.** `_dialog_audit_report_errors`, its helpers and
  the PYPOST-1259 markdown parsers live in `tests/test_pypost_1077_verification_artifacts.py`,
  and both `tests/test_pypost_1259_failing_repro.py` and `tests/test_pypost_1287_failing_repro.py`
  import private names from it. The PYPOST-1259 tech-debt file already proposed extracting the
  parsers "if additional verification tests adopt" them; this task is the second consumer, so
  the trigger has fired. Fix: move parsers and the validator into a helper module (for example
  `tests/helpers/dialog_audit_contract.py`) and import from there.
- **TD-11 (Low, accepted): regex brittleness.**
  - `_SCOPE_RE` requires the exact `Scope: pypost/ui/dialogs/ (<n> [dialog ]modules, <x> LOC
    total)` shape; rewording yields `audit report missing scope total LOC statement`. Loud, so
    accepted.
  - `_TOTAL_RE` (`Total: ([\d,]+) LOC`) takes the first match on any line. A future earlier
    `Total: <n> LOC` line elsewhere in the report would be validated instead of the inventory
    Total. The report has one such line today. Low risk; could be scoped to the Module
    Inventory section.
  - `_NUMBER_WORDS` stops at twenty; beyond that the report must use digits, and an English
    word gives a loud `unparseable` error. Accepted.
- **TD-12 (Low, accepted): repeated missing-module messages.** A discovered module that is
  absent from the whole report yields three messages: the live wrapper's
  `check_audit_report_covers(modules)` (`scripts/audit_dialogs_inventory.py:50-57`,
  `Audit report missing dialog module(s): ...`), R2 (`module inventory missing discovered
  dialog module: ...`) and R6 (`testability table missing dialog module: ...`). A module
  missing only from the inventory table yields no coverage-script message, because that
  script checks for the filename as a substring of the whole report, so any mention elsewhere
  (for example the Testability table) satisfies it; only R2 (and R6, if also absent there)
  fires. The output is redundant, not wrong, and the coverage script adds nothing that R2 does
  not already catch.
- Validator complexity is acceptable: the former ~120-line test body is split into six pure
  helpers, each under 30 lines, with one error per violation. `names.count(n)` in the
  duplicate check is O(n^2) over nine rows; negligible.

## Missing Tests

- **TD-9 (Low, accepted): seam coupling.** Repro cases 1-4 call
  `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates()` directly after
  monkeypatching the module globals `discover_dialog_modules`, `check_audit_report_covers` and
  `_DIALOG_AUDIT_REPORT`. This was the Step 2 design so the red tests could run before the
  validator existed. A rename breaks loudly (`monkeypatch.setattr` raises on a missing
  attribute), so it is not a silent risk. Now that the pure `_dialog_audit_report_errors`
  exists, direct validator tests would be simpler; fold into TD-8 if that work happens.
- **TD-10 (Low): repro case 5 duplication.** `test_live_report_inventory_loc_matches_discovery`
  re-parses the inventory and silently drops rows with non-numeric LOC, while the live 1077
  test now checks the same thing more strictly. The synthetic report builder also overlaps
  with the fixture text in `tests/test_pypost_1259_failing_repro.py`. Covered by TD-8.
- Validator branches in `_dialog_audit_report_errors` and its helpers with no synthetic
  case in `tests/test_pypost_1287_failing_repro.py` (cases 1-4 drive the validator; case 5
  only re-parses the live report):
  - R1: a missing required section (`audit report missing section: ...`).
  - `_inventory_errors`: an empty inventory table; a table without `Module` / `LOC` columns;
    duplicate inventory rows; an invalid LOC (non-numeric, or `<= 0`).
  - `_aggregate_errors`: a missing Scope line; a missing Total line; an unparseable Total
    value. (Scope and Total LOC mismatch are covered by case 4.)
  - `_module_count_errors` (R5, DoD 4): the Verdict phrase missing, a Verdict count that
    mismatches discovery, and an unparseable Scope or Verdict count. Case 4 covers only the
    Scope count mismatch; its Verdict count is correct.
  - A missing `_SEMANTIC_PHRASES` phrase, and a present `_STALE_CLAIMS` entry.
- R6 testability mismatch is exercised but not asserted: case 3 builds the Testability table
  from the same rows as the inventory (`ghost_dialog.py` listed, `gamma_dialog.py` omitted), so
  `_testability_errors` fires, but the case asserts only that each filename appears on some
  line, which R2 already satisfies. A regression that silenced R6 would stay green.
- Case 3 also stubs `check_audit_report_covers` to `[]`, so the coverage-script message in
  the live wrapper (TD-12) is never exercised by the repro.
- Low priority; add direct validator tests for these branches when TD-8 moves the
  validator.
- No tests lack explicit timeout markers.

## Performance Concerns

- None. The validator parses one ~230-line markdown file in memory; the targeted run stays well
  inside the 10-second per-test timeout.

## Follow-up Tasks

1. **TD-1 + TD-2 + TD-7 (Medium)**: make stale-claim and prose-figure rules count- and
   figure-agnostic: drop the `seven`/`eight modules` entries and the bare `446`/`1,747`
   entries from `_STALE_CLAIMS`, and either validate or remove prose module counts and prose LOC
   in the PYPOST-374 report. Jira: [PYPOST-1308][].
2. **TD-3 + TD-4 (Medium)**: add a `make` target for `scripts/audit_dialogs_inventory.py`
   (`--check`, and a report-schema LOC output or in-place refresh), then replace the raw
   `.venv/bin/python scripts/audit_dialogs_inventory.py` calls and raw `pytest` lines with
   `make` targets in all three docs: `doc/dev/verification_artifact_contracts.md` (Usage),
   `doc/dev/testing.md` (~lines 2030-2035) and `doc/dev/solid_audit.md` (~lines 199-206).
   Jira: [PYPOST-1307][]. (Step 8 of this task should already fix the Troubleshooting wording.)
3. **TD-6 (Medium)**: SOLID re-audit of `mcp_servers_dialog.py` (486 -> 1,031 LOC, x2.1) and
   `library_dialogs.py` (533 -> 703 LOC). The report still rates `mcp_servers_dialog.py` SRP
   "OK" and `library_dialogs.py` SRP "OK" from the June 2026 walkthrough. Re-rating was out of
   scope (requirements Q4), but a module that doubled to over 1,000 lines is a likely SRP
   finding, and the report is used to rank refactoring work. Warranted. Jira: [PYPOST-1309][].
4. **TD-8 (Low)**: extract the PYPOST-1259 markdown parsers and the PYPOST-1287 validator from
   `tests/test_pypost_1077_verification_artifacts.py` into a shared test helper module, repoint
   both repros, and add direct validator tests for the uncovered rule branches.
   Jira: [PYPOST-1310][].
5. **TD-5 (Medium)**: `make lint` runs flake8 on `pypost/` only, so the new and changed test
   code is not linted by the gate. Already tracked: [PYPOST-1303][]. Do not re-file.

### Pre-existing Failures (already filed — do not re-file)

1. **TD-13** — [PYPOST-1299][] — `NON-BLOCKER — pre-existing`
   - `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
     (failed after 60 s).
   - `tests/test_pytest_exit_policy.py::`
     `test_make_test_cov_fails_closed_when_parallel_runner_is_missing`
     (hung; worker timeout at 120 s).
   - Only failure of the Step 5 `make check` run (368 files, 361 passed, 1 failed, 6 skipped).
     Makefile/runner policy, unrelated to this task. DoD 8 is met.

## DoD Status

- DoD 1, 2, 4, 5 (apart from TD-1), 6 and 8: met.
- DoD 3: met by hand review; not guarded automatically (TD-7).
- DoD 7: the figures and the "matches discovery" contract text are aligned. The Usage and
  Troubleshooting sections of the same doc still describe the raw-script workflow (TD-3);
  Step 8 should correct the Troubleshooting text.

[PYPOST-1299]: https://pypost.atlassian.net/browse/PYPOST-1299
[PYPOST-1303]: https://pypost.atlassian.net/browse/PYPOST-1303
[PYPOST-1307]: https://pypost.atlassian.net/browse/PYPOST-1307
[PYPOST-1308]: https://pypost.atlassian.net/browse/PYPOST-1308
[PYPOST-1309]: https://pypost.atlassian.net/browse/PYPOST-1309
[PYPOST-1310]: https://pypost.atlassian.net/browse/PYPOST-1310
