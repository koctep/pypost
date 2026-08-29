# PYPOST-1041: Observability Implementation

## Scope

**N/A for production logging and metrics — this task's entire diff is test-only.**

The delivered diff is:

- `tests/test_display_role_scan_ownership.py` — strengthened AST ownership assertions
  (`_module_all_exports` helper, flat-finder delegation check, inline-`DisplayRole` prohibition,
  `__all__` manifest check).
- `tests/test_display_role_scan_ownership_repro.py` — new mutation-resistance repro.

No production module was changed. `pypost/agent/tree_index.py` already delegated matching to
`display_role_equals` and already declared a conforming `__all__`, so Step 4 needed no production
edit (`git diff --stat` shows one file: the ownership suite; the repro file is untracked/new).

Adding logging or metrics here would be actively wrong, not merely unnecessary:

1. **There is no new runtime path to observe.** `display_role_equals`,
   `find_child_index_by_display_text`, and `find_tree_index_by_display_text` are unchanged pure
   functions over `QModelIndex`. Nothing new executes in production.
2. **The requirements forbid it.** `10-requirements.md` lists "Changing `ui_select` error types,
   error messages, logging, or metric payloads" under **Non-Goals / Exclusions**, and NFR-4
   requires no runtime behaviour change.
3. **Per-row logging would be a defect.** `find_child_index_by_display_text` runs once per model
   row inside a UI action. Logging inside that loop would emit one record per row and would print
   user data (`DisplayRole` strings of environments, collections, requests), violating the skill's
   "do not output large data structures to logs" rule.
4. **The checks never run in production.** They are AST fitness functions executed by pytest.
   Their consumer is a CI log reader, not an operator or a dashboard.

The real observability surface of this diff is therefore **the diagnostic text the ownership
assertions emit into a CI log**. That surface is assessed below against a concrete standard:
*can someone reading only the CI log identify the violating function and the fix without opening
the file?*

### Existing production observability (unchanged, still the operator's surface)

- `pypost/agent/ui_actions.py:ui_select` logs
  `ui_action_applied primitive=select widget_id=%s outcome=ok duration_ms=%s` at **DEBUG** on
  success — an event name, the widget id, and a duration, with no row payload.
- The failure path raises `UiTargetNotInteractableError(widget_id, "option not found: <option>")`
  from `_select_item_view` when `find_child_index_by_display_text` returns `None`; the agent layer
  surfaces that error rather than logging a match miss per row.

Both were unchanged by this task and remain adequate for diagnosing a real selection failure.

## Logging Implementation

### Added Logs

No log statements were added — test-only task, no new production path.

- **EMERG**: none — no system-failure path introduced
- **ALERT**: none — no paging condition introduced
- **CRIT**: none — no critical production error path introduced
- **ERR**: none — the flat/tree finders signal "no match" by returning `None`, unchanged
- **WARNING**: none — no new warning site
- **NOTICE**: none — the project's Python logging has no NOTICE mapping
- **INFO**: none added — `ui_action_applied` already covers the enclosing action at DEBUG
- **DEBUG**: none added — see "per-row logging would be a defect" above

### Log Structure

- Structured logs: unchanged (existing `key=value` event lines)
- Includes context: N/A (no new events)
- Log levels: none added

## Diagnostic Surface Under Test (what replaces logging here)

### Captured diagnostics

Every contract violation was driven through the suite and its real `AssertionError` text captured
(mutant sources reused from `tests/test_display_role_scan_ownership_repro.py`, `_parse` patched to
the mutant, exactly as repro tests 4-5 do). This is verbatim CI text, not a paraphrase:

| Violation | Emitted diagnostic | Names symbol | Names owner module | States the fix | Shows observed state |
| --- | --- | --- | --- | --- | --- |
| Flat finder inlines DisplayRole and drops the call | `find_child_index_by_display_text must call display_role_equals instead of inlining DisplayRole comparison` | yes | no | yes | no |
| Flat finder delegates but *also* touches DisplayRole | `find_child_index_by_display_text must not compare ItemDataRole.DisplayRole inline; use display_role_equals` | yes | no | yes | no |
| `__all__ = []` | `pypost.agent.tree_index.__all__ must export ['display_role_equals', 'find_child_index_by_display_text', 'find_tree_index_by_display_text']; found []` | yes | yes | yes | yes |
| `__all__` partially populated | same message, `found ['display_role_equals']` | yes | yes | yes | yes |
| Non-literal `__all__` — `__all__ = list(_PUBLIC)`, and identically `__all__: list[str] = [...]` | same message, `found []` | yes | yes | yes | **misleading** (`found []` while the manifest is correct) |
| Flat finder deleted/renamed | `pypost.agent.tree_index must define find_child_index_by_display_text (flat sibling DisplayRole scan)` | yes | yes | yes | n/a |
| Tree finder renamed | `missing find_tree_index_by_display_text` | yes | **no** | **no** | no |
| `_select_item_view` renamed | `missing _select_item_view` | yes | **no** | **no** | no |

