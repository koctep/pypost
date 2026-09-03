# PYPOST-1184: Extract insert-before-plus helper so TabsPresenter stays under 785 LOC

## Goals

`pypost/ui/presenters/tabs_presenter.py` is the central presenter that owns the tab strip for
all three tab kinds (HTTP request, WebSocket, MCP Client). The project enforces a soft LOC cap
on this file (785 lines, tracked since `ai-tasks/PYPOST-376/baseline-metrics.md`) to keep the
presenter reviewable and to stop it from becoming a dumping ground for every new tab-kind
feature. PYPOST-1166's tech-debt analysis (`ai-tasks/PYPOST-1166/60-tech-debt.md`) flagged that
the three tab-factory methods — `add_new_tab`, `_insert_websocket_tab`, and
`_insert_mcp_client_tab` — each hand-roll the same "insert the new tab immediately before the
`+` (new-tab) button, or append and re-create the `+` tab if none is found, then focus it and
optionally persist tab state" sequence. That duplication was flagged as the thing to remove
**before** later MCP-TM work (restore, env propagation, `_current_tab` wiring) adds enough new
lines to blow through the cap.

**Verified current state (2026-09-03):** the file is no longer near the cap — it is
**1,064 lines**, already **279 lines over** the 785 cap. The insert-before-plus duplication is
confirmed present unchanged in all three factories. This means the business goal has shifted
from "extract before we breach the cap" to "extract as part of pulling the file back toward the
cap" — the preventive framing in the original ticket description is stale, but the underlying
duplication and its removal are still exactly what is needed.

The business goal is to keep `TabsPresenter` maintainable: a shared helper for the
insert-before-plus sequence removes ~14-21 duplicated lines across three call sites, reduces the
risk that a future edit to the plus-tab logic is made in only one or two of the three places
(a correctness/consistency risk, not just a line-count one), and gives later MCP-TM stories more
LOC headroom to work with in this file.

## User Stories

- As a developer implementing later MCP-TM stories (restore, env/header propagation,
  `_current_tab` wiring) that must touch `TabsPresenter`, I want the insert-before-plus logic
  centralized in one helper, so that I am not repeating or diverging from the existing pattern
  when I add a fourth call site or modify the existing three.
- As a developer maintaining tab-strip behavior (e.g. fixing a plus-tab bug), I want a single
  place that inserts a tab before the plus button, so that a fix applies uniformly to HTTP,
  WebSocket, and MCP Client tabs instead of requiring me to find and patch three near-identical
  blocks.
- As a code reviewer / tech-debt auditor, I want `tabs_presenter.py`'s duplicated tab-insertion
  logic removed, so that the file's LOC and complexity move back toward the enforced cap rather
  than growing further.

## Definition of Done

- The duplicated "insert before plus / append-and-ensure-plus / setCurrentWidget / optional
  save_tabs_state" sequence currently repeated in `add_new_tab`, `_insert_websocket_tab`, and
  `_insert_mcp_client_tab` is consolidated behind a single shared code path used by all three.
- Behavior is unchanged for all three tab kinds: a new tab is still inserted immediately before
  the `+` tab when the header reports one, otherwise appended and a `+` tab is (re-)ensured; the
  new tab still becomes the current tab; `save_tabs_state()` is still called only when the
  caller's `save_state` flag is true.
- No regression in existing tab-open / tab-restore / tab-save-state behavior for HTTP, WebSocket,
  and MCP Client tabs (verified by existing and/or updated automated tests — test strategy is
  Step 3/4 scope, not this step).
- `tabs_presenter.py`'s line count is measurably reduced by the extraction (exact target LOC and
  the destination of the extracted code — same file vs. a helper module — is an architecture
  decision for Step 2, not this step).
- The tech-debt item "Triplicated insert-before-plus" in `ai-tasks/PYPOST-1166/60-tech-debt.md`
  is resolved by this change.

## Task Description

### Problem

`tabs_presenter.py` currently implements three near-identical blocks (see Q&A for exact line
ranges as verified in this step) that each:

1. Ask the tab header for the index immediately before the plus/new-tab marker
   (`self._header.insert_index_before_plus()`).
2. If a valid index is returned, insert the new tab widget there with a computed title.
3. Otherwise, append the tab and ask the header to (re-)ensure a plus tab exists
   (`self._header.ensure_plus_tab()`).
4. Focus the newly created tab (`self._tabs.setCurrentWidget(tab)`).
5. Optionally persist the open-tabs state (`self.save_tabs_state()`) when the caller's
   `save_state` argument is true.

This sequence is duplicated verbatim (modulo the tab object and computed title) across the HTTP,
WebSocket, and MCP Client tab-factory methods. The duplication:

- Inflates the file's line count, contributing to it already exceeding the enforced 785-line
  cap.
- Creates a correctness risk: a future change to plus-tab placement/behavior must be applied
  identically in three places, and nothing enforces that it will be.
- Was explicitly called out by the PYPOST-1166 tech-debt review as the concrete thing to fix
  before further MCP-TM growth in this file.

### Goals of this task

- Remove the duplication by introducing one shared way to perform "insert this tab before the
  plus button (or append and re-ensure the plus tab), then focus it, then optionally save
  state."
