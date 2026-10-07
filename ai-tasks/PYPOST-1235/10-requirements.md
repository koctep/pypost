# PYPOST-1235: Teach `_module_all_exports` the annotated `__all__` spelling

## Goals

The DisplayRole ownership suite (`tests/test_display_role_scan_ownership.py`) guards that
`pypost.agent.tree_index` keeps its three public lookup helpers exported through `__all__`. It
reads that manifest statically, with the helper `_module_all_exports`, which today recognises
only the plain `__all__ = [...]` spelling.

Two cases go wrong:

1. **False red on a correct module.** A behaviour-preserving typing edit, such as
   `__all__: list[str] = [...]`, makes the guard fail even though every required name is still
   exported. An annotated `__all__` is a common typing-hygiene idiom. Today `make typecheck`
   does not push for it here: its mypy scope (`MYPY_PATHS` in `scripts/check_mypy_baseline.py`)
   is `pypost/core`, `pypost/models` and `pypost/ui`, so `pypost/agent/tree_index.py` and
   `tests/` are outside it. A future widening of that scope would invite exactly this edit.
2. **Misleading diagnostic.** The failure reads
   `pypost.agent.tree_index.__all__ must export [...]; found []`. A maintainer reads that as "the
   manifest is empty" and looks for the wrong defect, when the real cause is "the guard cannot
   read this spelling".

Business value: maintainers can make normal typing edits without a false CI failure, and when the
guard does fail, its message names the real cause. That cuts wasted CI round trips and
misdiagnosis time.

Origin: PYPOST-1041 Step 7, TD-1 (carried from OBS-5), in
`ai-tasks/PYPOST-1041/60-tech-debt.md`.

## User Stories

- **US-1:** As a maintainer, I can annotate `tree_index.__all__` with a type
  (`__all__: list[str] = [...]` or a tuple equivalent) without the ownership suite failing,
  provided the required names are still listed.
- **US-2:** As a maintainer reading a red ownership run, I can tell from the failure message
  whether `__all__` is really missing required names, or whether the suite could not read a
  literal manifest at all (absent, bare annotation, or computed value).
- **US-3:** As a reviewer of PYPOST-1041, I can rely on the already-reviewed red-then-green repro
  (`tests/test_display_role_scan_ownership_repro.py`) and the discoverability audit staying
  valid and green without being edited.

## Definition of Done

Here, "manifest spellings" means module-level `__all__` statements in the module the suite
parses as `tree_index`.

- **AC-1 (plain literal, no regression):** `__all__ = [...]` and `__all__ = (...)` with string
  literals are read as exactly those names. The ownership test passes against the real
  `pypost/agent/tree_index.py`.
- **AC-2 (annotated literal):** `__all__: list[str] = [...]` (and an annotated tuple literal) is
  read as exactly the listed names. The ownership test passes when `tree_index` uses this spelling
  with the three required names. It fails, with the "missing names" diagnostic, when a required
  name is absent.
- **AC-3 (bare annotation):** `__all__: list[str]` with no value does not raise any error other
  than the ownership `AssertionError`. It is treated as "no statically readable manifest".
- **AC-4 (computed value):** `__all__ = list(_PUBLIC)`, or any other non-literal value, does not
  raise any error other than the ownership `AssertionError`. It is treated as "no statically
  readable manifest".
- **AC-5 (distinguishable diagnostic):** When the ownership test fails because no statically
  readable literal `__all__` was found (absent, bare annotation, or computed), the message says
  so: it names `__all__` and states that no readable literal manifest was found or the spelling
  is unsupported. It must not show the outcome as `found []`. When a literal manifest is present
  but lacks required names, including the literal empty `__all__ = []`, the message keeps the
  current form: it names the required exports and lists what was found. Both kinds of failure
  stay single-line `AssertionError`s raised by
  `test_flat_and_tree_share_display_role_match_helper`.
- **AC-6 (unit coverage of spellings):** One or more new tests run the manifest reader on all
  four spellings: plain literal, annotated literal, computed, and bare annotation. They also cover
  the literal empty manifest and the absent manifest, and assert the outcome required by
  AC-1 to AC-5 for each. Every new test has a timeout marker, directly or through `pytestmark`.
- **AC-7 (end-to-end red repro):** At least one test swaps in the annotated-literal spelling of
  `tree_index` through the suite's source-substitution seam (the existing
  `_patch_tree_index_source` pattern) and shows that the ownership test passes. That test is
  red before the fix and green after it (Step 3 / Step 4 evidence).
- **AC-8 (coupling preserved, unedited guards stay green):**
  - The manifest reader is still named `_module_all_exports` and is still called from the
    ownership suite.
  - The suite still contains a literal collection naming `display_role_equals` and
    `find_child_index_by_display_text`, so `_has_all_exports_check` is still true.
  - `test_flat_and_tree_share_display_role_match_helper` keeps its name and is still callable
    with no arguments.
  - The empty-manifest mutant still fails with a message matching `__all__.*export` (repro test
    `test_repro_ownership_suite_catches_empty_all_exports_mutant`), and the inlined-DisplayRole
    mutant still fails as before.
  - `tests/test_display_role_scan_ownership_repro.py`,
    `tests/test_display_role_scan_ownership_independent_repro.py`,
    `tests/test_display_role_scan_ownership_aggregate_repro.py` and
    `tests/test_display_role_scan_ownership_discoverability.py` pass without modification. This
    includes the discoverability region markers `def _assert_flat_shared_ownership`,
    `def _assert_tree_shared_ownership` and
    `def test_flat_and_tree_share_display_role_match_helper`.
