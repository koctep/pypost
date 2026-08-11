# Roadmap: PYPOST-1007

## Suggested Branch Name

`fix/PYPOST-1007-mypy-baseline-line-churn` (reference only — work was committed directly on the
current branch per sprint-task-runner convention, no branch was created or switched).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mypy_baseline.py::TestMypyBaseline::test_gate_treats_line_shifted_error_as_unchanged`
    — builds a baseline via the real `--update-baseline` flow (current
    `_write_baseline`/`_load_baseline` shape), then re-runs the gate
    (`main()`) against mypy output for the identical `(path, code,
    message)` error shifted to a different line. Confirmed red against
    today's unmodified `scripts/check_mypy_baseline.py`: exit code 1, with
    stderr showing the phantom pair `New: ...:25:assignment` / `Resolved:
    ...:10:assignment` for what is the same logical error — demonstrates
    the `path:line:code` key's line-shift bug. No production code changed.
    Pending review subagent confirmation before marking `[x]`.
- [x] **STEP 4: Development**
  - [x] Rewrote `scripts/check_mypy_baseline.py`: `MypyError`/`BaselineEntry`
    NamedTuples, `_error_key` = `(path, code, message)`, `_diff_errors`
    extracted as a pure Counter-based multiset difference, `_load_baseline`
    rejects legacy (no `"version": 2`) files with a clear actionable error,
    `_write_baseline` emits v2 JSON with duplicates preserved, `main()`
    delegates formatting to `_format_new_report`/`_format_fixed_report`
    implementing the "which line to show" display spec. Step 3 red test
    (`test_gate_treats_line_shifted_error_as_unchanged`) now green.
  - [x] Updated `tests/test_mypy_baseline.py` for the new key/JSON shape:
    renamed/updated `test_parse_errors_extracts_path_line_code_and_message`,
    `test_baseline_entries_use_scoped_paths`,
    `test_baseline_scope_includes_core_models_and_ui`; added
    `test_diff_errors_ignores_line_shift_alone`,
    `test_diff_errors_detects_new_error_same_line`,
    `test_diff_errors_detects_fixed_error`,
    `test_diff_errors_multiset_partial_fix`,
    `test_diff_errors_multiset_new_duplicate`,
    `test_diff_errors_multiset_full_fix`,
    `test_load_baseline_rejects_legacy_flat_string_format`,
    `test_write_baseline_round_trip`,
    `test_write_baseline_preserves_duplicate_entries`. All pure-unit,
    `pytest.mark.timeout(30)` via module `pytestmark`.
  - [x] Regenerated `mypy-baseline.json` via `--update-baseline` against
    the live mypy run — v2 shape, real current error set.
  - [x] `PYTEST_ARGS="tests/test_mypy_baseline.py -v" make test` green;
    `make lint` clean for the changed files.
- [x] **STEP 5: Code Cleanup**
  - [x] Manually ran flake8 on `scripts/check_mypy_baseline.py` and
    `tests/test_mypy_baseline.py` (not covered by `make lint`, which is
    scoped to `pypost/`) — clean except 7 expected `T201` (print) hits on
    the CLI script's intentional stdout/stderr output, left unsuppressed
    per project convention. No unused imports/vars, no >100-char lines,
    no commented-out code, no dead code, no merge-conflict markers found.
  - [x] `PYTEST_ARGS="tests/test_mypy_baseline.py -v" make test`: 14 passed
    in 0.02s; all covered by module-level `pytestmark =
    pytest.mark.timeout(30)`.
  - [x] Created `ai-tasks/PYPOST-1007/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - [x] Assessed applicability: `scripts/check_mypy_baseline.py` is a synchronous, one-shot
    CLI gate script with no background process, no request/response cycle, and no state beyond
    `mypy-baseline.json`. Structured `logging`/metrics were determined not applicable —
    confirmed against strong local precedent (`ai-tasks/PYPOST-816`, `-815`, `-572`, `-931`,
    `-734`, `-735`) for CI-gate/tooling scripts under `scripts/`, all of which documented the
    same N/A decision with existing print/exit-code output as the observability surface.
    Contrasted with the two `scripts/` entries that do use `logging`
    (`encryption_migrate.py`, `generate_mcp_test_fixtures.py`) — both multi-step mutating
    "operator CLI" tools, unlike this single-pass gate.
  - [x] No code changes made; existing `print()` calls in `main()` already distinguish
    config/setup errors (missing/malformed baseline) from genuine new-error gate failures via
    distinct message text and exit code 1 — no synthetic logging levels would add information.
  - [x] Created `ai-tasks/PYPOST-1007/50-observability.md` documenting the analysis and
    decision honestly (N/A sections marked with one-line justifications, not left empty).
