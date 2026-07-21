# PYPOST-835: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

All acceptance criteria for UI state snapshot are met. Items below are
non-blocking follow-ups (no blockers relative to DoD). No Jira tickets created
for this review (orchestrator / user request).

## Shortcuts Taken

- **Env context via duck-typed accessors, not `EnvVariableSnapshot`.** Architecture
  sketched reading the supplier/cache; implementation uses
  `EnvPresenter.current_variables` / `current_hidden_keys` through `getattr` on
  `window.env`. Live combo selection matches what the UI shows; unit tests can
  inject a `_FakeEnv`. Cache and accessors can diverge only if env objects are
  mutated outside `_on_env_changed` (existing presenter contract).
- **`capture_ui_snapshot` accepts `QWidget`, not only `MainWindow`.** Widens the
  API for synthetic unit trees; production callers still pass the ready main
  window. Ready is documented, not enforced inside capture.
- **No `is_ui_ready` guard on `AgentAppSession.ui_snapshot()`.** Same pattern as
  other thin session helpers: callers must start/wait first; started session
  already implies ready after `start()`.
- **DEBUG summary only; no capture-failure event.** Matches Step 5 design —
  scalars (`node_count`, `named_count`, `duration_ms`); exceptions propagate.
- **Full `make check` not re-run.** Step 4 validated `make lint` plus scoped
  snapshot + lifecycle tests (6 passed), same deferral pattern as PYPOST-834.
- **Dev docs landed in Step 7.** `doc/dev/ui_snapshot.md` and
  `ui_snapshot_captured` in `doc/dev/logging.md` are present (not open debt).

## Code Quality Issues

- **Hardcoded selection summary cap:** `_raw_value` for `QAbstractItemView` joins
  at most `indexes[:5]`. Undocumented magic; agents with multi-select may miss
  later rows.
- **Truncation has no ellipsis marker.** Values longer than
  `UI_SNAPSHOT_MAX_VALUE_LENGTH` (500) are sliced silently; consumers cannot tell
  truncation from a short field without knowing the constant.
- **Role vocabulary is a fixed type table.** Checkboxes, spin boxes, tables, and
  other controls fall through to `role="widget"` with `value=null`. Enough for
  FR key surfaces; incomplete for rich post-action checks on niche widgets.
- **Invisible / pruned chrome is intentional** but opaque to callers — no
  `skipped_count` in the DEBUG log (only kept `node_count` / `named_count`).
- **Forced root when `_build_node` returns `None`:** Invisible/empty root still
  yields a minimal node so the API never returns `None`. Edge case only; fine
  for `MainWindow` after show.

Architecture vs implementation (intentional, not regressions):

| Architecture sketch | Implementation | Assessment |
| --- | --- | --- |
| `MainWindow` parameter type | `QWidget` | Testability; OK |
| Env via `EnvVariableSnapshot` | Presenter public accessors | OK; clearer UI truth |
| Optional `ui_snapshot()` | Present on `AgentAppSession` | Matches plan |
| No MCP tool | Confirmed | Matches boundary |
| Truncation constant | `UI_SNAPSHOT_MAX_VALUE_LENGTH = 500` | Matches plan |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Shape / hierarchy (role, name, value, children) | Covered |
| Hidden env value masking | Covered |
| Long value truncation | Covered |
| Ready integration + key `pypost_*` names | Covered (`session.ui_snapshot()`) |
| Explicit timeout markers | Covered (`pytestmark = timeout(60)`) |
| Invisible widgets omitted / unnamed chrome pruned | Not covered (optional) |
| `QTabWidget` / `QComboBox` / item-view value extractors | Not covered (optional) |
| Env missing / empty accessors → no crash, empty sanitize ctx | Not covered (optional) |
| `ui_snapshot()` before `start()` raises | Not covered (optional) |
| DEBUG `ui_snapshot_captured` fields (caplog) | Not covered (optional) |
| Multi-tab / post-action value change | Sibling stories (836+) |
| Full `make check` green | Not re-run for this story |

No timeout-marker blockers.

## Performance Concerns

None for intended use. Capture is on-demand, walks visible widgets once, truncates
long text, and logs only integer scalars. Very deep or unusually large trees could
raise `duration_ms` / `node_count` (observable at DEBUG); not a DoD issue for
current MainWindow surfaces.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Document or name the item-view selection cap (or raise it) | `indexes[:5]` magic | [PYPOST-848](https://pypost.atlassian.net/browse/PYPOST-848) |
| TD-2 | Low | Truncation marker (e.g. ellipsis) when slicing values | Agents can detect clip | [PYPOST-849](https://pypost.atlassian.net/browse/PYPOST-849) |
| TD-3 | Low | Unit tests: prune/invisible skip + tab/combo/item_view values | Hardens extractors | [PYPOST-850](https://pypost.atlassian.net/browse/PYPOST-850) |
| TD-4 | Low | Caplog assert for `ui_snapshot_captured` scalars | Observability regression | [PYPOST-850](https://pypost.atlassian.net/browse/PYPOST-850) |
| TD-5 | Low | Run full `make check` when sibling noise is clear | Deferred gate | [PYPOST-850](https://pypost.atlassian.net/browse/PYPOST-850) |
| TD-6 | Low | Optional richer roles (checkbox, spin, table) if agents need them | Beyond v1 FR surfaces | [PYPOST-850](https://pypost.atlassian.net/browse/PYPOST-850) |

Deferred by design (not debt for this ticket):

- Network MCP `ui_snapshot` tool — packaging / later epic wrap (839+).
- Actions / settle waits / golden flow — PYPOST-836 / 837 / 838.
- Exhaustive capture of every dialog and offscreen widget.

## Blocker Review

**SAFE TO CLOSE** — FR1–FR6 satisfied by `capture_ui_snapshot` /
`AgentAppSession.ui_snapshot()`, reuse of `sanitize_text` + env accessors,
structured tree contract, and `tests/test_ui_snapshot.py` (shape, masking,
truncation, ready integration). Listed gaps are non-blocking; follow-ups above
are plain titles only (no Jira keys invented).
