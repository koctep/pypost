# PYPOST-1184: Extract insert-before-plus helper so TabsPresenter stays under 785 LOC

## Research

- **Current duplication** (verified against `pypost/ui/presenters/tabs_presenter.py`, HEAD,
  1,064 lines):
  - `add_new_tab`, lines 210-220 — name computed at 210; insert-before-plus/append/focus at
    211-217; conditional `save_tabs_state()` at 219-220. Returns `None`.
  - `_insert_mcp_client_tab`, lines 304-314 — name at 304; insert/append/focus at 305-311;
    unconditional-looking but flag-gated `save_tabs_state()` at 312-313; returns `tab`.
  - `_insert_websocket_tab`, lines 336-347 — name at 336; insert/append/focus at 337-343;
    `save_tabs_state()` at 345-346; returns `tab`.
  - All three share the identical shape:
    ```python
    plus_idx = self._header.insert_index_before_plus()
    if plus_idx >= 0:
        self._tabs.insertTab(plus_idx, tab, name)
    else:
        self._tabs.addTab(tab, name)
        self._header.ensure_plus_tab()
    self._tabs.setCurrentWidget(tab)
    if save_state:
        self.save_tabs_state()
    ```
    (`_insert_mcp_client_tab` omits the blank line before `if save_state`; otherwise byte-for-byte
    identical modulo the tab/name variables.)

- **Existing sibling-module extraction pattern already established in this package.** The
  presenter already delegates several concerns to free functions in sibling modules under
  `pypost/ui/presenters/`, all following the same shape: a free function whose *first* positional
  parameter is `presenter: TabsPresenter`, imported only under `TYPE_CHECKING` to avoid a circular
  import, and the function reaches into the presenter's private attributes directly
  (`presenter._header`, `presenter._tabs`, `presenter._request_manager`, ...). Examples read
  directly from source:
  - `tabs_presenter_close.py::close_workspace_tab(presenter, index, *, prompt_close=None)` —
    extracted per PYPOST-1159; uses `presenter._header`, `presenter._tabs`,
    `presenter._request_manager`.
  - `tabs_presenter_request_close.py::close_tabs_for_request_ids(...)`,
    `tabs_presenter_ws_close.py::close_tabs_for_websocket_ids/rename_websocket_tabs(...)`,
    `tabs_presenter_mcp_close.py::close_tabs_for_mcp_client_ids/rename_mcp_client_tabs(...)` —
    same shape, one sibling module per concern.
  - `tabs_presenter_draft.py` holds pure helper functions that do *not* need the presenter
    (`make_websocket_saved_predicate`, `make_mcp_client_saved_predicate`, etc.) — these take only
    the specific collaborators they need (e.g. `request_manager: RequestManager`), not the whole
    presenter, because they don't touch presenter-private widget state.
  - `TabsPresenter.__init__` already wires several of these in (`close_workspace_tab`,
    `close_tabs_for_request_ids_helper`, `rename_websocket_tabs_ws`, ...), so callers importing a
    new sibling-module function alongside them is a well-worn path, not a new idiom.

  This is decisive: the codebase already answered "private method vs. free function vs. new
  module" for extractions from `TabsPresenter` that need `self._header` / `self._tabs`, and chose
  **free function in a new/existing sibling module, taking the presenter as its first argument**.
  Deviating from that (e.g. a private method) would introduce a second, inconsistent extraction
  style in the same file for no behavioral benefit.

- **`tab_header.py`** (`pypost/ui/widgets/tab_header.py`) is the sole owner of
  `insert_index_before_plus()` (line 74) and `ensure_plus_tab()` (line 40); both are only called
  from the three sites above (confirmed via repo-wide grep) — no other caller depends on the
  duplicated sequence, so the extraction has no external ripple effect beyond the three call
  sites and `TabsPresenter`'s import block.

## Implementation Plan

1. Add a new sibling module `pypost/ui/presenters/tabs_presenter_insert.py` (naming matches the
   existing `tabs_presenter_<concern>.py` convention: `_close`, `_request_close`, `_ws_close`,
   `_mcp_close`, `_draft`, `_hotkeys`, `_worker`). A new module — rather than appending to
   `tabs_presenter_draft.py` — keeps one file per concern, matching the existing pattern where
   close-family logic already got its own three modules split by tab kind rather than being
   folded into `_draft.py`.
