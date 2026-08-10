# PYPOST-1005: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — no blockers. Parse runs off the GUI thread with a
non-modal busy cue; PYPOST-987 import outcomes are preserved. Remaining items
are documented deferrals (Step 8 docs, optional determinate progress, optional
plan/apply async, small test gaps), not incomplete DoD work.

Scope reviewed: `pypost/core/qt/collection_import_parse_worker.py`,
`pypost/ui/presenters/collection_import_actions.py`,
`pypost/ui/presenters/collections_presenter.py`,
`pypost/core/collection_messages.py`,
`tests/test_collection_import_responsiveness.py`,
`tests/test_collections_import_ui.py`, and `ai-tasks/PYPOST-1005/*`.

## Shortcuts Taken

- **Parse-only off-thread.** Conflict prompts, `plan_collection_import`, and
  `apply_imported_collections` stay on the GUI thread after
  `parse_completed`. Architecture locked this deliberately so import semantics
  match PYPOST-987/1004; a pathological plan/apply over tens of thousands of
  collections could still hitch briefly. See *Performance Concerns* and
  *Follow-up Tasks* #3.
- **Indeterminate busy cue only.** Status-bar text
  (`MSG_IMPORT_PREPARING`) plus Import button disabled — no
  `progress(done, total)` signal and no Qt-free `on_progress` on
  `load_collection_import_candidates`. Architecture listed determinate progress
  as optional; JSON decode remains one opaque chunk until `_read_records`
  returns, so percent feedback would only cover post-decode validation anyway.
  Startup loading also has no percent UI. See *Follow-up Tasks* #2.
- **Import button disabled via `findChild`.** `_set_preparing` looks up
  `COLLECTION_IMPORT_BUTTON` on `parent_widget` rather than taking an injected
  enable/disable callable. Status hooks are injected; the button is not. Works
  because the panel is the parent and the widget id is stable
  (`ui_identity.md`). Slight asymmetry with `show_status` / `clear_status` DI.
- **No new pending-operation queue.** One user pick → one parse worker. Matches
  architecture (unlike env/collection storage gateways). Overlapping Import
  clicks are skipped via `is_busy()` INFO `collection_import_skipped
  reason=busy`.

## Code Quality Issues

- **`Signal(object, object)` / `Signal(object)` on the worker.** Same pattern as
  sibling Qt workers when crossing threads with typed Python objects
  (`list[Collection]`, exceptions). Readable enough; tightening to a custom
  result type would be polish only.
- **Busy re-entry is log-and-return, not queued.** A second Import click while
  preparing is ignored. Users must click again after the cue clears. Acceptable
  for a user-initiated one-shot; documenting here so product does not assume
  click-queueing.
- **Dual logging of file-level failures** (worker WARNING + orchestrator
  `collection_import_file_invalid`) is intentional per `50-observability.md`,
  not accidental noise — operators see both off-thread failure and the
  terminal “nothing changed” event.

## Missing Tests

**No blocker.** Explicit timeouts per `.cursor/lsr/do-testing.md`:

- `tests/test_collection_import_responsiveness.py` —
  `pytestmark = pytest.mark.timeout(120)` (GUI/responsiveness tier)
- `tests/test_collections_import_ui.py` —
  `pytestmark = pytest.mark.timeout(60)` (GUI tier)

Internal waits use bounded `process_until(..., timeout_ms=...)`.

| Scenario | Status |
| --- | --- |
| Event loop responsive during parse + busy cue | Present (blocking stub) |
| Happy path / conflicts / invalid / zero candidates / save failure | Present (async waiters) |
| caplog async lifecycle (`parse_started`, busy cue, `completed`) | Present |
| Explicit pytest timeout markers | Present — not a blocker |
| Second Import click while busy → skip + INFO log | Missing |
| Unexpected exception from `read_import_file` → invalid dialog + ERR | Missing (behavioral + caplog) |
| Status-bar preparing text asserted (not only button / `is_busy`) | Missing |
| Large synthetic JSON under `tmp_path` (CPU-bound real parse) | Missing — DoD met via blocking stub; real-parse regression optional |
| Worker finish-wait timeout WARNING | Missing (hygiene edge) |

