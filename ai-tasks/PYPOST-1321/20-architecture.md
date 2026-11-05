# PYPOST-1321: Register collection import teardown with main-window shutdown

## Research

### Current code facts (verified)

- `pypost/ui/main_window_lifecycle.py:53-154` (`teardown`):
  - Default overall budget is the unnamed literal `5000` (`:55`; also
    `shutdown_for_exit` at `:166`).
  - Owner list today (`:67-76`): `tabs`, `history_panel`, `history_manager`, `env`.
    `window.collections` (`CollectionsPresenter`) is absent.
  - Early `begin_teardown()` on every owner except the last (`:86-89`); `env` uses
    `begin_root_teardown()` then a late `begin_teardown()` after the tabs→env drain
    (`:111-120`). Env must stay last so that special case remains valid.
  - Per-owner budget: `allocated = budget_ms * slots_left / len(owners)`, then
    `owner_budget = min(allocated, remaining)` against one shared monotonic deadline
    (`:121-125`). Adding collections automatically gives it a fair share; no new
    allocator is required for DoD 2.
  - Aggregate outcomes expect each owner to return a `TeardownResult` (`:127-140`).

- `pypost/ui/presenters/collections_presenter.py:395-406`:
  - `teardown(timeout_ms: int | None = None) -> bool` closes collection creation,
    delegates to `CollectionImportActions.teardown`, closes the panel, and returns
    a bool. It does **not** return `TeardownResult`, does **not** expose
    `begin_teardown`, and does **not** cache a terminal result.
  - Presenter is near the LOC baseline cap (~527 / 535 from PYPOST-1264 debt); a
    lifecycle helper module (tabs pattern) is preferred over growing the presenter.

- `pypost/ui/presenters/collection_import_actions.py:172-274`:
  - Budgeted, shared-deadline teardown from PYPOST-1264; returns `bool` (`clean`).
  - Cooperative interrupt for the file parse worker; library worker is join-only
    (PYPOST-1324 remains out of scope).
  - New admission is rejected only while `is_busy()`; there is no teardown fence
    that rejects import start after teardown has begun while idle.

- `pypost/core/lifecycle.py`:
  - `TeardownResult` fields: `owner`, `outcome`, `elapsed_ms`, `active_count`,
    `pending_count`, `failure_kind`, optional `dispositions`.
  - `_LIFECYCLE_OWNER_BY_CLASS` has no `CollectionsPresenter` entry.
  - Peer owners (`TabsPresenter`, `HistoryPanel`, `EnvPresenter`, gateways) implement
    `begin_teardown` + idempotent `teardown` → `TeardownResult`, emit
    `lifecycle_teardown_started` / `_completed` with `teardown_id`, and call
    `record_teardown_metrics`.