2. In that module, define one free function:

   ```python
   from __future__ import annotations

   from typing import TYPE_CHECKING

   from PySide6.QtWidgets import QWidget

   if TYPE_CHECKING:
       from pypost.ui.presenters.tabs_presenter import TabsPresenter

   def insert_tab_before_plus(
       presenter: TabsPresenter,
       tab: QWidget,
       name: str,
       *,
       save_state: bool = True,
   ) -> None:
       """Insert *tab* immediately before the plus tab (or append and re-ensure the
       plus tab), focus it, then optionally persist tab state.

       Mirrors the sequence previously duplicated in ``add_new_tab``,
       ``_insert_mcp_client_tab``, and ``_insert_websocket_tab``: ask the header for
       the index before the plus marker; insert there if found, otherwise append and
       ask the header to (re-)ensure a plus tab exists; focus the new tab; call
       ``save_tabs_state()`` only when the caller asked for it.
       """
       plus_idx = presenter._header.insert_index_before_plus()
       if plus_idx >= 0:
           presenter._tabs.insertTab(plus_idx, tab, name)
       else:
           presenter._tabs.addTab(tab, name)
           presenter._header.ensure_plus_tab()
       presenter._tabs.setCurrentWidget(tab)
       if save_state:
           presenter.save_tabs_state()
   ```

   Design notes on the signature:
   - `tab: QWidget` and `name: str` are the two axes the three call sites already differ on
     (widget type / display-name expression); everything else (`plus_idx` lookup, insert-vs-append
     branch, focus, conditional save) is identical and moves into the helper unchanged.
   - The helper does **not** return anything and does **not** decide what the caller returns —
     `add_new_tab` returns `None` today, `_insert_mcp_client_tab`/`_insert_websocket_tab` return
     the `tab` they were given. Each call site keeps its own `return tab` (or lack thereof) after
     calling the helper, so the return-value asymmetry noted in the requirements stays exactly as
     it is — the helper is not the place that papers over it.
   - `save_state: bool = True` keeps the same default and same "caller decides" contract as today;
     no call site's effective default changes.
   - Takes `presenter: TabsPresenter` (not `header`/`tabs`/`save_tabs_state` as three separate
     params) to match the established sibling-module idiom above, and because a 3-callback
     signature would be strictly more ceremony at each call site for no gain — all three current
     and any future call sites are always full `TabsPresenter` methods, never called from outside
     the class.

3. Refactor the three call sites to call the helper, replacing the duplicated block with one line
   each:

   - `add_new_tab` (lines ~199-220): after computing `name` at line 210, replace lines 211-220
     with:
     ```python
     insert_tab_before_plus(self, tab, name, save_state=save_state)
     ```
     (`add_new_tab` keeps its existing `-> None` signature and implicit `return`.)
   - `_insert_mcp_client_tab` (lines ~289-314): after computing `name` at line 304, replace lines
     305-313 with:
     ```python
     insert_tab_before_plus(self, tab, name, save_state=save_state)
     ```
     followed by the existing `return tab` (unchanged).
   - `_insert_websocket_tab` (lines ~316-347): after computing `name` at line 336, replace lines
     337-346 with:
     ```python
     insert_tab_before_plus(self, tab, name, save_state=save_state)
     ```
     followed by the existing `return tab` (unchanged).
   - Add one import to `tabs_presenter.py`'s existing sibling-module import block (alongside
     `close_workspace_tab`, `close_tabs_for_request_ids_helper`, etc.):
     ```python
     from pypost.ui.presenters.tabs_presenter_insert import insert_tab_before_plus
     ```

4. Net effect on `tabs_presenter.py` LOC: each call site shrinks from a 7-10 line block to 1 line
   (plus the unchanged `name = ...` line and, for the two that had one, the unchanged `return
   tab`), for roughly 20-24 lines removed from `tabs_presenter.py`, offset by 1 new import line —
   a measurable step back toward the 785-line cap (currently 1,064; this alone does not close the
   279-line gap, and is not required to by this task's Definition of Done, which asks only for a
   "measurable reduction").