- **AC-9 (no production change):** No file under `pypost/` is modified, and
  `pypost/agent/tree_index.py` keeps its current plain-literal `__all__`.
- **AC-10 (quality gates and docs):** `make check` passes. `make typecheck` reporting no new
  errors against the baseline is a no-regression sanity check only: the changed files are
  outside its mypy scope, so it cannot fail because of this task. Developer docs that currently say the annotated spelling is
  skipped (`doc/dev/ui_actions.md`, troubleshooting entry "Ownership suite fails with
  `__all__ must export [...]; found []`", and the `_module_all_exports` description in the
  Enforcement paragraph) describe the new behaviour.

## Task Description

### Problem

`_module_all_exports(tree) -> set[str]` (`tests/test_display_role_scan_ownership.py:64-82`)
looks at module-level statements only, and only when the statement is a plain assignment whose
value is a list or tuple literal. It returns an empty set in every other case: an annotated
assignment, a bare annotation, a computed value, or no `__all__` at all. Its only caller (in
`test_flat_and_tree_share_display_role_match_helper`) checks that the three required names are a
subset of the result. It cannot tell an empty set that means "manifest empty" from one that means
"manifest unreadable".

### Reachability (re-verified at HEAD `5e8a9010`)

An AST census of `pypost/**/*.py` (285 files) found 57 module-level `__all__` declarations. All
are plain list-literal assignments. There are 0 annotated assignments, 0 augmented assignments
(`+=`) and 0 `__all__.<method>()` calls. The defect is therefore latent, not live, but it is one
token away from being reachable. The Jira description quotes 261 files and 49 declarations from
commit `253403db`; the conclusion is the same.

### Main entities (business view)

- **Export manifest:** the module's declared public names (`__all__`).
- **Manifest spelling:** plain literal, annotated literal, bare annotation, computed value, or
  absent.
- **Manifest reader:** `_module_all_exports`, the static reader the ownership suite uses.
- **Ownership contract:** `test_flat_and_tree_share_display_role_match_helper` and its
  diagnostics.
- **Repro guard:** the PYPOST-1041 meta-tests that check the contract's shape by name and AST
  pattern (`_has_all_exports_check` and the mutant tests). They must not be edited.

### Scope

In scope:

- The manifest reader's recognition of the annotated literal spelling.
- Safe handling of the bare annotation and computed spellings.
- The ownership diagnostic that tells "unreadable or absent" apart from "missing names".
- Unit and repro tests for these behaviours.
- Updating the dev-doc text that describes the reader's limitation.

Out of scope / non-goals:

- Any change under `pypost/`, including respelling `tree_index.__all__`.
- Evaluating computed manifests, or following `__all__ += [...]`, `__all__.extend(...)`,
  conditional or star-import manifests. These stay "not statically readable" (TD-1 "accepted, not
  fixed").
- Defining which of several module-level `__all__` statements wins, beyond keeping current
  behaviour for a single declaration (none exist in `pypost/` today).
- Splitting the fail-fast ownership test (TD-2), and the repro substring heuristic (TD-4).
- Changes to the PYPOST-1041 repro or discoverability tests.

### Non-functional requirements

- **NFR-1:** The ownership suite stays static. It never imports the modules under test and needs
  no Qt app or display.
- **NFR-2:** No measurable change in suite runtime; existing timeouts (`timeout(10)`) are kept.
- **NFR-3:** Diagnostics stay single-line and name the owner (`pypost.agent.tree_index.__all__`).
- **NFR-4:** All verification runs only through `make` targets (`AGENTS.md`).

### Constraints and assumptions

- Implementation language: Python (test code only).
- The repro guard matches the helper name `_module_all_exports` exactly, and repro tests 4-5
  invoke the ownership test by name. Any return-shape change must keep these contracts true
  (AC-8).
- Today the ownership file is the helper's only caller (`grep` over `tests/` and `doc/`). The
  repro guard `tests/test_display_role_scan_ownership_repro.py` also references the helper by
  name, in `_has_all_exports_check` (`_calls_to(tree, "_module_all_exports")`) and its docstring.
  That by-name coupling is what AC-8 protects.

## Q&A

- **Q1 (open, for Step 2):** How should the reader signal "no statically readable manifest" so
  that the caller can produce the AC-5 diagnostic? Options include a distinct sentinel or optional
  return (for example `set[str] | None`), a separate predicate, or a richer result. Step 1 fixes
  only the observable outcome (AC-5) and the coupling limits (AC-8). The mechanism is an
  architecture decision.
- **Q2:** Should a computed `__all__` be treated the same as an absent one?
  **A:** Yes for this task. Both count as "no statically readable literal manifest" (AC-4, AC-5).
  Evaluating computed values is out of scope.
- **Q3:** Must a bare annotation followed later by a literal assignment
  (`__all__: list[str]` then `__all__ = [...]`) be read?
  **A:** It is not required by any AC. Step 2 may choose to support it, and if it does, it should
  be covered by a test. The required minimum is that a bare annotation on its own never raises
  (AC-3).
- **Q4:** Why not simply widen the `isinstance` check?
  **A:** Recorded in TD-1. An annotated assignment exposes a single target and may have no value,
  so a one-token widening raises on the bare form. AC-3 makes "never raises" a requirement. How
  to meet it is left to Step 2.
- **References:** Jira PYPOST-1235; `ai-tasks/PYPOST-1041/60-tech-debt.md` (TD-1);
  `ai-tasks/PYPOST-1041/50-observability.md` (OBS-5); `doc/dev/ui_actions.md` (Enforcement
  paragraph and troubleshooting entry).