### Verdict

**Mostly yes, with two named exceptions.** The four assertions this task added or rewrote — three
new (flat-finder delegation, inline-`DisplayRole` prohibition, `__all__` subset) and one rewritten
(`find_child is not None`, previously an `in tree_defs` membership check) — are self-describing:
each names the exact function symbol and the required remedy in one line, and the `__all__`
assertion additionally prints expected-vs-found, which is the only diagnostic in the suite that
reports observed state. A CI reader seeing any of them knows what broke and what to do;
the only step they cannot skip is one `grep` to locate the file, because no message prints a path
(see OBS-3).

The two exceptions are the pre-existing one-word `missing X` messages (OBS-2), which name a symbol
but neither the module that must define it nor the corrective action.

### Findings

Recorded rather than fixed — see each item's rationale. None blocks Step 6.

- **OBS-1 (fail-fast masks co-occurring violations, low-medium).** All fourteen assertions
  (AST-counted) live in a single test function, so a run reports the first violation only.
  Demonstrated: a mutant that both inlines DisplayRole *and* empties `__all__` reports only
  `find_child_index_by_display_text must call display_role_equals ...`; the `__all__` breakage is
  invisible until the first is fixed and CI is re-run. A maintainer landing a broad refactor pays
  one CI round trip per violation.
  *Not fixed here:* splitting the contract into separate test functions would break repro tests 4-5,
  which call `ownership_suite.test_flat_and_tree_share_display_role_match_helper()` by name and
  assert a single `AssertionError`, and would change the suite's test count. Carry to Step 7.
- **OBS-2 (two pre-existing diagnostics are not self-describing, low).** `missing
  find_tree_index_by_display_text` and `missing _select_item_view` state neither the owning module
  (`pypost/agent/tree_index.py`, `pypost/agent/ui_actions.py`) nor the remedy, unlike the
  `pypost.agent.tree_index must define ...` message immediately above them. A CI reader must open
  the test file to learn which production file to edit.
  *Not fixed here:* on the AGENTS.md scope argument alone. AC-4 (`10-requirements.md:88`) pins
  these pre-existing assertions as "intact, passing, and unchanged **in intent**" — rewording a
  diagnostic changes no intent, so AC-4 does not forbid the improvement and must not be cited as
  if it did. What does hold is AGENTS.md's prohibition on edits outside the ticket's scope: this
  ticket's scope is the flat finder and the export manifest, not the
  tree-finder/`_select_item_view` presence checks. Carry to Step 7.
- **OBS-3 (no diagnostic prints a file path, low).** Of the 14 assertions, four messages name the
  dotted module `pypost.agent.tree_index` and eight name only a function; the remaining two are the
  `is_file()` guards. The constants `_TREE_INDEX` / `_UI_ACTIONS` hold absolute paths and are
  already interpolated by those two guards (`missing /home/.../tree_index.py`), but by none of the
  twelve contract assertions. Cost to the reader is one
  `grep -rn "def find_child_index_by_display_text"`; accepted as adequate.
- **OBS-4 (diagnostic wording is a machine-checked contract, informational).** Repro tests 4-5 pin
  the message text with `pytest.raises(match=...)`:
  `r"find_child_index_by_display_text.*(display_role_equals|DisplayRole)"` and
  `r"__all__.*export"`. This is deliberate and desirable — the diagnostics cannot silently rot —
  but it means a future reword must keep the function name and the helper name on **one line**
  (`.` does not match a newline) and must keep `__all__` before `export`. Documented here and in
  Step 8 so a maintainer is not surprised by a red repro after "just" rephrasing a message.
