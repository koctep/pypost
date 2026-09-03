# PYPOST-1228: Refactor CollectionImportActions internal state flags into CollectionImportState enum

## Goals

`CollectionImportActions` (`pypost/ui/presenters/collection_import_actions.py`) drives the
"Import Collection" flow: pick file → parse off-thread → resolve conflicts → plan → persist →
refresh. Today its "is something in flight" notion is spread across two loosely-related pieces of
state (a `_preparing` boolean and an `_worker` reference), combined ad hoc in `is_busy()`. This
was flagged as technical debt during PYPOST-1182 (see
`ai-tasks/PYPOST-1182/60-tech-debt.md`, "Multiple State Flags vs. Explicit State Machine").

Business goal: reduce the risk of import-flow bugs (e.g. a user able to re-trigger import while a
previous one is still finishing) and make the module's lifecycle easy to reason about and test, by
replacing the scattered flags with one formal, explicit state that always answers "what is this
import doing right now?" and "is it safe to start a new one?".

This is a pure internal refactor of state tracking. It must not change what the user experiences
when importing a collection (dialogs shown, ordering of operations, messages, busy cue behavior,
logging content) — only how the module keeps track of where it is in the flow.

## User Stories

- As a user of the collections sidebar, when I trigger "Import Collection" while a previous import
  is still being prepared, parsed, or applied, I want the button to stay disabled / the action to
  be ignored, so that I never end up with two overlapping imports.
- As a user closing the app or a collections panel while an import is in progress (preparing,
  parsing, or applying), I want the app to wait for/cleanly cancel that work exactly as reliably as
  it does today, so I don't lose collections or see a crash.
- As a developer maintaining `CollectionImportActions`, I want one place that tells me the current
  stage of an in-flight import, so that adding or debugging an edge case doesn't require tracing
  multiple booleans/attributes and their interactions.
- As a developer writing tests for the import flow, I want to assert on a single, explicit current
  state (e.g. "the presenter is in PARSING") instead of inferring it from a combination of private
  attributes, so that edge-case transitions are straightforward to set up and verify.

## Definition of Done

- `CollectionImportActions` exposes one authoritative notion of its current lifecycle stage,
  replacing today's separate `_preparing` flag and `_worker`-presence check as the basis for
  "busy" determination.
- The lifecycle recognizes at least the four stages named in the originating tech-debt note:
  **idle** (nothing in flight), **preparing** (file chosen, worker not yet started / picking up),
  **parsing** (background parse worker running), and **applying** (conflict resolution, planning,
  and persisting the parsed collections, after parsing has completed and before the flow returns
  to idle).
- `is_busy()` continues to report "not idle" for at least the same windows of time as today, plus
  closes the applying-stage gap noted below (no shrinking of the busy window) — see Q&A below
  regarding the current gap during "applying".
- All externally observable behavior is unchanged: dialogs, busy-cue text/enable-disable, status
  bar messages, log messages/fields, refresh/restore/emit ordering, and the final import-result
  presentation.
- `teardown()` and `wait_idle()` continue to reliably wait for and clean up in-flight work
  regardless of which lifecycle stage the flow is in when they are called.
- Existing tests for `CollectionImportActions` (e.g. `tests/test_collections_import_ui.py` and any
  other suites exercising this presenter) continue to pass, and cover the new lifecycle stages'
  edge cases (e.g. re-entrancy attempts during each stage, teardown during each stage).
- No change to the module's public API surface consumed by `CollectionsPresenter` or other
  callers, other than what is strictly necessary to expose/observe the new lifecycle state for
  testing purposes.

## Task Description

### Problem

`CollectionImportActions.is_busy()` is currently defined as:

```
return self._preparing or self._worker is not None
```

`_preparing` is set `True` right before a parse worker is created and set `False` again as soon as
the worker's `parse_completed`/`parse_failed` signal fires — i.e. it only covers the short window
between "user picked a file" and "parse worker started reporting progress/results". `_worker` is
non-`None` from worker creation until its `finished` signal has been handled.

Because of this, the module currently has an implicit fifth phase — the synchronous
`_finish_import()` work that runs after parsing completes (conflict-resolution dialogs, planning,
and persisting via `apply_imported_collections`) — that is **not** guaranteed to be covered by
`is_busy()`: if the worker's `finished` signal has already been processed (clearing `_worker`) by
the time `_finish_import()` runs, `is_busy()` reports `False` while conflict dialogs are still
open and collections are still being persisted. This is exactly the class of edge case the
tech-debt note wants easier to reason about and verify.

### Scope

In scope:
- Business/functional requirements for replacing the current flag-based tracking with a single,
  explicit, named lifecycle state for `CollectionImportActions`.
- The four named stages from the tech-debt note (idle / preparing / parsing / applying) as the
  minimum required vocabulary, including closing the observability gap around the "applying"
  window described above.
