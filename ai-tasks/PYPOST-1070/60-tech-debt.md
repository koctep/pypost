# PYPOST-1070: Technical Debt Analysis

## Shortcuts Taken

None in production code — no file under `pypost/` was touched by this ticket (confirmed
repeatedly in Steps 4-6 via `git diff --stat -- pypost/` and `flake8 --jobs=1 pypost/`, both
empty/clean). The entire change is scoped to `tests/*.py` (110 files, mechanical restructure),
one new permanent regression test (`tests/test_lint_pytestmark_e402.py`), and one new permanent
repo tool (`scripts/fix_pytestmark_e402.py`).

The judgment calls made along the way are legitimate engineering trade-offs, not corner-cutting:

- **Conservative 4th-trigger detection** (Step 4): the mechanical script's stray-top-level-node
  check flags *more* files for manual review than strictly necessary (it does not hardcode
  pycodestyle's full `try`/`except` exemption list), trading a small amount of extra manual work
  (2 extra files, both trivial) for a simpler, more auditable, less failure-prone detector. This
  is the right trade for a one-shot bulk-fix script — the alternative (encoding pycodestyle's
  exemption logic exactly) would add code and coupling to an external library's internals for
  a two-file savings.
- **Bounded/spot-check verification rather than exhaustive runs** (Step 4-6): the 110 changed
  files were verified in 8 batches (1384 tests, all passing) rather than insisting a single
  full-batch run succeed, once that full-batch run was shown to fail for a reason unrelated to
  this ticket (see Follow-up Tasks below). Batching to work around a known, pre-existing,
  independently-confirmed environment issue — rather than blocking this ticket on fixing that
  unrelated issue — is a reasonable scope boundary, not a shortcut on this ticket's own
  correctness.

Neither of these compromises correctness of the delivered fix: `flake8 --jobs=1 --select=E402
tests/` is 0 findings (down from 642), and every one of the 1384 tests in the 110 changed files
passes.

## Code Quality Issues

**`scripts/fix_pytestmark_e402.py`'s `main()` loop has no catch-all exception handler around
`fix_file()` calls**, beyond the `ast.parse`-related `SyntaxError` handling already inside
`fix_file()` itself (flagged non-blocking at Step 6 review). Concretely: if a future re-run of
this script hits some other exception type while processing file *N* of *M* (e.g. a permissions
error, an encoding error on a file that isn't valid UTF-8, or an unanticipated AST shape that
raises something other than `SyntaxError`), the run aborts without printing the summary line
(`Summary: N fixed, M skipped, K errors`) for the files already processed, and without any
partial-progress report for the remaining files.

**Assessment (own judgment, not deferring to the Step 6 reviewer's framing)**: this is
genuinely low-risk and does **not** warrant a follow-up Jira ticket. Reasoning:

- Every file the script targets has already been positively confirmed to parse cleanly by two
  independent tools before the script ever touches it: `flake8`'s own tokenizer/AST-adjacent
  checks (that's how the 110-file target set was identified in the first place) and the
  script's own `ast.parse()` call. The realistic failure surface (file doesn't parse, file
  isn't readable) is already caught.
- The script is a **one-shot, ticket-scoped bulk-fix utility**, not a maintained, recurring
  tool invoked by CI or `make`. It is kept in `scripts/` only as historical record, matching
  existing repo precedent (`scripts/fix_jira_debt_summaries.py`,
  `scripts/encryption_migrate.py`) — the same precedent this ticket's own Step 4 cited for
  keeping it at all. A future maintainer re-running it against a *new* set of files would be
  doing so deliberately and would notice a silent abort immediately (no `Summary:` line, script
  exits without the expected re-verification `flake8` pass at the end).
- No evidence exists of this actually happening: the real run against all 110 target files (plus
  the 3 flagged-for-manual-review files) completed cleanly, printed its summary, and the script's
  own built-in self-verification (`flake8 --select=E402`) ran successfully afterward.

Recorded here as a known limitation for future readers of this script; **no follow-up ticket**.
If the script were ever promoted to a recurring/CI-invoked tool, this would need to be revisited
at that time — but that is a hypothetical future use, not a current gap.

## Missing Tests

None identified beyond this ticket's own scope. `tests/test_lint_pytestmark_e402.py` provides
permanent regression coverage for the defect this ticket fixes (E402 from `pytestmark` ordering
in `tests/`), and no other acceptance-relevant scenario was left uncovered — Step 3's repro
confirmed it was red before the fix and Step 4 confirmed it green after, and it runs on every
`make test` invocation going forward with no opt-in marker needed.

### Explicit timeout-marker compliance audit

No timeout-marker debt remains in the test files changed by this ticket. A bounded, exhaustive
static audit enumerated the tracked test modules in `git diff --name-only -- tests/`, asserted
that the set contains exactly **110** files, and checked every file for an explicit module-level
`pytestmark` containing `pytest.mark.timeout`. It separately checked the new regression module,
`tests/test_lint_pytestmark_e402.py`, for the same explicit marker. This is stronger than the
earlier 10-file value spot-check because every edited module is included and a count mismatch is
a hard failure.

Command (bounded to 60 seconds):

```sh
timeout 60 sh -c 'set -eu
files=$(git diff --name-only -- tests/ | sort)
count=$(printf "%s\n" "$files" | sed "/^$/d" | wc -l)
[ "$count" -eq 110 ]
missing=""
for file in $files; do
  if ! grep -Eq "^[[:space:]]*pytestmark[[:space:]]*=[[:space:]]*pytest\.mark\.timeout" "$file"; then
    missing="$missing $file"
  fi
done
[ -z "$missing" ] || { printf "missing module timeout marker:%s\n" "$missing"; exit 1; }
grep -Eq "^[[:space:]]*pytestmark[[:space:]]*=[[:space:]]*pytest\.mark\.timeout" tests/test_lint_pytestmark_e402.py
printf "PASS: 110/110 edited test modules and the new regression module have explicit module-level timeout markers\n"'
```

Result: exit 0 — `PASS: 110/110 edited test modules and the new regression module have explicit
module-level timeout markers`.

## Architecture Deviations

The implementation itself follows `20-architecture.md`: the 110 affected test modules use
imports first and then the module-level `pytestmark`; the bulk rewrite uses the designed
AST-located, line-slice approach; the permanent guard invokes flake8 with
`--jobs=1 --select=E402 tests/`; and no production module or Makefile lint scope changed.
The three files that the conservative detector skipped were handled manually as the design
required, rather than forcing an unsafe mechanical rewrite. Evidence is the zero-finding
`flake8 --jobs=1 --select=E402 tests/` result, the 110/110 timeout audit above, and the unchanged
`pypost/` diff recorded in Steps 4-6.

There was one workflow-sequencing deviation: `20-architecture.md` placed the
`doc/dev/testing.md` convention update alongside the implementation, but Step 4 deferred it to
the roadmap's Step 8 developer-documentation phase. Step 8 has now corrected the tracked
developer guide to show the imports-first shape and to explicitly reject `# noqa: E402`
suppression. This timing deviation did not alter the architecture or runtime behavior, and no
documentation gap remains in the repository-tracked guide.

## Hardcoded Constants

The relevant constants are intentional and do not create follow-up debt:

- **60 seconds** bounds the compliance-audit shell process. It is a verification safety ceiling,
  not application behavior; the completed audit took under one second.
- **30 seconds** is the regression module's explicit pytest timeout. It follows the documented
  pure-unit tier and provides substantial headroom for the measured ~1.9-second flake8 run.
- **20 seconds** bounds the flake8 subprocess inside that test, leaving the outer pytest timeout
  enough time to report a subprocess timeout cleanly. Both timeout choices were specified in the
  architecture and are named/documented at their use site.
- **10 findings** is the failure-message preview count. It bounds diagnostic output while still
  showing actionable file-and-line examples; the message also reports the number omitted. Making
  this configurable would add complexity without a current consumer or operational need.
- **Canonical spacing** (one blank line between the final import and `pytestmark`, then two blank
  lines before the next top-level statement) is deliberately encoded by the one-shot rewrite
  script. It matches the architecture's observed dominant clean-file shape and normal Python
  module-level spacing. It is a formatting invariant, not a runtime tuning value; flake8 and the
  targeted regression test provide the relevant enforcement evidence.

## Performance Concerns

`tests/test_lint_pytestmark_e402.py` shells out to `python -m flake8 --jobs=1 --select=E402
tests/` as a subprocess on every run, adding approximately **2 seconds** (~1.9s measured
consistently across Steps 3, 5, and 6) to the test suite's total runtime on every `make test`
invocation going forward, forever.

This is an **accepted, deliberate tradeoff**, not something to fix: the architecture doc's Step 3
design explicitly chose this subprocess-based full-directory scan (rather than, say, an
in-process AST check limited to changed files) because it is the simplest possible mechanism
that exactly matches what `make lint`'s flake8 invocation would report, has zero risk of drifting
out of sync with the real flake8 config, and needs no bespoke detection logic to maintain. ~2
seconds is a negligible fraction of the full suite's runtime (2338 collected tests) and is the
right trade for a permanent regression guard against a repo-wide style-convention regression
recurring silently.

## Follow-up Tasks

### NON-BLOCKER — pre-existing full-suite failures already tracked

The final `make check` run found three failures that reproduce unchanged at the task base
commit `75342cad`; they are unrelated to PYPOST-1070 and already have open Jira Debt issues:

- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  and `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  — [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111).
- `tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
  — [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110).

Reproduction command:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates \
  tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics \
  tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication -v
```

Baseline result: the same three assertions fail at `75342cad`. Verdict: **NON-BLOCKER —
pre-existing and already filed**. The current task gate is therefore baseline-relative: no
new failures beyond PYPOST-1110 and PYPOST-1111.

### NON-BLOCKER — pre-existing native segfault, unrelated to this ticket (candidate for new Jira ticket)

**What was found (Step 4)**: running all 110 changed `tests/*.py` files together in a single
`pytest` process crashed natively — a segfault in `pypost/ui/styles/style_manager.py:102`
(`apply_theme`, specifically its `app.setStyle(...)` / `QStyleFactory.create("Fusion")` calls),
triggered from different GUI test files across two separate attempts. This was investigated and
confirmed **pre-existing and unrelated to this ticket's changes**: it reproduces identically when
running the same full-batch command against the original, pre-fix file contents (verified via
`git stash push -- tests/` / `pop` to restore the exact pre-restructure files, then re-running the
same full-batch command). Every individual file, and every 8-way chunked batch (1384 tests total),
passes cleanly — only the single all-110-files-in-one-process run crashes.

**Is this already tracked?** Checked both plausible existing homes for this class of issue:

- `ai-tasks/PYPOST-968/60-tech-debt.md` TD-1 ("Diagnose intermittent post-PASS Qt teardown
  SIGSEGV") and its full investigation in `ai-tasks/PYPOST-1040/20-architecture.md` document a
  **related-class but distinct** crash: `SettingsDialog`'s nested `QLayout`/`QWidgetItem` widget
  tree becoming reachable only through CPython's deferred cyclic garbage collector, triggered
  specifically by pytest's `unraisableexception` plugin forcing 5 rounds of `gc.collect()` at
  *session end* — reproduced at 32.5% (13/40) on `tests/test_agent_dialog_settle_e2e.py` alone
  (just 2 tests, no other files in the process), root-caused via ablation to that specific
  widget/layout composition and that specific forced-GC mechanism, and already has a recommended
  follow-up ticket, [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) (8 points,
  Medium priority), for the mitigation attempt (no `ai-tasks/PYPOST-1115/` work has started yet).

- This ticket's segfault differs from that one in two concrete ways that matter for whether it's
  the same bug: **(1) different crash site** — `style_manager.py`'s `apply_theme` (application-
  wide `QStyle`/`QPalette` swapping via `app.setStyle()`/`QStyleFactory.create()`), not
  `SettingsDialog`'s `QLayout`/`QWidgetItem` tree; **(2) different trigger condition** — it only
  appeared when running a *large batch* (all 110 files, far more than PYPOST-1040's 2-test
  module) together in one process, not from pytest's session-end forced GC after a small, fixed
  set of tests. PYPOST-1040's ablation study was specific and rigorous for its own crash site,
  but was never run against `style_manager.py`/`apply_theme`, so it neither confirms nor rules
  out a shared root cause here.

**My assessment**: this looks like the **same broad class** of problem — native instability in
Shiboken/PySide6 object lifetime management under this repo's GUI-heavy pytest suite — but is
**not confirmed to be the same root cause** as PYPOST-1040/TD-1, and it was found under a
materially different condition (batch size/process accumulation vs. a fixed 2-test module's
session-end GC). Folding it into PYPOST-1115 (which is narrowly and specifically scoped to the
`SettingsDialog`/`QWidgetItem`/forced-GC mitigation PYPOST-1040 already root-caused) would blur
that ticket's scope with an unverified, differently-triggered symptom.

**Recommendation for Phase D**: file a **new** Jira Debt ticket (do not extend PYPOST-1040 or
PYPOST-1115), scoped to diagnosing GUI-test-process instability under large-batch/sustained
`QApplication` load — explicitly cross-referencing PYPOST-1040's investigation as related prior
art and methodology (its ablation approach, environment-inventory table, and ownership-boundary
analysis are directly reusable), and explicitly noting the open question of whether it shares
PYPOST-1040's root cause (deferred cyclic GC of Shiboken-wrapped Qt objects) or is a distinct
issue in `QStyle`/`QPalette` object lifetime under repeated `app.setStyle()` calls across many
tests in one process. Candidate practical mitigations already surfaced by this ticket's own Step
4 (not evaluated further here, out of this ticket's scope): `pytest-forked`/process isolation
per test file, or a bounded per-process GUI-test batch size in CI — both call out directly to
CI/test-infra ownership, not `pypost/` production code.

- **NON-BLOCKER — pre-existing, unrelated to this ticket.**
- Reproduction: `QT_QPA_PLATFORM=offscreen pytest <all 110 changed tests/*.py files> -m "not
  slow"` in one process (not reproduced by any individual file or 8-way chunked batch).
- Crash site: `pypost/ui/styles/style_manager.py:102` (`apply_theme`).
- Related: `ai-tasks/PYPOST-968/60-tech-debt.md` TD-1,
  `ai-tasks/PYPOST-1040/20-architecture.md`, recommended follow-up ticket
  [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — related class, not the same
  confirmed root cause.
- **Jira:** [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) — created in
  Phase D with 13 story points and Medium priority.