- Apply it uniformly to all three existing call sites (HTTP `add_new_tab`, WebSocket
  `_insert_websocket_tab`, MCP Client `_insert_mcp_client_tab`).
- Reduce `tabs_presenter.py` LOC as a direct, measurable side effect.

### Constraints and Assumptions

- This is a pure tech-debt / internal-refactor task: **no user-visible behavior may change**.
  Tab titles, tab ordering, plus-tab placement, focus behavior, and state-persistence timing
  must remain exactly as they are today for all three tab kinds.
- The three call sites currently differ only in: the widget type being inserted, how the tab's
  display name is computed (`request_data.name or "New Request"`, `connection.name or
  "WebSocket"`, `connection.name or "New MCP Client"`), and the return value (two of the three
  return the created tab; `add_new_tab` does not). Any shared helper must account for these
  differences without changing them.
- No new dependencies, database/storage schema changes, or public API changes are in scope.
- The project's existing 785-line soft cap on `tabs_presenter.py` and the language (Python) are
  both established facts, not decisions made in this task; this task works within them.
- How the deduplication is implemented (a private method on `TabsPresenter`, a free function in
  an existing or new sibling helper module such as the existing
  `tabs_presenter_draft.py` / `tabs_presenter_close.py` pattern, etc.) is an architectural
  decision deferred to Step 2.
- Test strategy (whether new tests are needed, or existing `tests/test_tabs_presenter.py`
  coverage is sufficient to catch a regression) is deferred to Steps 3/4, consistent with the
  Top-Down workflow's separation of requirements from implementation.

## Main Entities

- **TabsPresenter** — the presenter under discussion; owns the `QTabWidget` tab strip and the
  three tab-factory methods that duplicate the insert-before-plus sequence.
- **Tab (HTTP `RequestTab` / `WebSocketTab` / `McpClientTab`)** — the three widget types that get
  inserted into the tab strip by the duplicated logic; each represents one open tab of a given
  protocol.
- **Tab header (`RequestTabHeader`)** — owns the plus/new-tab marker and exposes
  `insert_index_before_plus()` and `ensure_plus_tab()`, which the duplicated logic calls into.
- **Tab state persistence (`save_tabs_state`)** — the optional side effect triggered at the end
  of each duplicated block when the caller asks for it.

## User Scenarios

- **Open a new blank HTTP request tab** (`add_new_tab`): the tab is inserted before the plus
  button (or appended with the plus tab re-ensured), focused, and — unless the caller suppressed
  it (e.g. during bulk restore) — the open-tabs state is saved.
- **Open a new WebSocket connection tab** (`add_blank_websocket_tab` /
  `open_websocket_isolated_tab` via `_insert_websocket_tab`): same insert/focus/save-state
  sequence, for a `WebSocketTab`.
- **Open a new MCP Client connection tab** (`add_blank_mcp_client_tab` /
  `open_mcp_client_isolated_tab` via `_insert_mcp_client_tab`): same insert/focus/save-state
  sequence, for an `McpClientTab`.
- In every scenario above, the observable outcome (tab position, focus, persisted state) must be
  identical before and after this refactor — only the internal implementation path changes.

## Q&A

- **Q: Is the duplication described in the ticket actually present, and where?**
  A: Yes, verified directly in `pypost/ui/presenters/tabs_presenter.py` (current HEAD, 1,064
  lines total):
  - `add_new_tab`, lines 210-217 (name computed at line 210; plus-insert/append/focus at
    211-217).
  - `_insert_mcp_client_tab`, lines 304-311 (name at 304; plus-insert/append/focus at 305-311),
    plus the `save_tabs_state` call at 312-313.
  - `_insert_websocket_tab`, lines 336-343 (name at 336; plus-insert/append/focus at 337-343),
    plus the `save_tabs_state` call at 345-346.
  All three share the identical `plus_idx = self._header.insert_index_before_plus()` /
  `if plus_idx >= 0: insertTab ... else: addTab ... ensure_plus_tab()` /
  `self._tabs.setCurrentWidget(tab)` / `if save_state: self.save_tabs_state()` shape.

- **Q: What is the file's actual current LOC vs. the ticket's stated 771/785?**
  A: The ticket summary/description cites 771/785 from the PYPOST-1166 tech-debt snapshot. As of
  this step (2026-09-03), the file is **1,064 lines** — 279 lines past the 785 cap, not merely
  approaching it. This step documents the discrepancy as a requirement-gathering finding; it
  does not attempt to explain the intervening growth (out of scope for Step 1) or resize the cap
  (not this task's decision to make).

- **Q: Does `ai-tasks/PYPOST-1166/60-tech-debt.md` exist and match the ticket's description?**
  A: Yes. It documents the same "Triplicated insert-before-plus" item under "Code Quality
  Issues" and lists this ticket (PYPOST-1184) as its non-blocker follow-up (item 6 under
  "Follow-up Tasks"), confirming this task's origin and scope.

- **Q: Is any new business capability being added?**
  A: No. This is a pure internal refactor / tech-debt task. The "business" driver is
  maintainability of a file other in-flight and future stories (MCP-TM series) depend on
  editing.