- [x] **STEP 7: Review and Technical Debt**
  - [x] Created `ai-tasks/PYPOST-1007/60-tech-debt.md`: honest analysis of shortcuts
    (whole-baseline regeneration in one commit — documented as a deliberate,
    architecturally-justified decision with its one real cost, an un-reviewable bulk diff, not
    hidden; legacy-format hard-rejection with no dual-read path; pre-existing `_ERROR_RE`/
    `MYPY_PATHS` duplication), missing tests (`_format_new_report`/`_format_fixed_report` have
    zero direct unit coverage; no empty-baseline/zero-current-errors test; legacy-rejection
    message content only substring-checked), a **BLOCKER CHECK** on explicit pytest timeout
    markers (verified directly: module-level `pytest.mark.timeout(30)` on all 14 tests in
    `tests/test_mypy_baseline.py`, confirmed by fresh green run — 14 passed in 0.02s — and by
    `tests/conftest.py`'s independent collection-time enforcement; **no blocker**), a
    line-by-line architecture comparison (one minor beneficial deviation: report formatting
    factored into named `_format_new_report`/`_format_fixed_report` functions rather than left
    inline in `main()`; everything else matches `20-architecture.md` exactly), and hardcoded
    values review (`BASELINE_VERSION = 2` and `MYPY_PATHS` are legitimate; `_ERROR_RE`'s path
    alternation duplicates `MYPY_PATHS` as a pre-existing, newly-flagged latent trap). Three
    conservative follow-up items recorded (formatting-function tests, empty-baseline test,
    derive `_ERROR_RE` from `MYPY_PATHS`) — none rise to blocker status.
  - [x] Checked `doc/dev/` for gate-relevant docs needing an update: `doc/dev/static_type_checking.md`
    exists and documents this exact gate, but still describes the **pre-PYPOST-1007** key format
    (`"Parse errors into stable keys (pypost/core/foo.py:42:arg-type)"`, `"Frozen path:line:
    error-code signatures (218 as of PYPOST-815)"`) — now stale after this task's `(path, code,
    message)` key/v2-JSON change. Deferred to STEP 8 (Dev Docs), whose artifact is `doc/dev/`;
    not fixed in this step per the roadmap's step boundaries. No user-facing `doc/` (top-level)
    content references the mypy gate at all — confirmed via repo-wide grep — so no user-facing
    documentation update is needed, consistent with this being a purely internal dev-tooling
    change.
  - [x] Verdict: **SAFE TO CLOSE** (see `60-tech-debt.md` → Verdict). Per task instruction,
    proceeded autonomously without waiting for user review/approval.
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/static_type_checking.md`: replaced the stale `path:line:error-code`
    key description and "218 as of PYPOST-815" baseline count with the current `(path, code,
    message)` key, `"version": 2` JSON shape, and 219-error count (per live
    `mypy-baseline.json`). Added the line-shift rationale (PYPOST-987's ~30 phantom pairs) and
    the Counter-based multiset-diff rationale (~52% duplicate-key rate) to the "Baseline gate
    behavior" list, plus a note on legacy-format hard-rejection. Left the historical per-code
    triage tables (PYPOST-734/813/814/815) with a caveat pointing at the live JSON for exact
    current counts, since re-deriving every table cell is out of this step's scope. Repo-wide
    grep for `218`/`mypy-baseline`/`path:line:code` under `doc/` found no other stale
    references.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (existing gate script, no new language/stack).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1007/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1007/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1007/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1007/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1007/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
