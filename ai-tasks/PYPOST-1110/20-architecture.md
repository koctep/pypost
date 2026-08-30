# PYPOST-1110: Migrate test_mcp_controls_presenter.py off its local qapp() fixture onto shared conftest qapp

## Research

- **Guard test**: `tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
  (lines 132-159) does a suite-wide AST inventory over every `tests/test_*.py` module, flagging any
  module that (a) defines a local `def qapp():` fixture, (b) defines a `_get_app()` lazy-QApplication
  helper, or (c) has a `TestCase` subclass whose `setUpClass` constructs a `QApplication`. It is the
  authoritative acceptance check for this ticket's Definition of Done.
- **Shared fixture**: `tests/conftest.py` defines the single suite-wide fixture at module scope
  (~line 29-35):

  ```python
  @pytest.fixture(scope="module")
  def qapp():
      """Shared QApplication for Qt widget tests (module-scoped singleton)."""
      from PySide6.QtWidgets import QApplication
      app = QApplication.instance() or QApplication([])
      yield app
  ```

  Every Qt-based test module is expected to take `qapp` as a normal pytest fixture parameter rather
  than defining its own.
- **Precedent**: `tests/test_presenter_font_inheritance.py` was the pattern the ticket originally
  cited as the model to follow — it imports no `sys`/`QApplication`, defines no local `qapp()`, and
  its test functions simply accept `qapp` as a fixture argument (confirmed by reading its header,
  lines 1-19).
- **Target-file discovery (the key finding of this step)**: Reading
  `tests/test_mcp_controls_presenter.py` on `dev` HEAD (current head `f3dc3184`) shows it already
  matches the `test_presenter_font_inheritance.py` precedent exactly: no local `qapp()` fixture, no
  `sys` import, no `QApplication` import; `test_mcp_controls_presenter_widgets_and_initial_state`
  and other tests take `qapp` as a fixture parameter resolved from `tests/conftest.py`.
  `git show 494eb857 -- tests/test_mcp_controls_presenter.py` confirms commit `494eb857`
  ("fix(tests): PYPOST-1176 restore green test suite on dev") already performed this exact
  mechanical migration for this file, as part of an unrelated, broader test-suite-greening task.
  This was independently established during this task's own Step 1 (`10-requirements.md`) and is
  treated here as an already-verified fact, not re-derived.
- Net effect: the module/component this ticket targets (`tests/test_mcp_controls_presenter.py`)
  requires no further change. The remaining architectural question for Step 2 is how to verify and
  document that fact, not how to redesign anything.

## Implementation Plan

No further code change to `tests/test_mcp_controls_presenter.py` is needed — its content on `dev`
HEAD already satisfies the Definition of Done. Accordingly, the "architecture" for this ticket is a
**verification architecture** rather than a code-change architecture, consisting of four steps:

1. **Confirm current state of the target file** — re-read
   `tests/test_mcp_controls_presenter.py` on the current `dev` HEAD and confirm (via direct
   inspection, not memory) that it has no local `qapp()` fixture and no `sys`/`QApplication`
   imports. (Done in Research above; head was `f3dc3184` at verification time.)
2. **Run the guard test node id** —
   `PYTEST_ARGS="tests/test_suite_qapp_alignment.py -v" make test` and confirm
   `test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication` passes (it enumerates the
   whole suite, so a pass here directly proves the ticket's business requirement).
3. **Run the full related test files to ensure no regression** — run
   `tests/test_mcp_controls_presenter.py` and `tests/test_presenter_font_inheritance.py` (the
   target file plus its cited precedent) alongside the guard test in one batch, to confirm the
   target module's own tests still pass under the shared fixture and the precedent module is
   unaffected.
4. **Document in tech-debt/dev-docs that this ticket's scope was already delivered by
   PYPOST-1176** — at Steps 7-8, record that the guard-test-green outcome was produced by commit
   `494eb857` (PYPOST-1176) rather than by this ticket's own Step 4, so the paper trail correctly
   attributes the fix and the Jira ticket can be closed as already-resolved-by-prior-work with
   evidence.

Verification performed in this step (Step 2), ahead of Step 3/4, since it is read-only and
directly answers whether any implementation is still needed:

```
PYTEST_ARGS="tests/test_suite_qapp_alignment.py tests/test_mcp_controls_presenter.py \
  tests/test_presenter_font_inheritance.py -v" make test
```

Result: `Total Files: 3 | Passed: 3 | Failed: 0 | Skipped: 0` — all three files, including the
suite-wide guard test, pass on `dev` HEAD without any code change.

**Mandatory — Failing Repro (next Step 3):** `N/A — no behavioral change`.

Rationale for why N/A applies here specifically because "already fixed", not because "docs-only"
(both are valid N/A reasons per `td-25-failing-repro`, but they differ and this run's reasoning
must be explicit): the defect this ticket targets — `tests/test_mcp_controls_presenter.py` defining
a local `qapp()` fixture that diverges from the shared `tests/conftest.py` fixture — no longer
exists on `dev` HEAD. It was already eliminated by unrelated commit `494eb857` (PYPOST-1176) before
this ticket's own work began. A "red test" for Step 3 would normally assert the *desired* behavior
against *current* code and fail until a fix lands; here, current code already exhibits the desired
behavior, so any test asserting it would pass immediately — it could not be red without first
reintroducing the local `qapp()` fixture into the target file for the sole purpose of manufacturing
a failure, then removing that regression again in Step 4. That would be pointless churn: it adds a
temporary regression to a currently-passing, currently-correct file, contributes no verification
value beyond what the existing guard test already provides, and risks a transient window where the
suite-wide guard test genuinely fails for a change nobody asked for. The existing guard test
(`tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`)
already serves as the permanent regression guard for this exact defect class, suite-wide, and it is
green today. Step 3 for this ticket is therefore also N/A, carrying the same reasoning forward.

## Architecture

None — no modules are being changed by this ticket. `tests/test_mcp_controls_presenter.py` and
`tests/conftest.py` are both referenced only as read-only verification targets; neither requires
modification, and no new module, dependency, or interface is introduced.

## Q&A

- **Q: If no code changes, why does this step exist at all?**
  A: Per `td-00-rules`/`td-roadmap`, every Top-Down step must produce its artifact even when the
  outcome is "no change needed" — this document is that artifact, and it fixes the verification
  procedure (which commands to run, which files to check) so Steps 3-8 have a concrete, already-
  executed plan to reference rather than re-deriving it.
- **Q: Could the guard test's `_PRIORITY_MODULES` list need updating instead?**
  A: No — `test_mcp_controls_presenter.py` was never in `_PRIORITY_MODULES` (see
  `tests/test_suite_qapp_alignment.py` lines 16-38); it is only covered by the suite-wide
  `test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication` inventory test, which already
  passes for it. No change to the guard test itself is in scope or needed.