- Preserving all current user-facing behavior and the current external API used by
  `CollectionsPresenter`.

Out of scope (explicitly not part of this ticket):
- Any change to the Import Collection user experience (file picker, conflict dialogs, result
  dialog, status messages, ordering of steps).
- The other PYPOST-1182 tech-debt follow-ups (worker cancellation — PYPOST-1229; test-helper
  extraction — PYPOST-1230); those are separate tickets.
- Changes to `CollectionImportParseWorker`, `pypost.core.collection_import`,
  `pypost.core.collection_import_apply`, or other collaborators' internal logic — this ticket is
  scoped to how `CollectionImportActions` tracks its own lifecycle.
- Architecture/implementation choices (how the state is represented in code, where it is declared,
  how transitions are wired) — those belong to Step 2 (Architecture).

### Constraints and Assumptions

- `CollectionImportActions` is a Qt `QObject` presenter; state transitions are driven by
  synchronous calls (`import_collections`, `_start_parse`, `_finish_import`) and by Qt signals
  from `CollectionImportParseWorker` (`parse_progress`, `parse_completed`, `parse_failed`,
  `finished`) delivered on the GUI thread.
- The refactor must keep `teardown()` and `wait_idle()` correct and deterministic for tests
  (per PYPOST-829 H3 join semantics referenced in the module's `_WORKER_FINISH_WAIT_MS` comment).
- Python is the implementation language (existing module and codebase language).
- This is a tech-debt/internal-quality ticket: no new user-facing feature, so acceptance is judged
  by behavior parity plus improved internal clarity/testability, not by new functionality.

### Non-Functional Requirements

N/A — no performance/security impact; behavior-parity and determinism/testability requirements are
captured under Constraints/Definition of Done above.

## Main Entities

- **CollectionImportActions**: the presenter/orchestrator owning one Import Collection
  interaction; the entity whose internal lifecycle is being formalized.
- **Import lifecycle state**: the single business concept this ticket introduces — "what stage is
  the current (if any) import interaction in": idle, preparing, parsing, or applying.
- **Parse worker** (`CollectionImportParseWorker`): background off-thread parser whose activity
  window corresponds to the "parsing" stage.
- **Import interaction**: one end-to-end user-triggered sequence (pick file → parse → resolve
  conflicts → plan → persist → refresh) whose progress through the lifecycle states this ticket
  makes explicit.

## User Scenarios

1. **Happy path import**: user clicks "Import Collection", picks a valid file; module moves
   idle → preparing → parsing → applying → idle; button/busy cue reflect "busy" throughout; result
   dialog shown at the end.
2. **Re-entrant trigger while preparing**: user (or an automated double-click) triggers import
   again immediately after picking a file, before the parse worker has started producing output;
   the second attempt is ignored, consistent with current `is_busy()` guard behavior.
3. **Re-entrant trigger while parsing**: same as above, triggered while the background worker is
   actively parsing.
4. **Re-entrant trigger while applying**: same as above, triggered while conflict dialogs are open
   or the parsed collections are being persisted — today this window is not reliably reported as
   busy; after this ticket it must be.
5. **Invalid file / parse failure**: parsing fails or yields no valid collections; module returns
   to idle after showing the appropriate error, without ever entering "applying".
6. **Teardown/close mid-flow**: the panel/app is torn down while the module is in preparing,
   parsing, or applying; `teardown()` must still wait for and clean up the in-flight work exactly
   as it does today, regardless of which stage it was in.

## Q&A

- **Q: Should the "applying" stage's current observability gap (is_busy() can report False while
  `_finish_import()` is still running) be treated as a bug to fix, or left as-is and merely
  labeled?**
  A: Treated as a gap to close. The tech-debt note's stated goal is to "reduce state coordination
  complexity and make edge-case transitions easier to verify" — silently preserving a known
  re-entrancy gap would leave the exact class of edge case this ticket exists to address
  unverified. Definition of Done above requires `is_busy()` to cover the applying window.
- **Q: Does this ticket require changing any user-visible behavior, dialogs, or messages?**
  A: No. This is strictly an internal state-tracking refactor; Definition of Done requires full
  behavior parity aside from closing the applying-window busy gap (which has no user-visible
  effect beyond correctly blocking a re-entrant trigger that today could slip through).
  - **Q: Is a formal `CollectionImportState` enum (as literally named in the tech-debt note)
  mandatory, or is any equivalent internal representation acceptable?**
  A: The tech-debt note and Jira summary explicitly name `CollectionImportState` with values
  `IDLE, PREPARING, PARSING, APPLYING` as the target design; the *business* requirement is a
  single explicit, named lifecycle state with (at least) those four stages. The exact code-level
  representation is an architecture decision for Step 2, not a Step 1 concern.