## Performance Concerns

- **Plan and apply remain synchronous on the GUI thread.** For typical imports
  this is fine; only an extreme candidate count after a fast parse would
  reintroduce a noticeable hitch. Out of scope unless profiling shows parse was
  not the freeze (architecture risk table).
- **Whole-file `json.loads` is still one opaque chunk** inside
  `load_collection_import_candidates`. Off-thread placement removes the UI
  freeze; it does not stream-decode. Determinate progress during decode would
  need a different parser — not justified for this ticket.

## Deviations from Initial Architecture

None material. Delivery matches `20-architecture.md`:

- `CollectionImportParseWorker` under `pypost/core/qt/`
- `CollectionImportActions` as `QObject` owning worker lifecycle + busy cue
- Non-modal status + Import disabled (no modal `QProgressDialog`)
- `read_import_file` DI preserved; plan/apply/conflict policy unchanged
- Optional determinate `progress` / `on_progress` **not** implemented — listed
  as optional in architecture; indeterminate cue satisfies DoD

Dev and user doc updates remain **Step 8** (architecture items 6–7;
`doc/dev/collection_import.md` still describes a synchronous-looking flow and
omits the parse worker / new log events).

## Hardcoded Values

- `_WORKER_FINISH_WAIT_MS = 100` — same PYPOST-829 bounded join pattern as
  storage gateways; not user-facing.
- `MSG_IMPORT_PREPARING` lives in `collection_messages.py` (correct place).
- Responsiveness test holds parse ~0.4s (`_PARSE_HOLD_S`) — test-only.

## Pre-existing Issues Encountered (not caused by this task)

- Full `make check` / `make test` can abort on macOS with `Segmentation fault`
  inside unrelated Qt encryption-migration UI tests
  (`tests/test_settings_encryption_migration_ui.py`). Documented in
  `doc/dev/testing.md` and Step 5 notes. Touched-module suites for this task
  pass in isolation.
- Unrelated pre-existing suite failures noted in Step 5
  (`test_dialogs_audit`, `test_function_registry`, `test_jira_mcp_live_smoke`,
  `test_main_window_encrypted_startup`) sit outside this touch set.

## Follow-up Tasks

1. **Step 8 (this task):** Update `doc/dev/collection_import.md` architecture
   diagram and flow for async parse worker + busy cue; catalog new structured
   log events (`collection_import_parse_started`, worker start/complete/fail,
   busy cue show/clear, skip-busy, finish wait timeout). Update
   `doc/user/collections.md` (or equivalent) if it omits that large imports stay
   responsive with a preparing cue.
2. **Optional — determinate progress** during post-decode candidate validation:
   Qt-free `on_progress(done, total)` on the loader + worker `progress` signal +
   status-bar `done/total` text. Only if operators find indeterminate “Preparing…”
   insufficient for multi-megabyte files.
   Jira: [PYPOST-1061](https://pypost.atlassian.net/browse/PYPOST-1061)
3. **Optional — profile and, if needed, move plan/apply off the GUI thread**
   (or chunk them) for pathological import sizes. Do not expand without evidence
   that parse is no longer the bottleneck.
   Jira: [PYPOST-1062](https://pypost.atlassian.net/browse/PYPOST-1062)
4. **Close small async test gaps:** busy re-entry skip + INFO assertion;
   unexpected `read_import_file` exception → dialog + ERR `caplog`; optional
   status-message assertion; optional large synthetic JSON responsiveness
   regression alongside the blocking stub.
   Jira: [PYPOST-1063](https://pypost.atlassian.net/browse/PYPOST-1063)

None of the above blocks shipping. Parent debt item #3 from PYPOST-987
(async import parse with progress feedback) is addressed for the user-visible
responsiveness and busy-cue outcome.

## Verdict

**SAFE TO CLOSE** — no blockers. Timeout markers are present; parse is off the
GUI thread; busy cue and re-entry guard match architecture; deferred work is
Step 8 docs and optional polish, not incomplete responsiveness.
