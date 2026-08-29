# Roadmap: PYPOST-1041

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1041/10-requirements.md`
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1041/20-architecture.md`
  - AST strengthening design: AST inspection helper for `__all__` in `tree_index.py`,
    ownership assertions for `find_child_index_by_display_text` (delegation to `display_role_equals`,
    prohibition of inline `DisplayRole`), module export verification, diagnostic failure reporting,
    and Step 3 repro plan.
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_display_role_scan_ownership_repro.py`
  - Automated red repro tests created: 5 failing tests demonstrating lack of delegation check, lack of inline DisplayRole prohibition, lack of __all__ export validation, and mutant pass-through in `tests/test_display_role_scan_ownership.py`.
  - Documented in `ai-tasks/PYPOST-1041/25-failing-repro.md`.
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Iteration 1 — Strengthened `tests/test_display_role_scan_ownership.py`: added the
    `_module_all_exports` AST helper, asserted `find_child_index_by_display_text` calls
    `display_role_equals`, asserted it never references `ItemDataRole.DisplayRole` inline, and
    asserted `pypost.agent.tree_index.__all__` exports all three helpers, each with the
    diagnostic message specified in `20-architecture.md`. No production change was required:
    `pypost/agent/tree_index.py` already declares a conforming `__all__` and already delegates
    matching to `display_role_equals`.
  - [x] Iteration 2 — Applied the Step 3 review advisories to
    `tests/test_display_role_scan_ownership_repro.py`: gave the inline-DisplayRole mutant a
    compliant `__all__` so it isolates a single contract violation, switched the empty-exports
    mutant to a plain `__all__ = []` assignment (visible to an `ast.Assign`-only helper), tied
    `_has_all_exports_check` to the `_module_all_exports` helper name, and wrapped four lines
    over the `.flake8` 100-character limit.
  - [x] Iteration 3 — Verification. Targeted run
    (`make test PYTEST_ARGS="tests/test_display_role_scan_ownership_repro.py
    tests/test_display_role_scan_ownership.py"`) is green: 2/2 files, 6/6 tests. Full `make test`
    reports 304 files, 295 passed, 8 failed, 1 skipped; all 8 failures were triaged against base
    commit `253403db` in a throwaway `/tmp` worktree and classified NON-BLOCKER — pre-existing.
    None involve `tree_index.py`, `ui_actions.py`, or the ownership suites.
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1041/40-code-cleanup.md`
  - [x] `tests/test_display_role_scan_ownership.py` — `_module_all_exports` now iterates
    `ast.iter_child_nodes` instead of `getattr(tree, "body", [])` and documents its empty-set
    fallback; `test_flat_and_tree_share_display_role_match_helper` docstring now enumerates
    AC-1..AC-4 instead of AC-1 only. No assertion, message, or behaviour changed.
  - [x] `tests/test_display_role_scan_ownership_repro.py` — duplication removed: the two
    near-identical mutant module sources are generated from one `_MUTANT_TREE_INDEX_TEMPLATE`
    (mutants now mirror the real `tree_index.py` signatures and each varies exactly one axis);
    extracted `_calls_to`, `_refers_to_find_child`, and `_patch_tree_index_source`; deleted the
    redundant `_calls_helper`; renamed `target_mod` → `ownership_suite` and `mock_parse` →
    `fake_parse`; module docstring corrected from 4 gaps to the actual 5; PEP 257 docstring
    fixes; 2 lines rewrapped to the `.flake8` 100-character limit.
  - [x] Refactor safety re-verified: all three `_has_*_check` repro helpers still return `False`
    against the base-commit `253403db` ownership suite and `True` against the current one, so the
    Step 3 red-then-green property survives the cleanup.
  - [x] Verification — `make lint` clean;
    `make test PYTEST_ARGS="tests/test_display_role_scan_ownership_repro.py
    tests/test_display_role_scan_ownership.py"` green (2 files, 6/6 tests). Full `make test` not
    re-run (known Qt worker segfault + 110 MB core dump); Step 4 iteration 3 holds the triage.
  - Deliberately not deduplicated: the repeated `_calls_name` / `_has_display_role_attr`
    assertion pairs in the ownership suite are load-bearing — folding them behind a helper
    renames the first argument and silently defeats the repro's mutation guard.
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1041/50-observability.md`
  - [x] No production logging or metrics added, and none applicable: the task diff is test-only
    (`tests/test_display_role_scan_ownership.py`, `tests/test_display_role_scan_ownership_repro.py`),
    no new runtime path exists, `10-requirements.md` lists `ui_select` logging/metric changes under
    Non-Goals, and per-row logging inside `find_child_index_by_display_text` would print user
    DisplayRole strings once per model row. Reasoning recorded in `50-observability.md`.
  - [x] Assessed the diff's actual observability surface — the CI-log diagnostics of the ownership
    assertions. All 8 violation scenarios (inline DisplayRole, delegate-but-also-inline, empty
    `__all__`, partial `__all__`, non-literal `__all__`, flat finder deleted, tree finder renamed,
    `_select_item_view` renamed) were driven through the suite and their `AssertionError` text
    captured verbatim into a table in `50-observability.md` (9 mutants: the non-literal `__all__`
    scenario was driven in both its dynamic and its annotated spelling). Verdict: the four
    assertions this task added or rewrote are self-describing (symbol + remedy, and
    expected-vs-found for `__all__`); two pre-existing ones are not.
  - [x] Five findings recorded, none blocking, all carried to Step 7: OBS-1 fail-fast single test
    function reports one violation per CI run; OBS-2 pre-existing `missing
    find_tree_index_by_display_text` / `missing _select_item_view` name neither module nor remedy;
    OBS-3 no diagnostic prints a file path (4 of 14 assertions name the dotted module, 8 name only
    a function); OBS-4 message wording is pinned by the repro's `pytest.raises(match=...)` regexes;
    OBS-5 a non-literal `__all__` — computed *or* annotated `__all__: list[str] = [...]`, which
    `_module_all_exports` skips as an `ast.AnnAssign` — is reported as `found []`.
  - [x] No code change made in Step 6 — the skill does not call for one in a test-only diff, OBS-2
    touches assertions outside this ticket's scope (AC-4 freezes their intent, not their wording,
    so the deferral rests on the AGENTS.md scope rule), and OBS-1 cannot be split without breaking
    the Step 3 repro, which calls `test_flat_and_tree_share_display_role_match_helper()` by name.
  - [x] Bounded execution reconfirmed (`20-architecture.md` Phase 4): both test modules declare
    `pytestmark = pytest.mark.timeout(10)`.
  - [x] Verification — `make lint` clean;
    `make test PYTEST_ARGS="tests/test_display_role_scan_ownership_repro.py
    tests/test_display_role_scan_ownership.py"` green (2 files, 6/6 tests, 1.18 s). Full `make test`
    not re-run (known Qt worker segfault + 110 MB core dump); Step 4 iteration 3 holds the triage.
  - Step 6 acceptance gate passed (review verdict PASS after one fix loop)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1041/60-tech-debt.md`
  - [x] No code change in Step 7 — the diff stays test-only and byte-identical:
    `tests/test_display_role_scan_ownership.py` 1 file, 55 insertions / 3 deletions, plus the
    untracked `tests/test_display_role_scan_ownership_repro.py`.
  - [x] Upstream findings carried forward and de-duplicated rather than re-derived: OBS-1 → TD-2,
    OBS-2 → TD-6, OBS-3 → TD-7, OBS-4 → TD-9, OBS-5 → TD-1, and the `40-code-cleanup.md`
    "load-bearing repetition" note → TD-5. A mapping table heads the artifact.
  - [x] Two new findings from a fresh audit of the delivered guard, both proven with a throwaway
    in-memory AST probe (no repo file written): TD-3 — either flat-finder assertion can be moved
    into an uncalled helper, and the AC-4 `find_tree` pair can be deleted outright, with all five
    repro tests still green (the inline mutant violates AC-1 and AC-2 at once and test 4's regex
    accepts either message); TD-4 — `_refers_to_find_child`'s `"child" in arg.id.lower()`
    heuristic goes green for a loop that never inspects `find_child`.
  - [x] TD-1 (OBS-5) re-verified and given its patch: `_module_all_exports` matches `ast.Assign`
    only, so an annotated `__all__: list[str] = [...]` or a computed `__all__ = list(_PUBLIC)`
    reports `found []`. Still unreachable at this commit — 49 module-level `__all__` under
    `pypost/`, all plain literal `ast.Assign`, 0 `ast.AnnAssign`, 0 `ast.AugAssign` — and one
    token from reachable.
  - [x] Nine findings recorded, none blocking: six ticket candidates (TD-3 Medium; TD-1, TD-2
    Low-Medium; TD-4, TD-5, TD-6 Low), three recorded-only (TD-7 and TD-8 cosmetic, TD-9
    informational and owned by this task's Step 8).
  - [x] TD-8 records the Step 6 re-review wording nit — `50-observability.md` says "all 8 distinct
    messages" where rows 3 and 5 emit byte-identical text (8 scenarios, 7 distinct strings). Not
    corrected in place: `50-observability.md` is an accepted Step 6 artifact and editing it would
    re-open STEP 6 per `td-roadmap`.
  - [x] Step 4's eight pre-existing full-suite failures (base `253403db`) recorded under Follow-up
    Tasks as `NON-BLOCKER — pre-existing` with their existing keys — PYPOST-1231, PYPOST-1232,
    PYPOST-1233, PYPOST-1234, PYPOST-1111 (×2, commented), PYPOST-1117 (×2, epic; children
    PYPOST-1212/1213/1214). No new issues created for them.
  - [x] Timeout-marker blocker check PASS — both modules declare
    `pytestmark = pytest.mark.timeout(10)`.
  - [x] Verification — `make lint` clean (flake8 on `pypost/`, Markdown lint 16 files, link check
    18 files). Full `make test` deliberately not run (known Qt worker segfault + ~110 MB core
    dump); Step 4 iteration 3 holds the triage.
  - Step 7 acceptance gate passed (review verdict PASS; TD-3 independently confirmed real)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/ui_actions.md` — new `#### DisplayRole ownership boundary and its guard
    (PYPOST-1041)` subsection under `ui_select`: the four-part rule (`display_role_equals` owns
    the `Qt.ItemDataRole.DisplayRole` read; both finders delegate; `_select_item_view` delegates
    to the flat finder; `__all__` names all three helpers), how it is enforced
    (`tests/test_display_role_scan_ownership.py`, `ast.parse` only, one fail-fast test, module
    `pytestmark = pytest.mark.timeout(10)`, the four AST helpers), and where the guard-of-the-guard
    lives (`tests/test_display_role_scan_ownership_repro.py` — 3 AST presence checks + 2 mutants).
  - [x] Same subsection records the two editing constraints: **TD-9** — the diagnostic wording is a
    machine-checked contract pinned by the repro's `pytest.raises(match=...)` regexes (reword both
    files together; keep the function and helper names on one line; keep `__all__` before
    `export`); **TD-5** — none of the three `_calls_name` / `_has_display_role_attr` assertion
    pairs may be folded into a loop or a shared helper. Corrected reason: `_refers_to_find_child`
    accepts a first argument that is either an `ast.Name` whose lowercased id contains `child`
    *or* any expression whose `ast.dump` contains `find_child_index_by_display_text`, so only the
    `find_child` pair is recognised — folding it turns the repro red, while folding the
    `find_tree` or `_select_item_view` pairs is lost silently (TD-3).
  - [x] `doc/dev/ui_actions.md` cross-links and troubleshooting: the existing "Shared DisplayRole
    matching (PYPOST-971)" paragraph now points at the new subsection; the Architecture table row
    for `tree_index.py` notes the PYPOST-1041 ownership AST guard; two Troubleshooting entries
    added — `__all__ must export [...]; found []` (TD-1: keep the plain literal `__all__`) and
    "repro fails but the ownership suite passes" (restore the assertion shape, do not relax the
    repro).
  - [x] `doc/dev/testing.md` — the DisplayRole ownership AST marker paragraph now records what
    PYPOST-1041 added, names the repro as the guard of the guard, and links to the new
    `ui_actions.md` subsection.
  - [x] `doc/dev/README.md` — Testing and quality TOC entry
    "DisplayRole ownership boundary and its guard (PYPOST-971 / PYPOST-1041)" pointing at the new
    anchor. The anchor was checked **manually**, not by the repo gate: `make lint` runs
    `scripts/check_user_docs_links.py` with no arguments, and its `_DEFAULT_TARGETS` cover
    `doc/user/*.md`, `doc/README.md`, root `README.md`, and `examples/README.md` only — `doc/dev/`
    is outside that set. Manual check performed by calling
    `check_user_docs_links.extract_anchors(doc/dev/ui_actions.md)` directly and confirming it
    contains `displayrole-ownership-boundary-and-its-guard-pypost-1041`, which is also what
    `slugify` returns for the new heading.
  - [x] Link wrapping left as-is (reviewer non-blocking note). The new cross-links and the TOC
    entry wrap between `](` and the destination or inside the link text, so the checker's
    line-by-line `finditer` cannot match them — but a one-line form buys nothing here, because
    `doc/dev/` is not in the checker's default target set at all, and the one-line TOC entry
    would be 148 characters against a 100-character Markdown rule
    (`scripts/lint_user_docs.py`) and a 130-character longest line in `doc/dev/README.md`.
    The wrapped `](\n   dest)` form already exists in that file (the "jira-mcp example fixtures"
    entry), so the new entry matches the local convention.
  - [x] No new doc file created: `20-architecture.md` names `doc/dev/ui_actions.md` as the Step 8
    target and that file already owns the DisplayRole matching contract, so the existing sections
    were extended rather than duplicated.
  - [x] Fix loop 1 — Step 8 review returned FAIL with four accuracy gaps; all four corrected in
    `doc/dev/ui_actions.md` and `doc/dev/testing.md`, each re-verified against the real code
    before editing (no reviewer wording pasted):
    - **Gap 1 (Guard of the guard).** The claim "deleting an ownership assertion turns the repro
      red" was false and contradicted this task's own TD-3. Replaced with what the repro actually
      pins — the two `find_child` assertions plus the `__all__` subset assertion — and an explicit
      TD-3 limitation linking
      [PYPOST-1236](https://pypost.atlassian.net/browse/PYPOST-1236). Proven by a sandboxed
      per-assertion deletion sweep (repo files untouched; copies under the session scratchpad):
      **11 of the 14 assertions are unguarded**, not the ~8 the reviewer estimated. Only
      assertions 5, 6, and 7 turn the repro red; deleting the `find_tree` pair together with all
      three `_select_item_view` assertions leaves all five repro tests passing.
    - **Gap 2 (TD-5 bullet + the mirrored `testing.md` sentence).** Only the `find_child` pair is
      recognised by the repro. Kept the practical "do not fold into a helper or loop" advice —
      re-proven by actually folding that pair into an `_assert_delegates` helper in the sandbox,
      which turns repro tests 1 and 2 red — but corrected the reason and split the bullet so the
      `find_tree` / `_select_item_view` pairs are marked as silently unguarded.
    - **Gap 3.** Documented the second branch of `_refers_to_find_child`
      (`"find_child_index_by_display_text" in ast.dump(arg)`), so an inline lookup expression is
      named as accepted alongside the `ast.Name` spelling.
    - **Gap 4.** (a) Scoped the `display_role_equals` sole-reader claim to `pypost/agent` and
      named the out-of-scope readers (`pypost/ui/delegates/environment_name_delegate.py:39,50`,
      `pypost/ui/widgets/websocket/stream_view.py:199`,
      `pypost/ui/widgets/websocket/stream_model.py:68,75`) plus the guard's two-file parse scope.
      (b) Corrected the import claim: the `find_child_index_by_display_text` import is
      module-level in `ui_actions.py` (lines 27-29) and `_imports_from_tree_index` is called with
      the whole module AST, so it pins the module's import edge, not an import inside
      `_select_item_view`.
  - [x] Verification — `make lint` clean. Full `make test` deliberately not run (known Qt worker
    segfault + ~110 MB core dump); Step 4 iteration 3 holds the triage. Docs-only step: the tests
    diff is unchanged (`tests/test_display_role_scan_ownership.py` 1 file, 55 insertions /
    3 deletions, plus the untracked repro).
  - Step 8 acceptance gate passed (review verdict PASS after one fix loop)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1041/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1041/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_display_role_scan_ownership_repro.py`
- `ai-tasks/PYPOST-1041/25-failing-repro.md`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1041/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1041/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1041/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
