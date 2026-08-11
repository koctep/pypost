# PYPOST-1007: Technical Debt Analysis

## Shortcuts Taken

- **Whole-baseline regeneration in one commit, not a gradual migration.**
  `mypy-baseline.json` was fully regenerated via `--update-baseline` (219 v2
  entries, up from 218 v1 entries) and is committed atomically with the
  script change, rather than migrated incrementally. This was an explicit,
  reasoned architecture decision (`20-architecture.md` → "Migration story"),
  not an oversight: the old format never stored `message` text, so there is
  nothing to hand-migrate from — any migration would have to re-run mypy
  anyway, at which point it *is* `--update-baseline`. It is still worth
  flagging as debt-adjacent because it means **the diff between old and new
  `mypy-baseline.json` is not reviewable error-by-error in the PR** (git
  shows a near-total file rewrite: 1318 changed lines out of ~1300). A
  reviewer cannot easily confirm "no baselined error was silently dropped or
  added" by eyeballing the diff alone; they must trust the script's own
  round-trip tests plus the `error_count` field (218 → 219, +1 entry, no
  errors resolved — consistent with a pure key/format change over an
  unchanged codebase). This is a one-time cost specific to this cutover, not
  a recurring pattern.
- **Legacy-format rejection has no soft/dual-read path.** By design
  (`_load_baseline` hard-rejects any file without `"version": 2`), any
  branch that rebases across this commit without regenerating its baseline
  will hit a `ValueError` on the next `make typecheck` run. This is called
  out as an accepted, low-blast-radius risk in the architecture doc (`make
  typecheck` is not part of `make check`/CI), and the error message tells
  the developer exactly what to run (`--update-baseline`) — but it is a real
  (if minor and self-resolving) rough edge for anyone with a long-lived
  local branch spanning this change.
- **`_ERROR_RE`'s path prefix duplicates `MYPY_PATHS`.** The regex hardcodes
  `pypost/(?:core|models|ui)/` as a literal alternation
  (`scripts/check_mypy_baseline.py:29`) instead of deriving it from
  `MYPY_PATHS` (`scripts/check_mypy_baseline.py:26`). This predates
  PYPOST-1007 (inherited from the existing script) and this task did not
  touch it, but it is a latent trap: if `MYPY_PATHS` is ever extended (e.g.
  a future task adds `pypost/services`), the regex must be manually kept in
  sync or newly-scoped errors will silently fail to parse (parsed count
  quietly drops, no error raised). Not introduced by this task, but not
  fixed either, and this task's own docstring (line 2) name-checks itself
  alongside PYPOST-734/815 as maintaining this file, so it is fair to note
  here rather than pretend it's someone else's problem.

## Code Quality Issues

None found that need action. The extraction of `_error_key`, `_diff_errors`,
`_format_new_report`, and `_format_fixed_report` as small, single-purpose,
pure functions is a clear improvement over the previous `main()`-monolith
shape and matches the architecture's stated intent (pure-function extraction
for testability). One minor, harmless naming/structure deviation from the
architecture doc is noted below under "Deviations from Architecture" — it
is a quality *improvement*, not a regression, so no follow-up is warranted.

## Missing Tests

Three gaps survive an honest line-by-line comparison against the
architecture doc's test-impact section and the task brief's specific
prompts:

1. **`_format_new_report` / `_format_fixed_report` have no direct unit
   tests.** These two functions implement a non-trivial, explicitly-designed
   display contract (`20-architecture.md` → "Which line to show for a new
   key with multiple current-run instances" — the `(N new of M total)` /
   `(N of M baselined)` suffix logic, and "all current-run line numbers,
   sorted ascending"). Neither function is called from any test in
   `tests/test_mypy_baseline.py` — grep confirms zero references. The one
   test that exercises `main()` end-to-end
   (`test_gate_treats_line_shifted_error_as_unchanged`) only asserts on the
   process exit code for the *zero-diff* case; it never reaches the
   new/fixed report-formatting branch at all (no new/fixed keys are produced
   in that test), so the suffix logic, line-sorting, and the
   entirely-new-vs-partially-baselined branching are all exercised by
   neither a unit test nor the one integration-style test that exists. A
   regression here (e.g. an off-by-one in "N new of M total", or a sort
   order bug) would not be caught by the current suite.
2. **No test for a completely empty baseline / a clean (zero-error) mypy
   run.** All `_diff_errors` tests pass a non-empty baseline and/or a
   non-empty current list. There is no test asserting `_diff_errors([], [])
   == ([], [])`, and no end-to-end `main()` test for the "mypy baseline OK"
   success path (current == baseline, both non-trivial) or the
   fully-resolved-codebase edge case (baseline has entries, current mypy run
   returns zero errors — i.e., every baselined error was fixed). This is a
   real, if low-probability (~0 baselined errors is aspirational for this
   codebase today), gap in edge-case coverage explicitly called out by the
   task brief.
3. **The legacy-format-rejection test only checks a substring of the error
   message, not its full content.**
   `test_load_baseline_rejects_legacy_flat_string_format` asserts
   `pytest.raises(ValueError, match="--update-baseline")` — this confirms
   the actionable instruction is present but does not verify the message
   also names the file (`mypy-baseline.json`) or explains *why* it was
   rejected ("legacy/unrecognized format", `"version": 2` expectation). A
   future edit that broke the "why" portion of the message while
   accidentally preserving the word `--update-baseline` (e.g. from an
   unrelated refactor) would not be caught. Minor, since the actionable part
   (what to run) is the most important part and *is* covered.

None of these are severe enough to block merge — `_diff_errors` (the core,
architecturally-critical multiset logic) has thorough, explicit multiset
coverage (`test_diff_errors_multiset_partial_fix/new_duplicate/full_fix`),
and the empty-baseline/empty-current cases are trivial degenerate cases of
already-tested Counter-subtraction behavior, not new logic paths. They are
listed as genuine gaps worth a small follow-up, not blockers.

## BLOCKER CHECK: Explicit Timeout Markers

**Verified directly, not assumed.** `tests/test_mypy_baseline.py` line 22:
`pytestmark = pytest.mark.timeout(30)` at module scope, applying to all 14
collected test items across `TestMypyBaseline`, `TestDiffErrors`,
`TestLoadBaseline`, and `TestWriteBaseline` — confirmed by grep (no
class/function-level marker overrides, and no test lacks the module-level
mark). `PYTEST_ARGS="tests/test_mypy_baseline.py -v" make test` run fresh
during this review: **14 passed in 0.02s**, all shown with `[0ms]` timing.
The repo's `tests/conftest.py::pytest_runtest_setup` independently enforces
this at collection time (`pytest.fail(... "missing pytest.mark.timeout
marker" ...)` if any collected item lacks a timeout marker) — the suite
passing at all is itself corroborating evidence the marker is present and
effective. 30s is within the "Pure unit (mocked I/O): 10–30s" tier
recommended by `.cursor/lsr/do-testing.md` (all 14 tests are pure-unit or
hermetic tmp_path-based; none touch a live mypy subprocess).

**No blocker.**

## Performance Concerns

None. This is a synchronous, single-invocation CLI script; the entire test
suite runs in 0.02s. The dominant cost (the live `mypy` subprocess) is
unchanged by this task and outside this script's control, consistent with
the Step 6 observability analysis's conclusion. No optimization work is
warranted or was found necessary.

## Deviations from Architecture

A line-by-line comparison of `scripts/check_mypy_baseline.py` against
`20-architecture.md`'s "Module responsibilities" table, "Diff algorithm,"
"Baseline JSON shape," "Impact on existing functions," and "Non-goals"
sections found the implementation matches the design closely. One
structural deviation, no functional deviations:

- **Report formatting was extracted into two named functions
  (`_format_new_report`, `_format_fixed_report`) rather than left inline in
  `main()`.** The architecture doc's component table states `main()` "owns
  all string formatting of `_diff_errors`'s key-tuples into the
  human-readable report" and describes the suffix/line-listing logic as
  part of `main()`'s responsibility, without naming these as separate
  functions. The actual implementation factors that logic into two
  standalone, `main()`-called helper functions instead. This is a
  beneficial deviation (smaller, more testable units, consistent with the
  architecture's own "pure-function extraction for testability" pattern
  applied one level further than the doc spelled out) and does not change
  any observed behavior — but it is flagged here for honesty, and because
  it is directly relevant to the "Missing Tests" gap above: had the doc's
  literal shape been followed (formatting inline in `main()`), the missing
  direct-unit-test gap for the formatting logic would have been structurally
  unavoidable without mocking `main()`'s I/O; because it *was* extracted as
  named functions, the missing tests are a pure oversight, not a
  design-forced gap — i.e., they are easy to add later with no further
  refactoring.

Everything else checked line-by-line against the architecture doc matches
exactly: `_error_key` = `(path, code, message)`; `Counter`-based multiset
diff (not set diff) in `_diff_errors`; `BaselineEntry` has no `line` field;
`MypyError` retains `line` for display only and is structurally excluded
from the diffed `Counter`; `_write_baseline` preserves duplicate entries
(no dedup) and sorts by `(path, code, message)`; `mypy-baseline.json` v2
shape (`version`, `scope`, `error_count`, `errors: [{path, code, message}]`)
matches exactly, confirmed by direct inspection of the regenerated file;
`_load_baseline` rejects legacy format via the `"version" != 2` check
without attempting best-effort migration; `--update-baseline` bypasses
`_load_baseline` entirely (writes directly from the live run, per the
"regenerate, don't migrate" decision); no column-number tracking was
introduced; `MYPY_PATHS`/`_run_mypy`'s invocation are unchanged; `make
typecheck`'s optional-gate role is unchanged.

## Hardcoded Values

- `BASELINE_VERSION = 2` (`scripts/check_mypy_baseline.py:27`) — a genuine,
  intentional format-version constant, not a magic number; used consistently
  in both the write path (`_write_baseline`) and the read/reject path
  (`_load_baseline`), with no duplication. Not debt.
- `MYPY_PATHS = ("pypost/core", "pypost/models", "pypost/ui")`
  (`scripts/check_mypy_baseline.py:26`) — unchanged from before this task,
  and correctly used as the single source of truth for `_run_mypy`'s
  subprocess args and the written baseline's `scope` field. **However**, it
  is *not* the source of truth for `_ERROR_RE`'s path-matching alternation
  (`pypost/(?:core|models|ui)/`, line 29), which hardcodes the same three
  directory names as a separate literal — see "Shortcuts Taken" above. This
  is pre-existing (not introduced by PYPOST-1007) but is a real duplication
  that this task's own docstring takes ownership of by listing itself
  alongside the scripts that maintain this file.
- `pytest.mark.timeout(30)` (`tests/test_mypy_baseline.py:22`) — consistent
  with the project's documented "pure unit: 10–30s" tier
  (`.cursor/lsr/do-testing.md`); not arbitrary, and matches the value used
  by comparable pure-unit test modules elsewhere in the suite. Not debt.
- No other hardcoded magic numbers, credentials, URLs, or environment-
  specific values were found in either changed file.

## Follow-up Tasks

Conservative list — only items with a genuine, actionable, non-trivial
future benefit are included; routine "could always add more tests"
busywork is deliberately left out.

1. **Add direct unit tests for `_format_new_report` and
   `_format_fixed_report`.** Cover: the "(N new of M total)" /
   "(N of M baselined)" suffix appearing only when partial, the suffix being
   omitted when a key is entirely new/entirely fixed, and ascending line-sort
   for the new-error report. Small, low-risk, closes the most concrete gap
   found in this review (see "Missing Tests" #1).
   - **Jira:** [PYPOST-1065](https://pypost.atlassian.net/browse/PYPOST-1065)
2. **Add an empty-baseline / zero-current-errors test pair.** One test
   asserting `_diff_errors([], [])` reports no diff, and one end-to-end
   `main()`-level test for the "every previously-baselined error is now
   fixed" case (current mypy output has zero errors, baseline is non-empty)
   — currently untested in either direction (see "Missing Tests" #2).
   - **Jira:** [PYPOST-1066](https://pypost.atlassian.net/browse/PYPOST-1066)
3. **Derive `_ERROR_RE`'s path alternation from `MYPY_PATHS` instead of
   duplicating the directory list as a literal regex alternation.** Pure
   pre-existing tech debt (not introduced by this task) that this task's
   review surfaced as newly relevant: PYPOST-1007's docstring and design
   both treat `MYPY_PATHS` as the single source of truth for scope, but the
   regex isn't wired to it. Low priority — only bites if/when scope is ever
   extended — but cheap to fix and removes a silent-failure trap (a new
   scoped directory whose errors just don't get parsed, no error raised).
   - **Jira:** [PYPOST-1067](https://pypost.atlassian.net/browse/PYPOST-1067)

Not filed as follow-ups (considered and rejected as not worth a ticket):

- Strengthening the legacy-format-rejection message-content test beyond its
  current substring check — genuinely minor, the covered substring
  (`--update-baseline`) is the actionable part of the message; not worth a
  standalone ticket, better folded into follow-up #1/#2's test-file touch if
  anyone picks those up.
- The one-commit baseline regeneration's un-reviewable diff — this is a
  one-time cutover cost with no recurring instance to fix; nothing to file.
- The legacy-format hard-rejection's lack of a dual-read path — an
  intentional, already-justified architecture decision with an
  already-low, already-accepted blast radius (`make typecheck` not gating
  CI); revisiting it would contradict the architecture doc's own reasoning
  without new evidence, so no ticket.

## Verdict

**SAFE TO CLOSE.**

The implementation matches the architecture doc's design with only one
minor, beneficial structural deviation (report formatting factored into
named functions rather than left inline in `main()`) and zero functional
deviations. The mandatory timeout-marker blocker check passed: all 14 tests
in `tests/test_mypy_baseline.py` carry the module-level
`pytest.mark.timeout(30)` marker, verified directly by inspection and by a
fresh green test run (14 passed in 0.02s), and independently enforced by
`tests/conftest.py`'s collection-time check. No performance concerns. The
"regenerate the whole baseline in one commit" choice is a deliberate,
architecturally-justified decision (not an unexamined shortcut), documented
honestly above with its one real cost (a non-reviewable bulk diff) rather
than hidden. Three missing-test gaps and one pre-existing hardcoded-value
duplication were found and are recorded as three conservative follow-up
items above — none of them block this task, since the core,
architecturally load-bearing logic (`_diff_errors`'s multiset behavior) has
thorough, explicit test coverage and the gaps found are in secondary
display-formatting and edge-case territory.