- Tests that encode the current owner contract:
  - `tests/test_presenter_teardown_contract_repro.py` composition harness asserts
    call order `["tabs", "history_panel", "history_manager", "env"]` and shared
    remaining-deadline arithmetic. `_CompositionRootHarness` has no collections
    slot today; those tests must gain a collections owner when the production list
    does.
  - No automated proof that app close during file or library import runs
    collections teardown (PYPOST-1264 missing-test #1 / this ticket DoD 7).

- Related debt (authoritative pointers, not reimplemented here):
  - PYPOST-1264 Risk 5 / follow-up 1 → this ticket.
  - PYPOST-1325: name the application shutdown `5000` literals (optional here).
  - PYPOST-1324: library-worker interruptibility (out of scope; unclean within
    collections share remains accepted).

### External research

- **Qt cooperative shutdown**: `QThread.requestInterruption()` is advisory;
  `wait(deadline)` returns when the thread finishes or the deadline expires and
  does not stop the thread. `terminate()` remains discouraged. This matches the
  existing PYPOST-1264 policy and the NFRs for this task.
  Sources: [QThread (Qt 6)](https://doc.qt.io/qt-6/qthread.html),
  [Safe QThread usage in PySide6 (close-during-worker)](https://medium.com/@asilichenko/safe-qthread-usage-in-pyside6-signals-cancellation-and-error-handling-bf1823d95354).
- **Bounded close-while-worker-running**: intercept close, request interruption,
  wait with a timeout, log and proceed if the worker does not finish — never hang
  indefinitely. Same shape as main-window + collections budgets.
- **Shared parent deadline / child grant**: child work receives
  `min(local_grant, parent_remaining)` and does not reset the caller deadline
  ([Keel budgets and cancellation](https://www.keelcore.dev/docs/harness/budgets-and-cancellation)).
  This is exactly how `main_window_lifecycle` already allocates
  `min(allocated, remaining)` to each owner, and how
  `CollectionImportLifecyclePolicy` / `ImportTeardownDeadline` consume a
  caller-supplied budget.
- **Cooperative cancellation only**: forcible kill of Python/Qt workers that may
  hold locks or mutate shared state is unsafe; shutdown waits cooperatively then
  reports incomplete
  ([spaCR threading audit](https://einarolafsson.github.io/spacr/threading_cancellation_audit.html)).

## Implementation Plan

1. **Admit collections as a main-window shutdown owner** in
   `main_window_lifecycle.teardown`: include `getattr(window, "collections", None)`
   in the owner tuple **immediately before `env`**, so env remains last (drain /
   `begin_root_teardown` contract unchanged). Existing early `begin_teardown` loop
   then fences collections with the other non-last owners.
2. **Align `CollectionsPresenter` with the shutdown participant contract** (DoD 5–6):
   - Add `begin_teardown()` that sets a presenter fence (and forwards admission
     close into import actions) without waiting or closing the panel.
   - Change `teardown(...)` to return `TeardownResult` (idempotent, correlated,
     metrics-recorded), mapping the existing import `bool` into
     `success` / `incomplete` + `failure_kind="timeout"`, with `active_count` /
     `pending_count` derived from live import workers / busy state.
   - Prefer extracting lifecycle helpers to
     `pypost/ui/presenters/collections_presenter_lifecycle.py` (tabs precedent) so
     the presenter stays under the LOC baseline.
3. **Fence new import admission** in `CollectionImportActions` once teardown has
   begun (even when idle), so file and library import entry points refuse new work
   the same way peer owners reject post-fence admission. Preserve PYPOST-1264
   teardown phase ordering and budgets inside the actions; they still take a
   caller-supplied `timeout_ms` and return `bool`.
4. **Wire lifecycle identity**: register `CollectionsPresenter` →
   `collections_presenter` in `_LIFECYCLE_OWNER_BY_CLASS`; emit
   `lifecycle_teardown_started` / `_completed` with `teardown_id` (keep or thin the
   existing `collections_presenter_teardown_*` lines so diagnostics stay useful
   without breaking aggregability).
5. **Optional PYPOST-1325 overlap**: do **not** require a full application
   lifecycle policy module. The existing per-owner formula already gives
   collections a fair share once it is on the list. Leave naming the `5000`
   literals on PYPOST-1325 unless Step 4 finds documenting the share needs a
   single named constant in `main_window_lifecycle` (minimal extract only).
6. **Update composition-root contract tests** for the new owner slot and order.
7. **Regression coverage** (DoD 7): app-close / main-window teardown during an
   active file parse worker and during an active library worker, proving
   collections teardown runs under its allocated budget. Keep
   `CollectionImportActions` / PYPOST-1264 budget arithmetic tests green.

**Mandatory — Failing Repro (next Step 3):**

- **Location**: `tests/test_main_window_collections_shutdown_repro.py` with
  `pytestmark = pytest.mark.timeout(30)`, using `qapp`.
- **What it asserts (desired behaviour)**:
  1. `MainWindow.teardown` (via the public composition seam / a thin harness that
     binds real `main_window_lifecycle.teardown` to a root with a real or double
     `collections` owner) **invokes** `collections.teardown` with an integer
     `timeout_ms` that is a fair share of the shared budget
     (`0 ≤ timeout_ms ≤ budget`, and consistent with
     `min(allocated, remaining)` for its index).
  2. Owner call order includes collections immediately before env:
     `tabs → history_panel → history_manager → collections → env`.
  3. **File-import in flight**: with a spy/blocked parse worker on the real
     `CollectionImportActions` (or presenter), after `root.teardown(budget)`,
     import teardown has run (signals disconnected / interruption requested /
     worker field cleared as today) and the collections `TeardownResult` reports
     `outcome in {"success", "incomplete"}` with `active_count >= 1` when a worker
     was running at start, under the allocated budget (no unbounded hang;
     module timeout is the backstop).
  4. **Library-import in flight**: same for `_library_worker` — teardown waits /
     reaps under the collections share; unclean/`incomplete` is allowed if the
     non-interruptible worker outlives the share (PYPOST-1324).
- **How to force failure without live external deps**:
  - Composition ordering / budget-share asserts use owner doubles (extend
    `_CompositionRootHarness` or a sibling harness) — no disk, no network.
  - In-flight import asserts use existing spy / `threading.Event`-blocked worker
    patterns from `tests/test_collection_import_teardown_budget_repro.py` (no real
    library service, no real import files).
- **Red today**: collections is omitted from the owner list, so
  `collections.teardown` is never called during `main_window_lifecycle.teardown`;
  ordering and “teardown ran under budget while import active” asserts fail.
- **Sequencing**: research (this step) → red repro (Step 3, no production change)
  → owner registration + `TeardownResult` / fencing alignment (Step 4) until green
  → keep PYPOST-1264 suite green → optional constant extract only if needed.

## Architecture

### Module diagram

```mermaid
flowchart TD
    CE["close_event / handle_exit / shutdown_for_exit"]
    MW["main_window_lifecycle.teardown<br/>shared deadline + owner loop"]
    TABS["tabs<br/>begin_teardown + TeardownResult"]
    HP["history_panel"]
    HM["history_manager"]
    CP["CollectionsPresenter<br/>begin_teardown + TeardownResult"]
    CPL["collections_presenter_lifecycle<br/>(new helper module)"]
    CIA["CollectionImportActions<br/>budgeted teardown → bool<br/>admission fence"]
    POL["collection_import_lifecycle_policy<br/>ImportTeardownDeadline"]
    ENV["env<br/>begin_root_teardown + drain + teardown"]
    PW["CollectionImportParseWorker"]
    LW["LibraryOperationWorker"]

    CE --> MW
    MW -->|"begin_teardown early"| TABS
    MW -->|"begin_teardown early"| HP
    MW -->|"begin_teardown early"| HM
    MW -->|"begin_teardown early"| CP
    MW -->|"owner_budget = min(allocated, remaining)"| TABS
    MW --> HP
    MW --> HM
    MW --> CP
    MW -->|"last: drain then begin + teardown"| ENV
    CP → CPL
    CPL → CIA
    CIA → POL
    CIA -->|"requestInterruption / wait"| PW
    CIA -->|"wait remaining only"| LW
```

Dependency direction: composition root (`main_window_lifecycle`) → UI presenters →
import actions → Qt-free policy. No new reverse dependencies into the lifecycle
module from collections.

### Owner ordering and budget share

| Index (0-based) | Owner | Role on close |
| --- | --- | --- |
| 0 | `tabs` | Fence requests; drain env-update handoff cutoff |
| 1 | `history_panel` | Fence panel refresh |
| 2 | `history_manager` | Persist accepted history work |
| 3 | **`collections` (new)** | Fence import admission; interrupt/join import workers |
| 4 | `env` | Root fence, drain accepted updates, storage teardown |

With five owners and overall budget `B`, collections at index 3 receives
`min(B * 2/5, remaining)` at its turn (same formula as peers). Idle collections
teardown remains effectively free (PYPOST-1264 idle path), so DoD “no added delay
when idle” holds without a special case in the composition root.

**Rejected alternatives:**

- Calling `CollectionImportActions` directly from `main_window_lifecycle` —
  bypasses presenter fencing, panel close, and creation-closed semantics.
- Placing collections after `env` — breaks env-last drain / `begin_root_teardown`.
- Placing collections first — unnecessary; request/history shutdown should still
  precede collections so UI-side request work stops before import apply can race
  with a dying tabs presenter. Mid-list before env is enough.

### Interfaces

| Surface | Contract after this task |
| --- | --- |
| `main_window_lifecycle.teardown` owner list | Includes `window.collections` before `env` when present and `teardown`-callable |
| `CollectionsPresenter.begin_teardown() -> None` | **New.** Sets fence; rejects new import admission; no wait; no panel close |
| `CollectionsPresenter.teardown(timeout_ms: int \| None = None) -> TeardownResult` | **Signature change** from `bool`. Idempotent; honors caller budget; correlates via `_teardown_correlation_id`; records metrics |
| `CollectionImportActions.teardown(...) -> bool` | Unchanged return type; still shared-deadline phases from PYPOST-1264 |
| `CollectionImportActions` admission | After fence/teardown begun: file and library import entry points no-op / reject (log reason=`teardown`), including when not busy |
| `TeardownResult.owner` | `"collections_presenter"` |
| Outcome mapping | Import `clean is True` → `outcome="success"`; `clean is False` → `outcome="incomplete"`, `failure_kind="timeout"`; no new `"failed"` path unless a future hard error appears (none required now) |
| Counts | `active_count`: running parse and/or library workers at teardown start; `pending_count`: `1` if import state is non-idle else `0` (scalar, no collection content) |

Callers that today treat `CollectionsPresenter.teardown()` as a truthy `bool`
(tests such as `test_collection_import_teardown_policy.py`, MCP collection copy
tests, fixtures) update to assert on `TeardownResult.outcome` (or
`outcome == "success"`). Actions-level callers keep using `bool`.

### Patterns and justification

- **Composition-root owner list (existing)**: extend, do not invent a parallel
  close path (requirements constraint).
- **Fair remaining-deadline grants**: parent shared deadline +
  `min(allocated, remaining)` child grant — already implemented; collections
  plugs in.
- **Presenter lifecycle helper module**: mirrors `tabs_presenter_lifecycle.py`;
  keeps `CollectionsPresenter` under the LOC gate and isolates fencing /
  `TeardownResult` construction.
- **Adapter at presenter boundary**: keep import actions on `bool` so PYPOST-1264
  tests and policy stay stable; adapt once at the shutdown participant surface
  (DoD 5 without rewriting the import teardown engine).
- **Cooperative interruption only**: no `QThread.terminate()`; library join-only
  limitation unchanged (PYPOST-1324).

### Preservation of PYPOST-1264 behaviour (DoD 4)

Inside the collections share, import teardown keeps: cooperative interrupt →
wait-idle → disconnect/join file worker → join/reap library worker → IDLE;
no late UI delivery; no collection add/modify after teardown; idle fast path;
idempotent second teardown; no forcible kill. Only the **caller** changes on app
close: main-window now supplies the allocated share instead of never calling.

### Risks

1. **Bool → `TeardownResult` breaks callers** that assert `is True`. Mitigation:
   update in-repo callers in Step 4; keep actions `bool` unchanged.
2. **Presenter LOC baseline**: mitigation — extract
   `collections_presenter_lifecycle.py` rather than inlining.
3. **Library worker may consume the full collections share** and report
   `incomplete`. Accepted until PYPOST-1324; close still bounded by the share /
   overall deadline.
4. **Composition harness tests hard-code four owners / order**. Must be updated
   in the same change set as the owner list or they fail for the right reason.
5. **Nested uncapped `worker_finish_join_ms`** (PYPOST-1264 Risk 3) can still
   slightly overrun the collections share; remains within documented tolerance;
   not reopened here.
6. **Optional budget naming**: skipping full PYPOST-1325 leaves the `5000`
   literals unnamed; collections share is still well-defined by the formula.
   Residual naming debt stays on PYPOST-1325.

## Q&A

- **Why put collections before env rather than after tabs?** Env must remain last
  for `begin_root_teardown` and the accepted env-update drain. Collections has no
  dependency on that drain. Sitting with the other mid-list owners is enough and
  matches “extend the existing ordering contract.”
- **Why adapt at the presenter instead of changing `CollectionImportActions` to
  return `TeardownResult`?** Requirements require reportable alignment with the
  shutdown loop, not a rewrite of the import policy. Keeping actions on `bool`
  preserves PYPOST-1264’s surface and tests; one adapter at the participant edge
  is the smallest change that meets DoD 5.
- **Is naming the application budget mandatory?** No. DoD 8 / requirements: only
  when needed to allocate and document the share. The existing allocator already
  documents the share once collections is listed; PYPOST-1325 retains naming debt.
- **Does `begin_teardown` close the panel?** No. Fencing only. Panel close stays
  in `teardown`, matching history_panel (fence early, work in `teardown`).
- **Who accepts this architecture?** Autonomous sprint orchestrator after
  independent review (same gate as Step 1).
