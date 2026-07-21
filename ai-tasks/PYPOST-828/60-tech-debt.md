# PYPOST-828: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Richer timeout diagnostics meet DoD: optional lazy `timeout_detail`, neutral
default reason, busy/pending on gateway waits, optional `worker_running` on
gateway and worker-only waits, hang-defense timing unchanged. Items below are
non-blocking follow-ups. **Do not create Jira tickets in this step** — Phase D
fills the Jira column.

## Shortcuts Taken

- **`worker_operation` formatted but not wired at call sites.**
  `format_storage_async_timeout_detail` accepts `worker_operation`, and unit
  tests cover the formatter path, but `gateway_timeout_detail` and
  `_worker_timeout_detail` never pass it. Env workers expose `_operation`
  (`load` / `save`); collection workers are load-only and have no operation
  field. DoD is still met via busy/pending + optional `worker_running`.
- **Private `_worker` read for optional running state.** Tests already used
  gateway `_worker` before this ticket; diagnostics reuse that pattern rather
  than adding a public gateway API.
- **Local `_worker_timeout_detail` left in the collection worker module.**
  Single call-site helper; Step 4 intentionally did not extract it next to
  `gateway_timeout_detail`.
- **Full `make check` not re-run.** Step 4 validated `make lint` plus focused
  helper/consumer tests (28 passed). Same scoped pattern as sibling harness
  tickets.

## Code Quality Issues

- **`worker_operation` API surface ahead of consumers** — see Shortcuts / TD-1.
  Formatter + docs mention the field; live timeout text from wired waits never
  includes `worker_operation=…`.
- **Broad `except Exception` around `timeout_detail()`** — intentional so a
  bad detail callable cannot mask the timeout `AssertionError`. Could narrow
  later once failure modes are catalogued (Lowest; accepted by design for now).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Formatter omits `None` fields; includes `worker_operation` when set | Covered |
| `gateway_timeout_detail` busy/pending + `worker_running` | Covered (fake gateway) |
| Default timeout message neutralized | Covered |
| Detail failure does not mask timeout | Covered |
| Hang defense still exits near deadline | Covered |
| Real gateway/worker timeout message with `worker_operation` | Not covered — needs call-site wiring (TD-1) |
| Forced real-gateway timeout asserting busy/pending in CI text | Not covered — optional; wiring + unit coverage exist |
| Full `make check` green after this story | Not re-run for PYPOST-828 |

Timeout markers present (`pytestmark` on diagnostic module and four consumers).
**No timeout-marker blockers.**

## Performance Concerns

None. `timeout_detail` runs only after the wait ends on failure; success paths
do not invoke it. Hang-defense timing unchanged.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Wire `worker_operation` into env gateway timeout detail | Read env worker `_operation` (or a small public accessor) in `gateway_timeout_detail` when present; leave collection load-only waits without the field | [PYPOST-878](https://pypost.atlassian.net/browse/PYPOST-878) |
| TD-2 | Lowest | Optional shared `worker_timeout_detail` helper | Extract from `test_collection_storage_worker.py` only if a second worker-only consumer appears | [PYPOST-879](https://pypost.atlassian.net/browse/PYPOST-879) |
| TD-3 | Low | Run full `make check` when sibling noise is clear | Deferred scoped gate; not a DoD blocker | [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Gateway worker `deleteLater` / short `wait` on finish | [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) |
| Align remaining gateway tests on shared `qapp` | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| Port hang-resistant wait into env-presenter nested wait | [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877) |

### Planned this ticket (not separate Debt)

- Step 7: update `doc/dev/gui_testing.md` (and related storage async notes) for
  richer timeout text — not a Debt ticket.

## User documentation

N/A — harness-only change; no `doc/user/` updates. Developer docs are Step 7.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: timeout reports include duration + neutral reason; gateway load/save
  waits include busy/pending; optional worker running state is available;
  hang-resistant timing preserved; no production behavior change.
- TD-1 is incremental triage polish (env load vs save), not an acceptance gap.
- No missing pytest timeout markers.
- Existing siblings 829 / 830 / 877 remain open and are not recreated here.
