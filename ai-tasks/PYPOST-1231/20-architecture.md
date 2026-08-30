# PYPOST-1231: agent_e2e mark set drifted from the harness table doc

## Research

- Guard test: `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`.
  - Discovers marked modules by AST-parsing every `tests/test_*.py` for a module-level
    `pytestmark = [... pytest.mark.agent_e2e ...]` (or a decorator form) — see
    `_discover_marked_modules` / `_module_has_agent_e2e_mark`.
  - Discovers documented modules by locating the `_TABLE_ANCHOR = "Harness modules under the
    marker"` string in `doc/dev/agent_e2e.md`, then scanning the first Markdown table that starts
    with a `| Module |` header row after that anchor, collecting every `` | `path` | `` cell via
    `_MODULE_CELL_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")` until a non-`|` line ends the table.
  - Asserts `marked == documented`, reporting `only_in_marks` / `only_in_doc` on mismatch.
- Re-ran the repro during this step (2026-08-30, same as Step 1):
  `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -v"` → 1 failed, with diff
  showing exactly three modules present in `only_in_marks` and absent from the doc table:
  - `tests/test_agent_session_event_settle.py`
  - `tests/test_agent_ui_actions_mcp_seed.py`
  - `tests/test_ui_actions_tree_no_model_mutation.py`
  `only_in_doc` is empty — the doc has no stale/extra rows. This matches the Step 1 Q&A finding
  exactly (list unchanged since Step 1, confirming no further drift occurred between steps).
- Read each missing module's top-of-file docstring to source the "Covers" text from the module's
  own stated purpose (per the requirement to not invent ticket numbers):
  - `tests/test_agent_session_event_settle.py`: `"""PYPOST-1217: Assert AgentAppSession post-ready
    flush and tree settlement contracts."""`
  - `tests/test_agent_ui_actions_mcp_seed.py`: `"""PYPOST-993: Failing repro test for
    seed/collection injection in sidecar session. ... Seed path resolution and environment
    variable precedence ... Sidecar CLI argument parsing for --seed/--seed-file ...
    In-process AgentAppSession initialization with seed_path and verification that seeded
    collections are loaded into the UI tree and visible in UI snapshot upon reaching
    is_ui_ready."""`
  - `tests/test_ui_actions_tree_no_model_mutation.py`: `"""PYPOST-1042 / PYPOST-972 TD-1: Evidence
    that test_select_tree_no_model_raises is load-bearing. Proves that the contract test in
    tests/test_ui_actions.py genuinely guards the tree-no-model refusal path by showing it fails
    when the production guard in _select_tree is deleted or reworded."""` — this matches the
    Step 1 Q&A verbatim basis already agreed for this row.
- Existing table row style (`doc/dev/agent_e2e.md`, "Harness modules under the marker" section,
  lines ~82-102): `` | `tests/module.py` | Short phrase; optional (ticket-number) suffix | ``.
  Rows favor a concise plain-English phrase over a verbatim docstring quote, with a bracketed
  ticket number only when one directly identifies the change (e.g. `(899)`, `(975)`); several rows
  omit a ticket number entirely when the phrase alone is descriptive.

## Implementation Plan

1. Open `doc/dev/agent_e2e.md` and locate the "Harness modules under the marker" table (the same
   `| Module | Covers |` table the guard test parses, currently ending at
   `` | `tests/test_agent_e2e_websocket.py` | WebSocket UI & Inspector loopback e2e (1132) | ``
   around line 102).
2. Append exactly three new rows immediately after the last existing row, in the same
   `` | `module/path` | Covers text | `` format, alphabetical-by-insertion order not required (the
   guard test only compares sets, not order) but appended in a stable, readable order:

   ```markdown
   | `tests/test_agent_session_event_settle.py` | Post-ready flush and tree settlement contracts (1217) |
   | `tests/test_agent_ui_actions_mcp_seed.py` | Sidecar seed/collection injection: path resolution, CLI args, UI-ready seeded tree (993) |
   | `tests/test_ui_actions_tree_no_model_mutation.py` | Evidence that the tree-no-model contract test is load-bearing (1042/972 TD-1) |
   ```

3. No other content in `doc/dev/agent_e2e.md` is touched — the task is out-of-scope for any other
   doc section (per requirements "Out of scope").
4. No production/source code changes. No changes to the guard test itself (the fix must not
   weaken it — only the doc changes).
5. Verify: re-run `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -v"` and
   confirm it now passes (`marked == documented`, empty `only_in_marks`/`only_in_doc`).

**Mandatory — Failing Repro (next Step 3):** No new red test is written. The guard test
`tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
is a pre-existing, already-failing (red) automated test on the current tree — it is the guard
named directly in the Jira ticket and re-confirmed failing in this step's Research section above
(`only_in_marks` lists the same three modules found in Step 1). This is the standard "pre-existing
guard test now red, doc fix makes it green" pattern: Step 3's job is to formally document/confirm
this existing red test (capture its current failing output as the repro artifact) rather than
author a new test file, since the guard test already asserts the desired behavior (marked-module
set equals documented-module set) and already fails for the right reason (three modules present in
marks, absent from doc). Step 4 makes it pass purely via the three doc-table row insertions above,
with no test-file changes.

## Architecture

This task has no runtime/production architecture — it is a documentation-content fix scoped to a
single Markdown table cell region. There is no module diagram, no new interfaces, and no new
component. The only "interface" involved is the implicit doc-vs-code contract enforced by the
guard test:

- **Producer of truth**: `tests/test_*.py` modules decorated with `@pytest.mark.agent_e2e` (or
  `pytestmark = [pytest.mark.agent_e2e]`).
- **Consumer / mirror**: the `| Module | Covers |` table in `doc/dev/agent_e2e.md`, under the
  `Harness modules under the marker` anchor, which must list exactly the same module-path set.
- **Enforcement**: `tests/test_agent_e2e_harness_table_doc.py`, unchanged by this task, diffing
  the two sets via AST parsing (marks) and anchored-table-row parsing (doc).

This task restores the "consumer / mirror" side to match the "producer of truth" side by adding
the three missing rows; it does not alter the enforcement mechanism or the producer side.

## Q&A

- **Q: Does this task change any production/source code?**
  A: No. Only `doc/dev/agent_e2e.md` is modified (three appended table rows). Confirmed against
  the Definition of Done constraint in `10-requirements.md`.
- **Q: Is the three-module list from Step 1 still accurate as of Step 2?**
  A: Yes, re-verified by re-running `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -v"`
  in this step: identical `only_in_marks` list, empty `only_in_doc`.
- **Q: Where do the three "Covers" descriptions come from?**
  A: Each module's own top-of-file docstring (quoted/paraphrased above), per the requirements
  constraint against inventing ticket numbers or descriptions not grounded in the module's stated
  purpose.