## Preserving Existing Behavior

Every observable behavior called out in the requirements' Definition of Done and User Scenarios
is preserved because the helper's body is a verbatim (variable-renamed) copy of the three
duplicated blocks, with no logic change:

- **Insertion position**: `presenter._header.insert_index_before_plus()` is still called first,
  and the same `>= 0` branch decides `insertTab` (before plus) vs. `addTab` + `ensure_plus_tab()`
  (append and re-ensure) — identical to today for all three tab kinds.
- **Titles**: unchanged — each call site still computes its own `name` expression
  (`request_data.name or "New Request"`, `connection.name or "New MCP Client"`, `connection.name
  or "WebSocket"`) *before* calling the helper; the helper only ever receives the already-computed
  string and never recomputes or defaults it itself.
- **Ordering**: unchanged — same `_header`/`_tabs` calls in the same order.
- **Focus**: unchanged — `presenter._tabs.setCurrentWidget(tab)` still runs unconditionally after
  insertion, for all three call sites.
- **Conditional `save_tabs_state()` timing**: unchanged — the helper still calls
  `presenter.save_tabs_state()` if and only if `save_state` is true, and still does so *after*
  `setCurrentWidget`, matching all three current call sites (including
  `_insert_mcp_client_tab`, which today has no blank line before the check — a purely cosmetic
  difference that carries no behavioral meaning).
- **Return values**: unchanged — `add_new_tab` keeps returning `None`; `_insert_mcp_client_tab`
  and `_insert_websocket_tab` keep returning `tab`, because the helper never returns anything and
  each call site keeps its own trailing `return`.
- **Call-site-specific work that must stay outside the helper and is untouched by this
  extraction**: `add_new_tab`'s legacy-MCP redirect and `copy_request_for_isolated_tab` /
  `snapshot_persisted_fields` calls (lines 200-208); `_insert_mcp_client_tab`'s
  `McpClientPresenter`/`McpClientTab` construction, persisted-baseline snapshot, and
  `_wire_mcp_client_tab_signals` (lines 295-303); `_insert_websocket_tab`'s
  `WebSocketPresenter`/`WebSocketTab` construction, persisted-baseline snapshot,
  `tab_title_changed` connection, and `_wire_websocket_tab_signals` (lines 322-334). None of this
  moves — only the shared tail (insert-before-plus through conditional save) is extracted.

**Mandatory — Failing Repro (next Step 3):** This is a pure internal refactor with no intended
behavioral change (confirmed in Requirements §Constraints and Assumptions: "no user-visible
behavior may change"). Per the Top-Down workflow, Step 3 does not need a *new* red test asserting
new behavior. Instead, Step 3 should:

- Confirm `tests/test_tabs_presenter.py` (and any WebSocket/MCP-client tab tests) already cover,
  or extend it to cover, the three preserved behaviors per tab kind: (a) insertion immediately
  before an existing plus tab, (b) append + plus-tab re-ensure when no plus tab is found, (c)
  focus (`currentWidget()`) lands on the new tab, (d) `save_tabs_state()` is called iff
  `save_state=True` (spy/mock the call), for HTTP (`add_new_tab`), WebSocket
  (`_insert_websocket_tab` via `add_blank_websocket_tab`/`open_websocket_isolated_tab`), and MCP
  Client (`_insert_mcp_client_tab` via `add_blank_mcp_client_tab`/`open_mcp_client_isolated_tab`).
- If any of those four behaviors, for any of the three tab kinds, is not already asserted by an
  existing test, Step 3 adds the missing assertion(s) to the relevant existing test file(s) as
  the "repro" — it must pass against current (pre-refactor) code (green, not red, since no
  behavior is changing) and would only turn red if a future edit to the new helper broke one of
  the four behaviors. This satisfies the workflow's Step 3 intent (a regression guard exists
  before Step 4 touches production code) without inventing a red test for behavior that isn't
  changing.
- State explicitly in Step 3's artifact which of the four behaviors, per tab kind, were already
  covered vs. newly added.

## Architecture