- **OBS-5 (a non-literal `__all__` is reported as `found []`, low-medium).** `_module_all_exports`
  scans module-level `ast.Assign` nodes only, and an `ast.AnnAssign` is not an `ast.Assign`, so
  **two** spellings of a *correct* manifest both fail with `... must export [...]; found []`:
  a dynamically built `__all__` (`_PUBLIC = (...)` then `__all__ = list(_PUBLIC)`) and the far more
  ordinary annotated literal `__all__: list[str] = [...]`. Both were driven through the suite and
  emit byte-identical text, which reads as "the manifest is empty" when it is not. The helper's
  docstring documents the empty-set fallback, but the emitted message does not distinguish
  "no literal `__all__` found" from "literal `__all__` is empty".
  *Not fixed here:* all 49 `__all__` declarations under `pypost/` are plain literal assignments
  (verified — no annotated and no computed form exists), so no module trips this at this commit.
  But "unreachable today" is a weaker guarantee than first recorded: the dynamic form is exotic,
  while the annotated form is one token away — adding `: list[str]` to the existing literal in
  `tree_index.py`, a behaviour-preserving typing edit of exactly the kind the repo's
  `make typecheck` mypy baseline invites, would turn the green ownership contract red and blame an
  empty manifest. Carried to Step 7 raised from low to low-medium: the fix is widening one
  `isinstance` check to `(ast.Assign, ast.AnnAssign)` (reading `node.target` instead of
  `node.targets`), not a new code path with no caller.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: none added — no new runtime path. The suite's own bound is the timeout marker
  below; both files run in ~1.2 s wall clock including interpreter and collection start-up, well
  inside NFR-1's 200 ms of actual assertion work.
- **Throughput**: none — not a throughput-bearing change
- **Error rate**: none — the finders' "no match" result is a `None` return, not an error event

### Business Metrics

- none — architectural fitness-function hardening; no user-facing volume changes

### System Health Metrics

- **Resource usage**: unchanged — AST parsing of two source files, no `QApplication`, no display
  server, no network, no disk writes
- **Component status**: unchanged

## Monitoring Integration

- [ ] Prometheus metrics — N/A (no production change)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A. CI itself is the alerting channel: a violated ownership contract fails
      the `make test` gate.
- [ ] Log aggregation (ELK, Loki, etc.) — N/A (no new events)

## Validation Results

- [x] Logs are correctly formatted — N/A (none added); existing `ui_action_applied` line unchanged
- [x] Metrics are collected correctly — N/A (none added)
- [x] Logging works in error scenarios — N/A (no new error path); the equivalent check for this
      diff, exercising every failure branch of the diagnostic surface, was performed and is
      tabulated above (8 violation scenarios driven across 9 mutants — the non-literal `__all__`
      scenario was driven in both its dynamic and its annotated spelling, which emit identical
      text — and all 8 distinct messages captured verbatim)
- [x] Large data structures are not logged — N/A (none added), and per-row DisplayRole logging was
      explicitly rejected because it would print user data once per model row
- [x] Metrics are available for monitoring — N/A (none added)
- [x] Bounded execution confirmed (`20-architecture.md` Phase 4): both
      `tests/test_display_role_scan_ownership.py` and
      `tests/test_display_role_scan_ownership_repro.py` declare
      `pytestmark = pytest.mark.timeout(10)` per `do-testing`
- [x] `make lint` — clean (flake8 on `pypost/`, Markdown lint 16 files, link check 18 files)
- [x] `make test PYTEST_ARGS="tests/test_display_role_scan_ownership_repro.py
      tests/test_display_role_scan_ownership.py"` — 2 files, 6/6 tests passed, 1.18 s wall clock

Full `make test` was deliberately not re-run: it segfaults the Qt workers and writes a ~110 MB core
dump. Step 4 iteration 3 holds the triage of the 8 pre-existing failures
(PYPOST-1231/1232/1233/1234, PYPOST-1111/1117); none touches `tree_index.py`, `ui_actions.py`, or
the ownership suites, and Step 6 changed no code.

## Notes

- **No code change was made in Step 6.** The skill calls for production logging and metrics; this
  diff has no production code, and the requirements explicitly exclude touching `ui_select`
  logging. The two improvable diagnostics (OBS-2) belong to assertions outside this ticket's scope
  — AC-4 freezes their intent, not their wording — and the fail-fast structure (OBS-1) cannot be
  split without breaking the Step 3 repro. All five findings are recorded above for Step 7 rather
  than silently passed over.
- The observability model of this task is inverted relative to a normal feature: the *test* is the
  monitor and CI is the alert channel. The production code it monitors is deliberately silent —
  a pure predicate over `QModelIndex` should stay that way.
