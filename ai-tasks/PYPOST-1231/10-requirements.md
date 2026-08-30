# PYPOST-1231: agent_e2e mark set drifted from the harness table doc

## Goals

`doc/dev/agent_e2e.md` maintains a "Harness modules under the marker" table that is meant to be
the authoritative, human-readable index of every test module carrying `@pytest.mark.agent_e2e`.
Developers rely on this table to understand, at a glance, what the agent_e2e harness covers
without having to grep the test tree. An automated test
(`tests/test_agent_e2e_harness_table_doc.py`) exists specifically to guard this table against
drift — it compares the set of modules actually marked `agent_e2e` against the set of modules
listed in the doc table and fails when the two disagree.

That guard test is currently failing (pre-existing, reproduced at base commit `253403db`,
unrelated to any in-flight feature work). This means the documentation is out of date, and — more
importantly — the CI guard that exists to catch exactly this kind of drift is currently red,
so it provides no protection until it is restored to green. Leaving it red also risks the failure
being normalized/ignored by developers, which defeats its purpose for future changes.

This task exists to restore the documentation to an accurate state and get the guard test passing
again, so the harness table remains a reliable reference and the CI guard resumes doing its job.

## User Stories

- As a developer working on agent_e2e test coverage, I want the harness table in
  `doc/dev/agent_e2e.md` to accurately list every module that carries the `agent_e2e` marker, so
  that I can trust the doc as a complete reference instead of having to cross-check it against the
  test tree myself.
- As a developer running the full test suite, I want
  `tests/test_agent_e2e_harness_table_doc.py` to pass, so that a currently-failing, unrelated test
  doesn't obscure real regressions in my own changes or erode confidence in a green suite.
- As a maintainer of the agent_e2e harness documentation, I want the doc-vs-marks guard test to
  stay green going forward, so that future modules added under the `agent_e2e` marker are caught
  immediately if the doc isn't updated alongside them.

## Definition of Done

- Every test module currently carrying `@pytest.mark.agent_e2e` that is missing from the harness
  table in `doc/dev/agent_e2e.md` is added as a row, with a short "Covers" description consistent
  in style with the existing rows in that table.
- `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
  passes.
- No production (non-documentation) code is changed as part of this task.
- The added rows accurately describe what each module covers (verified against the module's own
  content — docstring/purpose — not invented).

## Task Description

This is a documentation-drift fix. Two or more modules were given the `agent_e2e` pytest marker
by prior tasks but were never added as rows to the "Harness modules under the marker" table in
`doc/dev/agent_e2e.md`, so the table no longer matches reality. An automated regression test
compares the two sets and fails whenever they diverge, and it is currently failing.

The Jira ticket description, written when the ticket was created, cites two missing modules
(`tests/test_agent_session_event_settle.py`, added by PYPOST-1217, and
`tests/test_agent_ui_actions_mcp_seed.py`, added by PYPOST-993). Re-running the repro during this
task's Step 1 (2026-08-30) shows the drift has grown since the ticket was filed: a third module,
`tests/test_ui_actions_tree_no_model_mutation.py`, is also missing from the table. The scope of
this task covers all modules missing from the table as of the verification run performed while
executing this task, not only the two originally named in the ticket — because the business goal
(an accurate, trustworthy doc and a green guard test) is not met if a fix only addresses a stale
snapshot of the drift.

Constraints:

- Documentation-only change: no source/production code is modified.
- No new Jira ticket number should be invented for a module's "Covers" description; if a module's
  purpose can't be tied to a specific ticket from its own docstring/comments, describe its purpose
  in plain terms instead.
- The fix must not weaken or bypass the guard test — the table must actually become accurate, not
  have the test relaxed to tolerate drift.

Out of scope:

- Investigating or fixing *why* modules are added without a doc update (process/tooling
  improvement) — this task only restores current accuracy.
- Any other doc content in `doc/dev/agent_e2e.md` unrelated to the harness table.

## Main Entities

- **Harness table** — the "Module | Covers" table in `doc/dev/agent_e2e.md` that documents every
  test module under the `agent_e2e` pytest marker.
- **agent_e2e-marked test module** — a test file under `tests/` decorated with
  `@pytest.mark.agent_e2e`; expected to have exactly one corresponding row in the harness table.
- **Guard test** — `tests/test_agent_e2e_harness_table_doc.py`, which asserts the marked-module
  set and the documented-module set are identical.

## Q&A

- **Q: Should this task fix only the two modules named in the Jira description, or all modules
  currently missing?**
  A: All modules missing as of this task's verification run. The Jira description itself notes it
  "may be stale," and the business requirement (accurate doc, green guard) is only satisfied by
  matching current reality, not the ticket's original snapshot. Verified via
  `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py"` on 2026-08-30: current
  `only_in_marks=['tests/test_agent_session_event_settle.py',
  'tests/test_agent_ui_actions_mcp_seed.py', 'tests/test_ui_actions_tree_no_model_mutation.py']`,
  `only_in_doc=[]`.
- **Q: What is `tests/test_ui_actions_tree_no_model_mutation.py` about, for its "Covers" row?**
  A: Its module docstring identifies it as PYPOST-1042 / PYPOST-972 TD-1 evidence that
  `test_select_tree_no_model_raises` (in `tests/test_ui_actions.py`) is load-bearing — it proves
  that contract test fails when the production guard in `_select_tree` is deleted or reworded.
  This will be used verbatim as the basis for its "Covers" description in Step 4/8, without
  inventing a different ticket number.