- **New module**: `pypost/ui/presenters/tabs_presenter_insert.py` — one free function,
  `insert_tab_before_plus(presenter, tab, name, *, save_state=True) -> None`, following the
  established `presenter: TabsPresenter` sibling-module extraction pattern already used by
  `tabs_presenter_close.py`, `tabs_presenter_request_close.py`, `tabs_presenter_ws_close.py`, and
  `tabs_presenter_mcp_close.py`.
- **Modified module**: `pypost/ui/presenters/tabs_presenter.py` — add one import; replace the
  duplicated tail of `add_new_tab`, `_insert_mcp_client_tab`, and `_insert_websocket_tab` with a
  single call to `insert_tab_before_plus(self, tab, name, save_state=save_state)` each, keeping
  each method's existing tab-kind-specific setup and return statement untouched.
- **No changes** to `pypost/ui/widgets/tab_header.py` (`insert_index_before_plus`,
  `ensure_plus_tab`) or to any of the six existing sibling modules — this task adds a seventh
  sibling module rather than editing an existing one, since none of the existing modules own
  "insert a tab into the strip" as a concern (they own close/rename/draft-predicate concerns).
- **Dependency direction unchanged**: `tabs_presenter_insert.py` depends on `TabsPresenter` only
  under `TYPE_CHECKING` (for the type hint) — same as the existing close-family modules — so there
  is no runtime circular import between it and `tabs_presenter.py`.
- **Rejected alternative — private method on `TabsPresenter`**: would remove the duplicated
  *lines* but keep them counted against `tabs_presenter.py`'s LOC (only ~3-4 lines saved per call
  site instead of ~7-9, since the method body itself still lives in the file), and would be
  inconsistent with every other multi-call-site extraction already done in this file (all of
  which are sibling-module free functions). Rejected because it under-delivers on the LOC goal and
  breaks the established pattern for no offsetting benefit.
- **Rejected alternative — expand `tabs_presenter_draft.py` instead of a new module**:
  `tabs_presenter_draft.py`'s existing functions are either presenter-free predicates/helpers
  (`make_*_saved_predicate`, `*_id_is_saved`) or draft-dirty-close confirmation helpers
  (`confirm_close_*_draft`) — a distinct concern (closing) from tab *insertion*. Rejected to avoid
  conflating two concerns in one file, consistent with how close-logic itself was split across
  three separate `_close`/`_request_close`/`_ws_close`/`_mcp_close` modules rather than merged.

## Q&A

- **Q: Why a free function taking `presenter` rather than a `@staticmethod`/classmethod on
  `TabsPresenter`, or a method on `RequestTabHeader`?**
  A: A static/class method on `TabsPresenter` is still counted in `tabs_presenter.py`'s LOC and
  breaks the established sibling-module pattern (see Rejected Alternatives). A method on
  `RequestTabHeader` (`tab_header.py`) was considered but rejected because the sequence also
  touches `presenter._tabs` (the `QTabWidget`, owned by `TabsPresenter`, not the header) and
  `presenter.save_tabs_state()` (a `TabsPresenter` method) — the header does not have access to
  either without being handed the presenter or the tab widget anyway, so moving the function to
  the header module would not reduce coupling, only relocate it to a module whose stated
  responsibility (per its own file) is the plus-tab marker itself, not general tab-strip
  insertion.

- **Q: Does the helper need to know about the three different widget types
  (`RequestTab`/`WebSocketTab`/`McpClientTab`)?**
  A: No — it operates on `tab: QWidget`, the common base all three tab widgets satisfy for the
  operations it performs (`insertTab`/`addTab`/`setCurrentWidget` all accept `QWidget`). The
  helper has no need to `isinstance`-branch on tab kind, which is exactly why it can be shared
  across all three call sites unmodified.

- **Q: Should `save_tabs_state` itself move into the new module?**
  A: No — out of scope. `save_tabs_state()` is called from other places in `TabsPresenter` beyond
  these three insertion sites (confirmed by requirements' Main Entities section describing it as
  a general persistence hook), so moving it would be a larger, unrelated extraction. The helper
  only *calls* `presenter.save_tabs_state()` conditionally, exactly as the three original blocks
  did.
